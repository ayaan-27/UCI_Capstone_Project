"""Statistical checks with analytic references and a deliberately broken chain."""
import itertools
import json
import unittest
import numpy as np
import pandas as pd
from scipy import stats
from posterior_study.analysis import ROOT, GROUPS, GRADES, PosteriorRegression, diagnostics


class PosteriorTests(unittest.TestCase):
    def setUp(self):
        self.frame=pd.read_csv(ROOT/'mlc_results/expanded_student_features.csv')
        self.tr=self.frame[self.frame.cohort.ne('2026 SPR')]
        self.va=self.frame[self.frame.cohort.eq('2026 SPR')]
        self.features=[v for group in GROUPS.values() for v in group]+GRADES
        self.m=PosteriorRegression().fit(self.tr[self.features],self.tr.percentage)

    def test_original_cpd_agrees_for_complete_evidence(self):
        notebook=json.loads((ROOT/'MLC_Bayesian_DAG_updated.ipynb').read_text())
        namespace={'np':np,'pd':pd,'itertools':itertools}
        exec(''.join(notebook['cells'][7]['source']),namespace)
        original=namespace['GaussianDAG'](features=self.features,shrinkage=10).fit(self.tr[self.features],self.tr.percentage)
        np.testing.assert_allclose(original.posterior['percentage']['mean'],self.m.mean,atol=1e-10)
        complete=self.va.dropna(subset=self.features)
        self.assertEqual(len(complete),29)
        np.testing.assert_allclose(original.predict_distribution(complete[self.features])[:,0],self.m.predictive(complete[self.features])[0],atol=1e-10)

    def test_independent_draws_match_analytic_posterior_and_student_t(self):
        rng=np.random.default_rng(41)
        b,v=self.m.sample(rng,60000)
        variance=self.m.b/(self.m.a-1)
        se=np.sqrt(variance*np.diag(self.m.cov_unit)/len(b))
        self.assertLess(np.max(abs(b.mean(axis=0)-self.m.mean)/se),4.5)
        self.assertAlmostEqual(v.mean()/variance,1,delta=.01)
        x=self.va[self.features].iloc[:1]
        loc,scale,df=self.m.predictive(x)
        y=(b@self.m.matrix(x).T).ravel()*self.m.y_scale+self.m.y_center+rng.normal(size=len(v))*np.sqrt(v)*self.m.y_scale
        np.testing.assert_allclose(np.quantile(y,[.05,.5,.95]),stats.t.ppf([.05,.5,.95],df,loc=loc[0],scale=scale[0]),atol=.2)

    def test_validation_extremes_do_not_change_training_preprocessing(self):
        before=(self.m.medians.copy(),self.m.center.copy(),self.m.scale.copy(),self.m.mean.copy())
        x=self.va[self.features].copy();x.iloc[:]=1e9
        self.m.predictive(x)
        pd.testing.assert_series_equal(before[0],self.m.medians)
        for a,b in zip(before[1:],[self.m.center,self.m.scale,self.m.mean]):
            np.testing.assert_array_equal(a,b)
        # Missing evidence has a defined imputed-design distribution.
        x.iloc[:]=np.nan
        loc,scale,df=self.m.predictive(x)
        self.assertTrue(np.isfinite(loc).all() and (scale>0).all())

    def test_diagnostics_detect_nonconvergence(self):
        rng=np.random.default_rng(29)
        good=rng.normal(size=(4,2000,2))
        d=diagnostics(good,['a','b'])
        self.assertLess(d.rank_split_Rhat.max(),1.01)
        bad=good.copy();bad[0,:,0]+=5
        self.assertGreater(diagnostics(bad,['a','b']).rank_split_Rhat.iloc[0],1.1)


if __name__=='__main__':
    unittest.main()
