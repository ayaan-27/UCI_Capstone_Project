"""Audit the uploaded free-text RETRO and compare candidate prediction models.

No external NLP service or numerical sentiment labels are used. Text is input
only in week-labelled retrospective scenarios, never claimed as verified timing.
python -m posterior_study.retro_followup --retro-csv data/retro_uploaded.csv
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from .analysis import ROOT, TERMS, CONTEXTS, GROUPS, PosteriorRegression, SEED
from .cohort_policy import exclude_summer_rows

COURSES={76548:'2025 FAL',80120:'2026 WTR',82172:'2026 SPR'}
PROMPTS={
    "What didn't go well?":'not_well',
    'What went well?':'went_well',
    'What can be improved?':'improve',
}
RETRO_TERMS=['2025 FAL','2026 WTR','2026 SPR']
BASE_NON=[v for g in GROUPS.values() for v in g]


def load_retro(path,frame,max_week=4):
    """Validate keys and aggregate ONLY week-labelled observations <= max_week.

    Returns one row for every base student, preserving nonrespondents. Distinct
    questions remain separate text channels. All blank responses stay absent.
    Unknown course/question/week labels, duplicate responses or mismatched IDs
    stop analysis rather than being silently pooled or dropped.
    """
    frame,_=exclude_summer_rows(frame)
    r=pd.read_csv(path)
    required=['lms_course_id','student_name','user_id','lms_user_id','week','retrospective_q','response']
    if not set(required).issubset(r):raise ValueError('Missing RETRO schema columns')
    if not r.student_name.eq(r.user_id).all() or not r.student_name.eq(r.lms_user_id).all():
        raise ValueError('Anonymized student ID columns disagree')
    r['student_id']=r.student_name.str.strip()
    if not r.student_id.str.fullmatch(r'MLCStudent\d+').all():raise ValueError('Unexpected student ID')
    r['cohort']=r.lms_course_id.map(COURSES)
    r,summer_audit=exclude_summer_rows(r)
    if r.cohort.isna().any():raise ValueError('Unmapped course')
    nums=r.week.str.extract(r'^Week (\d+)$',expand=False)
    if nums.isna().any():raise ValueError('Unrecognized week labels')
    r['week_num']=nums.astype(int)
    if not set(r.week_num).issubset({2,4,6,8,10}):raise ValueError('Unexpected weeks')
    def question(q):
        found=[name for prefix,name in PROMPTS.items() if q.startswith(prefix)]
        if len(found)!=1:raise ValueError('Unrecognized question')
        return found[0]
    r['question']=r.retrospective_q.map(question)
    keys=['cohort','student_id','week_num','question']
    if r.duplicated(keys).any():raise ValueError('Duplicate student-week-question response')
    check=r.merge(frame[['cohort','student_id']],on=['cohort','student_id'],how='left',indicator=True,validate='many_to_one')
    if not check._merge.eq('both').all():raise ValueError('RETRO IDs do not match the grade table')
    r['text']=r.response.fillna('').astype(str).str.replace(r'\s+',' ',regex=True).str.strip()
    availability=r.groupby(['cohort','week_num']).agg(students=('student_id','nunique'),
        rows=('question','size'),nonblank=('text',lambda s:s.ne('').sum())).reset_index()
    early=r[r.week_num.le(max_week)&r.text.ne('')].copy()
    early=early.sort_values(['cohort','student_id','week_num','question'])
    texts=early.groupby(['cohort','student_id','question']).text.agg(' '.join).unstack('question').fillna('')
    texts=texts.reindex(columns=list(PROMPTS.values()),fill_value='').rename(columns=lambda c:'text_'+c)
    features=frame.merge(texts.reset_index(),how='left',on=['cohort','student_id'],validate='one_to_one')
    for col in ['text_'+c for c in PROMPTS.values()]:features[col]=features[col].fillna('')
    counts=early.groupby(['cohort','student_id']).agg(retro_n_answers=('text','size'),retro_n_weeks=('week_num','nunique'))
    features=features.merge(counts.reset_index(),how='left',on=['cohort','student_id'],validate='one_to_one')
    features[['retro_n_answers','retro_n_weeks']]=features[['retro_n_answers','retro_n_weeks']].fillna(0)
    features['retro_instrument_available']=features.cohort.isin(RETRO_TERMS)
    features['retro_responded']=(features.retro_n_answers>0).astype(int)
    text=features[['text_'+c for c in PROMPTS.values()]].agg(' '.join,axis=1)
    features['retro_log_words']=np.log1p(text.str.findall(r'\b\w+\b').str.len())
    r.attrs['summer_exclusion']=summer_audit
    return features,availability,r


class SafeTFIDF(TfidfVectorizer):
    """Handle a fold with no train vocabulary without learning from test texts."""
    def fit_transform(self,raw_documents,y=None):
        self.empty_=False
        try:return super().fit_transform(raw_documents)
        except ValueError as e:
            if 'empty vocabulary' not in str(e) and 'After pruning' not in str(e):raise
            self.empty_=True
            return sparse.csr_matrix((len(raw_documents),1))
    def transform(self,raw_documents):
        if self.empty_:return sparse.csr_matrix((len(raw_documents),1))
        return super().transform(raw_documents)


def numeric_model(name):
    if name=='Bayesian CPD':return PosteriorRegression()
    if name=='Ridge':est=Ridge(alpha=10.)
    elif name=='Huber':est=HuberRegressor(epsilon=1.35,alpha=1.,max_iter=3000,tol=1e-7)
    elif name=='ExtraTrees':est=ExtraTreesRegressor(n_estimators=200,max_depth=4,min_samples_leaf=5,random_state=SEED,n_jobs=2)
    elif name=='HistGB':est=HistGradientBoostingRegressor(max_iter=150,max_leaf_nodes=7,min_samples_leaf=10,l2_regularization=10.,learning_rate=.05,random_state=SEED)
    else:raise ValueError(name)
    # Outcome scaling makes Huber's regularization comparable across contexts.
    return TransformedTargetRegressor(regressor=make_pipeline(SimpleImputer(strategy='median',keep_empty_features=True),StandardScaler(),est),transformer=StandardScaler())


def score(y,mu):
    mu=np.clip(mu,0,100);y=np.asarray(y)
    return dict(n=len(y),MAE=float(np.mean(abs(y-mu))),RMSE=float(np.sqrt(np.mean((y-mu)**2))),
        n_below70=int(sum(y<70)),MAE_below70=float(np.mean(abs(y[y<70]-mu[y<70]))) if np.any(y<70) else np.nan,
        worst_abs_error=float(np.max(abs(y-mu))))


def benchmark(frame,out):
    frame,_=exclude_summer_rows(frame)
    rows=[];preds=[]
    for fold in range(2,6):
        tr=frame[frame.cohort.isin(TERMS[:fold])];va=frame[frame.cohort.eq(TERMS[fold])]
        for context,grades in CONTEXTS.items():
            for group in ['Baseline','All sources']:
                cols=grades+(BASE_NON if group=='All sources' else [])
                # sklearn needs at least one input column for the intercept-only context.
                xtr=tr[cols] if cols else pd.DataFrame({'constant':np.ones(len(tr))},index=tr.index)
                xva=va[cols] if cols else pd.DataFrame({'constant':np.ones(len(va))},index=va.index)
                for name in ['Bayesian CPD','Ridge','Huber','ExtraTrees','HistGB']:
                    model=numeric_model(name)
                    with warnings.catch_warnings(record=True) as ws:
                        warnings.simplefilter('always',ConvergenceWarning)
                        model.fit(xtr,tr.percentage)
                        if any(issubclass(w.category,ConvergenceWarning) for w in ws):raise RuntimeError(f'{name} did not converge')
                    mu=model.predictive(xva)[0] if name=='Bayesian CPD' else model.predict(xva)
                    rows.append(dict(term=TERMS[fold],context=context,group=group,model=name,**score(va.percentage,mu)))
                    for i,(_,r) in enumerate(va.iterrows()):
                        preds.append(dict(term=TERMS[fold],student_id=r.student_id,context=context,group=group,model=name,actual=r.percentage,prediction=float(np.clip(mu[i],0,100))))
    met=pd.DataFrame(rows);pp=pd.DataFrame(preds)
    met.to_csv(out/'model_benchmark_by_term.csv',index=False);pp.to_csv(out/'model_benchmark_predictions.csv',index=False)
    macro=met.groupby(['context','group','model'])[['MAE','RMSE','MAE_below70','worst_abs_error']].mean().reset_index()
    macro.to_csv(out/'model_benchmark_macro.csv',index=False)
    return macro


COUNT_COLS=['retro_responded','retro_n_answers','retro_n_weeks','retro_log_words']
TEXT_COLS=['text_'+v for v in PROMPTS.values()]


def text_model(cols,encoding,alpha):
    numeric=cols+(COUNT_COLS if encoding!='None' else [])
    blocks=[]
    if numeric:
        blocks.append(('numeric',make_pipeline(SimpleImputer(strategy='median',keep_empty_features=True),StandardScaler()),numeric))
    if encoding=='TFIDF+response':
        for name in PROMPTS.values():
            blocks.append((name,SafeTFIDF(ngram_range=(1,2),min_df=2,max_features=200,stop_words=sorted(ENGLISH_STOP_WORDS-{'not','no','nor','never'}),sublinear_tf=True),'text_'+name))
    if not blocks:
        # A constant input produces the earlier-student mean with Ridge intercept.
        blocks=[('constant','passthrough',['constant'])]
    pipeline=make_pipeline(ColumnTransformer(blocks,sparse_threshold=1.),Ridge(alpha=alpha,solver='lsqr',tol=1e-8,max_iter=10000))
    return TransformedTargetRegressor(regressor=pipeline,transformer=StandardScaler())


def retro_comparisons(features,out):
    features,_=exclude_summer_rows(features)
    rows=[];preds=[]
    # Only terms where this questionnaire exists. Earlier terms are not fake
    # nonrespondents. Two possible later-term checks, with 20 then 60 train rows.
    for fold in [1,2]:
        tr=features[features.cohort.isin(RETRO_TERMS[:fold])].copy()
        va=features[features.cohort.eq(RETRO_TERMS[fold])].copy()
        tr['constant']=1.;va['constant']=1.
        for context,grades in CONTEXTS.items():
            for base in ['Baseline','All early sources']:
                cols=grades+(BASE_NON if base=='All early sources' else [])
                for alpha in [1.,10.,100.]:
                    for encoding in ['None','Response pattern','TFIDF+response']:
                        m=text_model(cols,encoding,alpha);m.fit(tr,tr.percentage)
                        mu=m.predict(va)
                        rows.append(dict(term=RETRO_TERMS[fold],n_train=len(tr),context=context,base=base,alpha=alpha,retro=encoding,**score(va.percentage,mu)))
                        for i,(_,r) in enumerate(va.iterrows()):
                            preds.append(dict(term=RETRO_TERMS[fold],student_id=r.student_id,context=context,base=base,alpha=alpha,retro=encoding,
                                responded=int(r.retro_responded),actual=r.percentage,prediction=float(np.clip(mu[i],0,100))))
    met=pd.DataFrame(rows);pp=pd.DataFrame(preds)
    met.to_csv(out/'retro_metrics_by_term.csv',index=False);pp.to_csv(out/'retro_predictions.csv',index=False)
    macro=met.groupby(['context','base','alpha','retro'])[['MAE','RMSE','MAE_below70']].mean().reset_index()
    macro.to_csv(out/'retro_macro_metrics.csv',index=False)
    changes=[]
    for (ct,base,alpha),d in pp.groupby(['context','base','alpha']):
        ref=d[d.retro.eq('None')].set_index(['term','student_id'])
        pattern=d[d.retro.eq('Response pattern')].set_index(['term','student_id']).reindex(ref.index)
        text=d[d.retro.eq('TFIDF+response')].set_index(['term','student_id']).reindex(ref.index)
        assert np.allclose(text.actual,ref.actual)
        for term in RETRO_TERMS[1:]:
            for scope,ids in [('All students',ref.loc[term].index),('RETRO responders',ref.loc[term].query('responded == 1').index)]:
                a=ref.loc[term].loc[ids];b=pattern.loc[term].loc[ids];c=text.loc[term].loc[ids]
                changes.append(dict(context=ct,base=base,alpha=alpha,term=term,scope=scope,n=len(a),
                    baseline_MAE=float(abs(a.actual-a.prediction).mean()),
                    response_MAE_gain=float((abs(a.actual-a.prediction)-abs(b.actual-b.prediction)).mean()),
                    text_total_MAE_gain=float((abs(a.actual-a.prediction)-abs(c.actual-c.prediction)).mean()),
                    text_over_response_gain=float((abs(b.actual-b.prediction)-abs(c.actual-c.prediction)).mean()),
                    mean_abs_prediction_shift=float(abs(a.prediction-c.prediction).mean())))
    delta=pd.DataFrame(changes);delta.to_csv(out/'retro_paired_gains.csv',index=False)
    return macro,delta


def main(path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    frame,base_summer_audit=exclude_summer_rows(pd.read_csv(ROOT/'mlc_results/expanded_student_features.csv'))
    features,audit,r=load_retro(path,frame)
    audit.to_csv(out/'retro_availability_by_week.csv',index=False)
    features.groupby('cohort').agg(n=('student_id','size'),early_retro_respondents=('retro_responded','sum')).to_csv(out/'retro_early_coverage.csv')
    # Save aggregates only; raw reflection text is kept in the ignored local data/
    # input, not copied into figures or result CSVs.
    features[['student_id','cohort','retro_instrument_available']+COUNT_COLS].to_csv(out/'retro_response_features.csv',index=False)
    print('Running numeric candidate models',flush=True)
    bm=benchmark(frame,out)
    print('Running early RETRO text comparisons',flush=True)
    macro,delta=retro_comparisons(features,out)
    meta=dict(base_summer_exclusion=base_summer_audit,retro_summer_exclusion=r.attrs['summer_exclusion'],retro_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),rows=len(r),unique_respondents=int(r.student_id.nunique()),
        matched_rows=len(r),early_respondents=int(features.retro_responded.sum()),week_limit=4,
        timestamps_available=False,retro_terms=RETRO_TERMS,retro_evaluation_terms=RETRO_TERMS[1:],
        retrofit='week labels only; 6/8/10 excluded; not verified early availability',
        numeric_benchmark='fixed candidate settings; 4 explored temporal terms; no winner independently confirmed',
        text_representation='three separate train-only TFIDF channels, <=200 features each, min document frequency 2, unigrams/bigrams; response counts included',
        alpha='1,10,100 sensitivity; no choice claimed as unbiased winner',
        counts='120 numeric fits; 108 text/comparator fits',seed=SEED)
    (out/'retro_provenance.json').write_text(json.dumps(meta,indent=2))
    print(bm[bm.context.eq('Block B')].to_string(index=False))
    print(delta[delta.alpha.eq(10)&delta.scope.eq('All students')].to_string(index=False))
    return meta


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--retro-csv',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=ROOT/'retro_followup_results')
    args=ap.parse_args();main(args.retro_csv,args.output)
