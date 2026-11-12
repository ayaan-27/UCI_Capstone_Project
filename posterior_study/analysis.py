"""Conjugate posterior simulation, Gibbs validation, and temporal group ablations.

Run from repository root: python -m posterior_study.analysis
Only the exported processed table is required. No raw-data reproduction is claimed.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
import platform
from pathlib import Path
import importlib.metadata
import numpy as np
import pandas as pd
from scipy import linalg, special, stats
from .cohort_policy import exclude_summer_rows, require_non_summer_columns

ROOT = Path(__file__).resolve().parents[1]
TERMS = ['2024 FAL','2025 WTR','2025 SPR','2025 FAL','2026 WTR','2026 SPR']
GROUPS = {'LMS':['log_page_views','log_lms_participations'],
          'EVC':['cost_support','expectancy','value'], 'Wellness':['wellness']}
GRADES = ['nspe_pct','quiz1_comm_pct','quiz1_ethics_pct','ethics_pct','paper_a_pct',
          'writing_exercises_pct','early_peer_draft_pct','group_a_written_pct',
          'group_a_oral_pct','group_a_team_pct','quiz2_comm_pct','quiz2_ethics_pct',
          'paper_b_pct','paper_b_peer_pct','pitch_reflection_pct','pitch_completion_pct']
CONTEXTS = {'No grades':[], 'Block A':GRADES[:10], 'Block B':GRADES}
COMBOS = [c for k in range(4) for c in itertools.combinations(GROUPS,k)]
SEED = 271828
PRACTICAL_GAIN = .5  # illustrative final-percentage points; not professor-approved
RISK_THRESHOLD = 70.  # illustrative, not official letter-grade or intervention policy


def label(combo):
    return '+'.join(combo) if combo else 'Baseline'


@dataclass
class PosteriorRegression:
    """NIG outcome CPD, conditional on train-only median-imputed fixed design.

    beta | variance ~ N(0, variance * diag(.001, precision, ...)^{-1})
    variance ~ InvGamma(shape=2, scale=1), in standardized outcome units.
    All prediction-time missing values are filled with training medians. This is
    deliberately a common ablation design, NOT the original joint-DAG marginalizer.
    """
    precision: float = 10.
    indicators: bool = False

    def fit(self, frame, y):
        if not np.isfinite(y).all():
            raise ValueError('Outcome must be finite')
        if np.isinf(frame.to_numpy(dtype=float)).any():
            raise ValueError('Predictors must not contain infinity')
        require_non_summer_columns(frame.columns)
        self.original_columns = list(frame.columns)
        self.medians = frame.median().fillna(0.)
        x = self._fill(frame)
        self.columns = [c for c in x if x[c].nunique()>1]
        x = x[self.columns]
        self.center = x.mean().to_numpy()
        self.scale = x.std(ddof=0).to_numpy()
        self.y_center = float(np.mean(y))
        self.y_scale = max(float(np.std(y)), 1e-8)
        z = (x.to_numpy()-self.center)/self.scale
        self.design = np.column_stack([np.ones(len(x)),z])
        self.z_y = (np.asarray(y)-self.y_center)/self.y_scale
        p = self.design.shape[1]
        prior = np.diag([.001]+[self.precision]*(p-1))
        self.L = prior+self.design.T@self.design
        self.chol = np.linalg.cholesky(self.L)
        self.mean = linalg.cho_solve((self.chol,True),self.design.T@self.z_y)
        self.a = 2+len(x)/2
        # Stable equivalent to y'y - m'Lm.
        residual = self.z_y-self.design@self.mean
        self.b = float(1+.5*(residual@residual+self.mean@prior@self.mean))
        self.cov_unit = linalg.cho_solve((self.chol,True),np.eye(p))
        return self

    def _fill(self, x):
        x = x[self.original_columns]
        result = x.fillna(self.medians).copy()
        if self.indicators:
            for c in self.original_columns:
                result[c+'__missing'] = x[c].isna().astype(float)
        return result

    def matrix(self, x):
        z = (self._fill(x)[self.columns].to_numpy()-self.center)/self.scale
        return np.column_stack([np.ones(len(z)),z])

    def predictive(self, x):
        a = self.matrix(x)
        loc = (a@self.mean)*self.y_scale+self.y_center
        lev = np.einsum('ij,ji->i',a,linalg.cho_solve((self.chol,True),a.T))
        scale = np.sqrt((self.b/self.a)*(1+lev))*self.y_scale
        return loc, scale, 2*self.a

    def sample(self, rng, n=20000):
        variance = 1/rng.gamma(self.a,1/self.b,size=n)
        noise = linalg.solve_triangular(self.chol.T,rng.normal(size=(len(self.mean),n)),lower=False).T
        beta = self.mean+np.sqrt(variance)[:,None]*noise
        return beta,variance

    def coefficients(self, practical=1.):
        # Marginal t distribution, expressed as final percentage points per
        # one TRAINING standard deviation of each predictor, others held fixed.
        mu = self.mean[1:]*self.y_scale
        scale = np.sqrt(self.b/self.a*np.diag(self.cov_unit)[1:])*self.y_scale
        df = 2*self.a
        dist = stats.t(df,loc=mu,scale=scale)
        return pd.DataFrame({'feature':self.columns,'mean_points_per_SD':mu,
            'lower95':dist.ppf(.025),'upper95':dist.ppf(.975),
            'P_positive':dist.sf(0), 'P_abs_gt_1point':dist.cdf(-practical)+dist.sf(practical)})


def gibbs(model, seed=SEED, chains=4, warmup=1000, draws=4000):
    """Actual two-block MCMC, not renamed independent posterior draws.

    beta|s2,D ~ N(m,s2 L^-1)
    s2|beta,D ~ IG(a+p/2,b+(beta-m)'L(beta-m)/2).
    Exact independent NIG draws provide a reference for this educational check.
    """
    p=len(model.mean)
    out=np.empty((chains,draws,p+1))
    for c in range(chains):
        rng=np.random.default_rng(seed+c)
        v=(model.b/(model.a-1))*[.1,1,10,100][c%4]
        for i in range(warmup+draws):
            z=rng.normal(size=p)
            beta=model.mean+np.sqrt(v)*linalg.solve_triangular(model.chol.T,z,lower=False)
            # Quadratic form is v*z'z, so no repeated dense product is needed.
            v=1/rng.gamma(model.a+p/2,1/(model.b+.5*v*(z@z)))
            if i>=warmup:
                out[c,i-warmup,:p]=beta
                out[c,i-warmup,p]=v
    return out


def _split(x):
    h=x.shape[1]//2
    return np.concatenate([x[:,:h],x[:,-h:]],axis=0)


def _rhat(x):
    n=x.shape[1]
    w=np.var(x,axis=1,ddof=1).mean(axis=0)
    b=n*np.var(x.mean(axis=1),axis=0,ddof=1)
    return np.sqrt(((n-1)/n*w+b/n)/w)


def _ess(x):
    """Multi-chain FFT autocovariance with Geyer positive/monotone pair sums."""
    m,n,p=x.shape
    xc=x-x.mean(axis=1,keepdims=True)
    f=np.fft.rfft(xc,n=2*n,axis=1)
    ac=np.fft.irfft(f*f.conj(),n=2*n,axis=1)[:,:n].real/n
    w=np.var(x,axis=1,ddof=1).mean(axis=0)
    varplus=(n-1)/n*w+np.var(x.mean(axis=1),axis=0,ddof=1)
    rho=1-(w[None,:]-ac.mean(axis=0))/varplus[None,:]
    rho[0]=1
    ess=[]
    for j in range(p):
        sums=[]
        for t in range(0,n-1,2):
            pair=rho[t,j]+rho[t+1,j]
            if pair<0: break
            sums.append(pair if not sums else min(pair,sums[-1]))
        tau=max(1.,-1+2*np.sum(sums))
        ess.append(m*n/tau)
    return np.array(ess)


def diagnostics(draws,names):
    s=_split(draws)
    z=np.empty_like(s)
    folded=np.empty_like(s)
    for j in range(s.shape[2]):
        for source,target in [(s,z),(np.abs(s-np.median(s,axis=(0,1))),folded)]:
            ranks=stats.rankdata(source[:,:,j]).reshape(s.shape[:2])
            target[:,:,j]=special.ndtri((ranks-.375)/(ranks.size+.25))
    rhat=np.maximum(_rhat(z),_rhat(folded))
    bulk=_ess(z)
    tails=[]
    for q in [.05,.95]:
        tails.append(_ess((s<=np.quantile(s,q,axis=(0,1))).astype(float)))
    rawess=_ess(s)
    return pd.DataFrame({'parameter':names,'rank_split_Rhat':rhat,'bulk_ESS':bulk,
        'tail_ESS':np.minimum(*tails),'mean_MCSE':np.std(s,axis=(0,1),ddof=1)/np.sqrt(rawess)})


def metrics(y,loc,scale,df):
    y=np.asarray(y); pred=np.clip(loc,0,100)
    lo=loc+stats.t.ppf(.05,df)*scale
    hi=loc+stats.t.ppf(.95,df)*scale
    risk=stats.t.cdf((RISK_THRESHOLD-loc)/scale,df)
    return dict(n=len(y),MAE=float(np.mean(abs(y-pred))),RMSE=float(np.sqrt(np.mean((y-pred)**2))),
        NLPD=float(-np.mean(stats.t.logpdf((y-loc)/scale,df)-np.log(scale))),
        coverage90=float(np.mean((y>=lo)&(y<=hi))),width90=float(np.mean(hi-lo)),
        Brier70=float(np.mean((risk-(y<RISK_THRESHOLD))**2)),n_below70=int(sum(y<RISK_THRESHOLD)))


def temporal(frame,precision=10.,indicators=False,responders=False):
    frame,_=exclude_summer_rows(frame)
    rows=[];predictions=[]
    common=GROUPS['EVC']+GROUPS['Wellness']+GROUPS['LMS']
    for fold in range(2,6):
        tr=frame[frame.cohort.isin(TERMS[:fold])].copy()
        va=frame[frame.cohort.eq(TERMS[fold])].copy()
        if responders:
            tr=tr.dropna(subset=common);va=va.dropna(subset=common)
        assert set(tr.student_id).isdisjoint(va.student_id)
        for context,grades in CONTEXTS.items():
            for combo in COMBOS:
                columns=grades+[v for g in combo for v in GROUPS[g]]
                m=PosteriorRegression(precision,indicators).fit(tr[columns],tr.percentage)
                loc,scale,df=m.predictive(va[columns])
                rows.append(dict(context=context,group=label(combo),term=TERMS[fold],
                    n_train=len(tr),precision=precision,**metrics(va.percentage,loc,scale,df)))
                for j,(_,r) in enumerate(va.iterrows()):
                    predictions.append(dict(context=context,group=label(combo),term=TERMS[fold],
                        student_id=r.student_id,actual=r.percentage,prediction=float(np.clip(loc[j],0,100)),
                        loc=loc[j],scale=scale[j],df=df,
                        probability_below70=float(stats.t.cdf((70-loc[j])/scale[j],df)),
                        imputed_inputs=int(r[columns].isna().sum())))
    return pd.DataFrame(rows),pd.DataFrame(predictions)


def comparisons(preds,n=40000):
    """Bayesian bootstrap on four TERM mean paired gains, not beta posterior.

    Terms are weighted by Dirichlet(1,1,1,1). Conditional exploratory uncertainty;
    only four terms, with overlapping training sets. No future-term guarantee.
    """
    rng=np.random.default_rng(SEED)
    weights=rng.dirichlet(np.ones(4),size=n)
    results=[];terms=[]
    for context in CONTEXTS:
        p=preds[preds.context.eq(context)]
        for combo in COMBOS[1:]:
            for kind,base,extended in [('add_to_baseline','Baseline',label(combo))]:
                terms.append(_paired_terms(p,context,kind,base,extended))
        for g in GROUPS:
            reduced=label(tuple(k for k in GROUPS if k!=g))
            terms.append(_paired_terms(p,context,'add_last_'+g,reduced,label(tuple(GROUPS))))
    byterm=pd.concat(terms,ignore_index=True)
    for keys,d in byterm.groupby(['context','comparison','base','extended'],sort=False):
        d=d.set_index('term').loc[TERMS[2:]]
        gains=d.gain_MAE.to_numpy()
        samples=weights@gains
        results.append(dict(context=keys[0],comparison=keys[1],base=keys[2],extended=keys[3],
            macro_MAE_gain=float(gains.mean()),gain_lower95=float(np.quantile(samples,.025)),
            gain_upper95=float(np.quantile(samples,.975)),BB_P_gain_gt0=float(np.mean(samples>0)),
            BB_P_gain_gt_0_5=float(np.mean(samples>PRACTICAL_GAIN)),
            terms_improved=int(sum(gains>0)),macro_NLPD_gain=float(d.gain_NLPD.mean())))
    return byterm,pd.DataFrame(results)


def _paired_terms(p,context,kind,base,extended):
    a=p[p.group.eq(base)].set_index(['term','student_id'])
    b=p[p.group.eq(extended)].set_index(['term','student_id']).reindex(a.index)
    assert len(a)==len(b) and np.allclose(a.actual,b.actual)
    ga=abs(a.actual-a.prediction)-abs(b.actual-b.prediction)
    nla=-(stats.t.logpdf((a.actual-a['loc'])/a.scale,a.df)-np.log(a.scale))
    nlb=-(stats.t.logpdf((b.actual-b['loc'])/b.scale,b.df)-np.log(b.scale))
    d=pd.DataFrame({'gain_MAE':ga,'gain_NLPD':nla-nlb}).groupby('term').mean().reset_index()
    return d.assign(context=context,comparison=kind,base=base,extended=extended)


def run(output=None):
    out=Path(output or ROOT/'posterior_results');out.mkdir(parents=True,exist_ok=True)
    path=ROOT/'mlc_results/expanded_student_features.csv'
    frame,cohort_audit=exclude_summer_rows(pd.read_csv(path))
    (out/'summer_exclusion.json').write_text(json.dumps(cohort_audit,indent=2))
    assert len(frame)==191 and frame.student_id.nunique()==191
    assert set(frame.cohort)==set(TERMS)
    assert frame.percentage.between(0,100).all()
    aud=frame.groupby('cohort').agg(n=('student_id','size'),survey_present=('wellness','count'),lms_present=('log_page_views','count'))
    aud.to_csv(out/'data_availability.csv')
    ms,pred=temporal(frame)
    ms.to_csv(out/'temporal_metrics.csv',index=False);pred.to_csv(out/'temporal_predictions.csv',index=False)
    ts,cs=comparisons(pred)
    ts.to_csv(out/'paired_term_gains.csv',index=False);cs.to_csv(out/'paired_gain_summary.csv',index=False)
    shifts=[]
    for context in CONTEXTS:
        pp=pred[pred.context.eq(context)]
        base=pp[pp.group.eq('Baseline')].set_index(['term','student_id'])
        for combo in COMBOS[1:]:
            extended=pp[pp.group.eq(label(combo))].set_index(['term','student_id']).reindex(base.index)
            delta=extended.prediction-base.prediction
            for term in TERMS[2:]:
                v=delta.loc[term]
                shifts.append(dict(context=context,group=label(combo),term=term,
                    mean_abs_prediction_shift=float(abs(v).mean()),
                    max_abs_prediction_shift=float(abs(v).max()),fraction_shift_gt1=float((abs(v)>1).mean())))
    pd.DataFrame(shifts).to_csv(out/'prediction_shift_summary.csv',index=False)

    macro=ms.groupby(['context','group'])[['MAE','RMSE','NLPD','coverage90','width90','Brier70']].mean().reset_index()
    macro.to_csv(out/'macro_metrics.csv',index=False)
    sens=[]
    for name,prec,ind,resp in [('precision_1',1.,False,False),('precision_100',100.,False,False),
                               ('missingness_indicators',10.,True,False),('respondents_only',10.,False,True)]:
        met,pp=temporal(frame,prec,ind,resp)
        met.to_csv(out/(name+'_metrics.csv'),index=False)
        _,sc=comparisons(pp);sc.insert(0,'sensitivity',name);sens.append(sc)
    pd.concat(sens).to_csv(out/'sensitivity_gains.csv',index=False)
    # Final-fit coefficient interpretation: earlier five terms only; Spring 2026
    # is reused for diagnostics, not an untouched confirmation set.
    tr=frame[frame.cohort.ne(TERMS[-1])];va=frame[frame.cohort.eq(TERMS[-1])]
    columns=[v for g in GROUPS.values() for v in g]+GRADES
    model=PosteriorRegression().fit(tr[columns],tr.percentage)
    coeff=model.coefficients();coeff.to_csv(out/'coefficient_posteriors.csv',index=False)
    contextual=[]
    for context,grades in CONTEXTS.items():
        cols=[v for group in GROUPS.values() for v in group]+grades
        cm=PosteriorRegression().fit(tr[cols],tr.percentage)
        contextual.append(cm.coefficients().assign(context=context))
    pd.concat(contextual).to_csv(out/'coefficients_by_context.csv',index=False)
    rng=np.random.default_rng(SEED)
    beta,var=model.sample(rng)
    loc,scale,df=model.predictive(va[columns])
    a=model.matrix(va[columns]);draw_means=(beta@a.T)*model.y_scale+model.y_center
    draw_y=draw_means+rng.normal(size=draw_means.shape)*np.sqrt(var)[:,None]*model.y_scale
    probs=stats.t.cdf((70-loc)/scale,df)
    simulation_checks=dict(mean_abs_risk_MC_error=float(np.mean(abs((draw_y<70).mean(axis=0)-probs))),
        max_abs_risk_MC_error=float(np.max(abs((draw_y<70).mean(axis=0)-probs))),draws=len(beta))
    assert simulation_checks['max_abs_risk_MC_error']<.02
    va_out=va[['student_id','cohort','percentage']].copy()
    va_out['predictive_mean']=loc;va_out['lower90']=loc+stats.t.ppf(.05,df)*scale
    va_out['upper90']=loc+stats.t.ppf(.95,df)*scale
    va_out['P_final_below70']=probs;va_out['MC_P_final_below70']=(draw_y<70).mean(axis=0)
    va_out['n_imputed']=va[columns].isna().sum(axis=1)
    va_out.to_csv(out/'spring2026_probabilities.csv',index=False)
    # Conditional posterior predictive checks on TRAINING design; not validation.
    replicated=(beta@model.design.T)*model.y_scale+model.y_center
    replicated+=rng.normal(size=replicated.shape)*np.sqrt(var)[:,None]*model.y_scale
    ppc={}
    for name,observed,sims in [('sd',tr.percentage.std(ddof=0),replicated.std(axis=1)),
                              ('min',tr.percentage.min(),replicated.min(axis=1)),
                              ('n_below70',sum(tr.percentage<70),(replicated<70).sum(axis=1))]:
        ppc[name]=dict(observed=float(observed),replicated_lower95=float(np.quantile(sims,.025)),
            replicated_upper95=float(np.quantile(sims,.975)),posterior_predictive_tail=float(np.mean(sims>=observed)))
    ppc['unbounded_support']=dict(fraction_draws_outside_0_100=float(np.mean((replicated<0)|(replicated>100))))
    chain=gibbs(model)
    names=['intercept']+model.columns+['variance']
    diag=diagnostics(chain,names)
    means=chain.mean(axis=(0,1));exact=np.r_[model.mean,model.b/(model.a-1)]
    diag['MCMC_mean']=means;diag['exact_mean']=exact
    diag['mean_error_in_MCSE']=abs(means-exact)/diag.mean_MCSE
    diag.to_csv(out/'mcmc_diagnostics.csv',index=False)
    assert diag.rank_split_Rhat.max()<1.01
    assert diag.bulk_ESS.min()>1000 and diag.tail_ESS.min()>1000
    assert diag.mean_error_in_MCSE.max()<5
    mc_ci=np.quantile(chain[:,:,:-1], [.025,.975],axis=(0,1))
    analytic_scale=np.sqrt(model.b/model.a*np.diag(model.cov_unit))
    exact_ci=model.mean+stats.t.ppf(np.array([.025,.975])[:,None],2*model.a)*analytic_scale
    assert np.max(abs(mc_ci-exact_ci)/analytic_scale)<.15
    simulation_checks.update(max_Rhat=float(diag.rank_split_Rhat.max()),min_bulk_ESS=float(diag.bulk_ESS.min()),
        min_tail_ESS=float(diag.tail_ESS.min()),max_mean_error_in_MCSE=float(diag.mean_error_in_MCSE.max()),
        max_CI_error_in_posterior_scale=float(np.max(abs(mc_ci-exact_ci)/analytic_scale)))
    provenance=dict(seed=SEED,python=platform.python_version(),cohort_policy=cohort_audit,
        packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','matplotlib']},
        input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        input='existing processed table; original raw ZIP and MLC RETRO unavailable',
        outcome='percentage',precision=10,prior_IG_shape=2,prior_IG_scale=1,intercept_precision=.001,
        practical_MAE_gain=PRACTICAL_GAIN,illustrative_risk_threshold=RISK_THRESHOLD,
        validation='4 expanding-window terms, 146 predictions per model; historically explored data/settings',
        preprocessing='training-only median imputation and scaling; imputation uncertainty excluded',
        simulation_checks=simulation_checks,posterior_predictive_checks=ppc)
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2))
    plots(out,macro,cs,coeff,chain,model)
    print(macro[macro.group.isin(['Baseline','LMS+EVC+Wellness'])].to_string(index=False))
    print(cs[(cs.extended.eq('LMS+EVC+Wellness'))&(cs.comparison.eq('add_to_baseline'))].to_string(index=False))
    print(json.dumps(simulation_checks,indent=2))
    return provenance


def plots(out,macro,summary,coeff,chain,model):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    colors=['#2563EB','#0F766E','#9D4EDD']
    fig,ax=plt.subplots(figsize=(10,4.5))
    labels=[label(c) for c in COMBOS];x=np.arange(len(labels))
    for j,(ct,col) in enumerate(zip(CONTEXTS,colors)):
        values=macro[macro.context.eq(ct)].set_index('group').loc[labels].MAE
        ax.plot(x,values,'o-',label=ct,color=col)
    ax.set_xticks(x,labels,rotation=25,ha='right');ax.set_ylabel('Macro MAE (percentage points)');ax.legend()
    ax.set_title('Four later-term checks · identical students per model');fig.tight_layout();fig.savefig(out/'ablation_mae.png',dpi=180);plt.close(fig)
    s=summary[(summary.context.eq('Block B'))&summary.comparison.eq('add_to_baseline')].copy()
    fig,ax=plt.subplots(figsize=(9,4))
    y=np.arange(len(s));ax.errorbar(s.macro_MAE_gain,y,xerr=[s.macro_MAE_gain-s.gain_lower95,s.gain_upper95-s.macro_MAE_gain],fmt='o',color=colors[1],capsize=3)
    ax.set_yticks(y,s.extended);ax.axvline(0,color='#64748B',ls='--');ax.axvline(.5,color='#D97706',ls=':')
    ax.set_xlabel('MAE reduction vs grades only (positive = better)');ax.set_title('Block B · 95% term Bayesian-bootstrap intervals')
    fig.tight_layout();fig.savefig(out/'paired_gains.png',dpi=180);plt.close(fig)
    s=coeff[coeff.feature.isin([x for g in GROUPS.values() for x in g])]
    fig,ax=plt.subplots(figsize=(9,4))
    y=np.arange(len(s));ax.errorbar(s.mean_points_per_SD,y,xerr=[s.mean_points_per_SD-s.lower95,s.upper95-s.mean_points_per_SD],fmt='o',color=colors[2],capsize=3)
    ax.set_yticks(y,s.feature);ax.axvline(0,color='#64748B',ls='--');ax.axvspan(-1,1,color='#E2E8F0',alpha=.5)
    ax.set_xlabel('Final percentage points per 1 training SD · 95% credible interval');ax.set_title('Conditional associations with grades held fixed')
    fig.tight_layout();fig.savefig(out/'coefficient_posteriors.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(10,4.5))
    index=model.columns.index('expectancy')+1
    for c in range(chain.shape[0]):
        axes[0].plot(chain[c,:800,index],alpha=.65,lw=.6)
        axes[1].plot(chain[c,:800,-1],alpha=.65,lw=.6)
    axes[0].set_ylabel('Expectancy weight');axes[1].set_ylabel('Residual variance');axes[1].set_xlabel('First 800 retained Gibbs iterations per chain')
    fig.tight_layout();fig.savefig(out/'gibbs_trace.png',dpi=180);plt.close(fig)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path)
    args=ap.parse_args();run(args.output)
