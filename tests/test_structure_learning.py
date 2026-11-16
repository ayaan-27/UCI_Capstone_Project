"""Independent checks of the BGe score, graph prior and MCMC stationary target."""
import itertools
import unittest
from collections import Counter
import numpy as np
from scipy import stats
from scipy.special import logsumexp
from posterior_study.structure_learning import (bge_local_scores, acyclic,
    log_posterior, sample_dags, indicators)


def all_three_node_dags():
    return [pa for pa in itertools.product(*[[m for m in range(8) if not m & (1 << j)]
            for j in range(3)]) if acyclic(pa)]


def equivalence_signature(parents):
    d=len(parents)
    skeleton=tuple((i,j) for i in range(d) for j in range(i+1,d)
        if (parents[j] & (1 << i)) or (parents[i] & (1 << j)))
    colliders=[]
    for j in range(d):
        pa=[i for i in range(d) if parents[j] & (1 << i)]
        for a,b in itertools.combinations(pa,2):
            if not (parents[a] & (1 << b) or parents[b] & (1 << a)):
                colliders.append((a,j,b))
    return skeleton,tuple(colliders)


class StructureTests(unittest.TestCase):
    def test_univariate_marginal_matches_sequential_student_t_predictions(self):
        # Independent conjugate update, without using the subset-score formula.
        x=np.array([-.8,.3,1.4,-.2,.5,2.1,-1.3])
        k=1.;mu=0.;nu=3.;scale_matrix=.5; logp=0.
        for value in x:
            predictive_scale=np.sqrt(scale_matrix*(k+1)/(k*nu))
            logp+=stats.t.logpdf(value,nu,loc=mu,scale=predictive_scale)
            scale_matrix+=k/(k+1)*(value-mu)**2
            mu=(k*mu+value)/(k+1);k+=1;nu+=1
        self.assertAlmostEqual(bge_local_scores(x[:,None])[0,0],logp,places=10)

    def test_all_markov_equivalent_three_node_graphs_have_equal_score(self):
        x=np.random.default_rng(31).normal(size=(37,3))
        x[:,1]+=.8*x[:,0];x[:,2]+=.6*x[:,1]
        local=bge_local_scores(x);groups={}
        dags=all_three_node_dags();self.assertEqual(len(dags),25)
        for pa in dags:
            sig=equivalence_signature(pa)
            score=log_posterior(pa,local,.5)
            if sig in groups:self.assertAlmostEqual(score,groups[sig],places=10)
            groups[sig]=score
        self.assertEqual(len(groups),11)
        # Conditional independence is different for collider and chain graphs.
        self.assertNotAlmostEqual(log_posterior((0,1,2),local),
                                  log_posterior((0,5,0),local),places=3)

    def test_graph_sampler_matches_exact_enumeration_including_orientations(self):
        rng=np.random.default_rng(7);x=rng.normal(size=(20,3));x[:,1]+=.45*x[:,0]
        local=bge_local_scores(x);dags=all_three_node_dags();q=.35
        lp=np.array([log_posterior(pa,local,q) for pa in dags]);exact=np.exp(lp-logsumexp(lp))
        samples,logs,accept=sample_dags(local,q,warmup=4000,draws=18000,thin=2,seed=871)
        counts=Counter(map(tuple,samples.reshape(-1,3)))
        observed=np.array([counts[pa]/samples.shape[0]/samples.shape[1] for pa in dags])
        self.assertLess(np.max(np.abs(observed-exact)),.012)
        self.assertAlmostEqual(sum(observed),1.,places=10)
        self.assertTrue(all(0<a<1 for a in accept))
        bits,keys=indicators(samples)
        for k,(a,b) in enumerate(keys):
            truth=sum(w for w,pa in zip(exact,dags) if pa[b] & (1 << a))
            self.assertAlmostEqual(bits[:,:,k].mean(),truth,delta=.012)
        self.assertTrue(all(acyclic(pa) for pa in counts))

    def test_cycles_and_invalid_inputs_are_rejected(self):
        self.assertFalse(acyclic((4,1,2)))
        local=bge_local_scores(np.random.default_rng(1).normal(size=(10,3)))
        self.assertEqual(log_posterior((4,1,2),local),-np.inf)
        for q in [0,1,-1]:
            with self.assertRaises(ValueError):sample_dags(local,q,draws=2)
        with self.assertRaises(ValueError):bge_local_scores([[np.nan],[1],[2]])
