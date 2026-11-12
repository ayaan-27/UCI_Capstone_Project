"""RETRO timing/key integrity and train-only text feature validation."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from posterior_study.retro_followup import load_retro, text_model
from posterior_study.analysis import ROOT

class RetroTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'retro.csv'
        self.base=pd.DataFrame({'cohort':['2025 FAL','2025 FAL'],'student_id':['MLCStudent1','MLCStudent2']})
        self.raw=pd.DataFrame([dict(lms_course_id=76548,student_name='MLCStudent1',user_id='MLCStudent1',
            lms_user_id='MLCStudent1',week=f'Week {week}',retrospective_q='What went well? example',response=text)
            for week,text in [(2,'helpful feedback'),(4,'good teamwork'),(10,'laterfinalscoretoken')]])

    def test_late_text_cannot_enter_early_features_and_nonrespondents_preserved(self):
        self.raw.to_csv(self.path,index=False)
        f,_,_=load_retro(self.path,self.base)
        self.assertEqual(len(f),2)
        self.assertNotIn('laterfinalscoretoken',f.text_went_well.iloc[0])
        self.assertEqual(f.retro_n_answers.iloc[0],2)
        self.assertEqual(f.retro_responded.iloc[1],0)
        self.assertEqual(f.text_went_well.iloc[1],'')
        # Changing an excluded response must not change any early feature.
        self.raw.loc[self.raw.week.eq('Week 10'),'response']='entirely different later outcome'
        self.raw.to_csv(self.path,index=False)
        g,_,_=load_retro(self.path,self.base)
        pd.testing.assert_frame_equal(f,g)

    def test_duplicate_and_unmatched_rows_are_rejected(self):
        pd.concat([self.raw,self.raw.iloc[:1]]).to_csv(self.path,index=False)
        with self.assertRaisesRegex(ValueError,'Duplicate'):load_retro(self.path,self.base)
        raw=self.raw.copy()
        for c in ['student_name','user_id','lms_user_id']:raw[c]='MLCStudent999'
        raw.to_csv(self.path,index=False)
        with self.assertRaisesRegex(ValueError,'do not match'):load_retro(self.path,self.base)

    def test_text_vocabulary_never_fits_evaluation_words(self):
        train=pd.DataFrame({'text_not_well':['challenging tasks']*4,'text_went_well':['helpful feedback']*4,
            'text_improve':['practice writing']*4,'retro_responded':[1]*4,'retro_n_answers':[3]*4,
            'retro_n_weeks':[1]*4,'retro_log_words':[3]*4})
        model=text_model([],'TFIDF+response',10)
        model.fit(train,np.array([70.,75.,80.,85.]))
        test=train.copy();test['text_went_well']='futuretokenzz'
        model.predict(test)
        vocabulary=model.regressor_.named_steps['columntransformer'].named_transformers_['went_well'].vocabulary_
        self.assertNotIn('futuretokenzz',vocabulary)
        self.assertIn('feedback',vocabulary)

    def test_benchmark_reproduces_prior_bayesian_predictions(self):
        new=ROOT/'retro_followup_results/model_benchmark_predictions.csv'
        if not new.exists():self.skipTest('Run follow-up benchmark first')
        p=pd.read_csv(new);p=p[p.model.eq('Bayesian CPD') & p.group.eq('All sources')]
        old=pd.read_csv(ROOT/'posterior_results/temporal_predictions.csv')
        old=old[old.group.eq('LMS+EVC+Wellness')]
        merged=p.merge(old,on=['term','context','student_id'],validate='one_to_one',suffixes=('_new','_old'))
        self.assertEqual(len(merged),146*3)
        np.testing.assert_allclose(merged.prediction_new,merged.prediction_old,atol=1e-9)

if __name__=='__main__':unittest.main()
