"""Exploratory Gaussian DAG posterior over six non-grade inputs and final grade.

Unlike analysis.gibbs, this sampler adds, deletes and reverses arrows. The BGe
score uses compatible normal-Wishart subset marginals, so Markov-equivalent
DAGs have equal likelihood scores. Direction frequencies remain conditional on
this observational model and graph prior; they do not identify causal effects.

Run: .venv/bin/python -m posterior_study.structure_learning --output PATH
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import multigammaln, logsumexp
from .analysis import ROOT, GROUPS, diagnostics
from .cohort_policy import exclude_summer_rows

COLUMNS = [x for g in GROUPS.values() for x in g] + ['percentage']
LABELS = ['LMS page views', 'LMS participation', 'EVC cost/support',
          'EVC expectancy', 'EVC value', 'Wellness', 'Final grade']


def bge_local_scores(x, prior_scale=1., kappa=1., extra_df=2.):
    """Log p(X_child | X_parents) by ratios of compatible subset marginals.

    Full precision ~ Wishart(nu=d+extra_df, T^-1); mean|precision ~
    N(0, (kappa*precision)^-1). T=prior_scale*kappa/(kappa+1)*(nu-d-1) I.
    Thus the full prior predictive covariance is prior_scale*I. Subset precision
    has df nu-d+|S|. For S, integrate its proper normal-Wishart prior exactly.
    Data are centered/scaled beforehand; these are empirical scale conventions.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all() or len(x) < 3:
        raise ValueError('Need a finite 2D dataset with at least three records')
    if prior_scale <= 0 or kappa <= 0 or extra_df <= 1:
        raise ValueError('Improper normal-Wishart prior parameters')
    n, d = x.shape
    mean = x.mean(axis=0)
    scatter = (x-mean).T@(x-mean)
    t = np.eye(d)*prior_scale*kappa/(kappa+1)*(extra_df-1)
    r = t+scatter+(kappa*n/(kappa+n))*np.outer(mean, mean)
    marginal = np.zeros(1 << d)
    for mask in range(1, 1 << d):
        index = [i for i in range(d) if mask & (1 << i)]
        k = len(index); nu = extra_df+k
        sign_t, log_t = np.linalg.slogdet(t[np.ix_(index, index)])
        sign_r, log_r = np.linalg.slogdet(r[np.ix_(index, index)])
        if min(sign_t, sign_r) <= 0:
            raise ValueError('Prior/posterior scale not positive definite')
        marginal[mask] = (-n*k/2*np.log(np.pi)
            +k/2*np.log(kappa/(kappa+n))
            +nu/2*log_t-(nu+n)/2*log_r
            +multigammaln((nu+n)/2, k)-multigammaln(nu/2, k))
    local = np.full((d, 1 << d), np.nan)
    for child in range(d):
        for parents in range(1 << d):
            if not parents & (1 << child):
                local[child, parents] = marginal[parents | (1 << child)]-marginal[parents]
    return local


def acyclic(parents):
    parents = tuple(map(int, parents))
    done = 0
    for _ in range(len(parents)):
        old = done
        for j, pa in enumerate(parents):
            if not (done & (1 << j)) and not (pa & ~done):
                done |= 1 << j
        if done == (1 << len(parents))-1:
            return True
        if done == old:
            return False
    return False


def is_ancestor(parents, ancestor, node):
    todo = parents[node]; seen = 0
    while todo:
        if todo & (1 << ancestor):
            return True
        bit = todo & -todo; todo ^= bit
        if not seen & bit:
            seen |= bit
            todo |= parents[bit.bit_length()-1] & ~seen
    return False


def log_posterior(parents, local, adjacency_prior=.5):
    """Prior: each unordered pair is absent (1-q) or oriented either way (q/2),
    conditioned jointly on acyclicity. This is a prior on DAGs, not on orders.
    The acyclicity normalizer and common dyad constants cancel in MH ratios.
    q is the pre-conditioning dyad parameter, not the marginal DAG edge rate.
    """
    parents = tuple(map(int, parents))
    if not 0 < adjacency_prior < 1:
        raise ValueError('adjacency_prior must be between zero and one')
    if not acyclic(parents):
        return -np.inf
    return sum(local[j, pa] for j, pa in enumerate(parents)) + sum(
        pa.bit_count() for pa in parents)*np.log(adjacency_prior/(2*(1-adjacency_prior)))


def sample_dags(local, adjacency_prior=.5, chains=4, warmup=20000,
                draws=10000, thin=10, seed=7291):
    """Symmetric Metropolis-Hastings moves on an unordered pair's 3 states.

    Pick a dyad uniformly, then one of its other two states uniformly. Reject
    cyclic proposals. The proposal is symmetric even at graphs with different
    numbers of legal moves; there is no legal-neighbor-count bias.
    """
    if not 0 < adjacency_prior < 1 or min(chains, draws, thin) < 1 or warmup < 0:
        raise ValueError('Invalid sampling configuration')
    d = local.shape[0]
    if not 2 <= d <= 8:
        raise ValueError('Parent-bitmask storage supports 2–8 nodes')
    pairs = list(itertools.combinations(range(d), 2))
    edge_log_prior = np.log(adjacency_prior/(2*(1-adjacency_prior)))
    samples = np.empty((chains, draws, d), dtype=np.uint8)
    logs = np.empty((chains, draws)); accepted = []
    for c in range(chains):
        rng = np.random.default_rng(seed+c)
        parents = [0]*d
        # Starts vary from empty to dense DAGs in different topological orders.
        if c:
            order = rng.permutation(d)
            for a in range(d):
                for b in range(a+1, d):
                    if rng.random() < c/max(chains-1, 1):
                        parents[int(order[b])] |= 1 << int(order[a])
        logp = log_posterior(parents, local, adjacency_prior)
        total = warmup+draws*thin
        moves = rng.integers(0, 2*len(pairs), size=total)
        uniforms = np.log(rng.random(total))
        accepts = 0
        for step in range(total):
            move = int(moves[step]); a, b = pairs[move//2]
            state = 1 if parents[b] & (1 << a) else 2 if parents[a] & (1 << b) else 0
            new_state = (state+1+move%2)%3
            old_a, old_b = parents[a], parents[b]
            parents[a] &= ~(1 << b); parents[b] &= ~(1 << a)
            if new_state == 1:
                legal = not is_ancestor(parents, b, a)
                parents[b] |= 1 << a
            elif new_state == 2:
                legal = not is_ancestor(parents, a, b)
                parents[a] |= 1 << b
            else:
                legal = True
            if legal:
                delta = (local[a, parents[a]]+local[b, parents[b]]
                         -local[a, old_a]-local[b, old_b]
                         +edge_log_prior*((new_state != 0)-(state != 0)))
                if uniforms[step] < delta:
                    logp += delta
                    if step >= warmup:
                        accepts += 1
                else:
                    parents[a], parents[b] = old_a, old_b
            else:
                parents[a], parents[b] = old_a, old_b
            if step >= warmup and (step-warmup+1)%thin == 0:
                k = (step-warmup)//thin
                samples[c, k] = parents
                # Avoid accumulated floating-point drift in repeated visits.
                logs[c, k] = log_posterior(parents, local, adjacency_prior)
        assert acyclic(parents)
        np.testing.assert_allclose(logp, log_posterior(parents, local, adjacency_prior), atol=1e-7)
        accepted.append(accepts/(draws*thin))
    return samples, logs, accepted


def indicators(samples):
    d = samples.shape[-1]
    oriented = np.stack([((samples[:, :, b] >> a) & 1) for a in range(d)
                         for b in range(d) if a != b], axis=-1).astype(float)
    keys = [(a, b) for a in range(d) for b in range(d) if a != b]
    return oriented, keys


def summarize(samples, logs, names):
    oriented, keys = indicators(samples)
    values = []; labels = []; rows = []
    for a, b in itertools.combinations(range(len(names)), 2):
        forward = oriented[:, :, keys.index((a, b))]
        reverse = oriented[:, :, keys.index((b, a))]
        adjacency = forward+reverse
        pa = float(adjacency.mean()); pf = float(forward.mean()); pr = float(reverse.mean())
        rows.append(dict(a=names[a], b=names[b], p_connection=pa,
            p_a_to_b=pf, p_b_to_a=pr,
            p_a_to_b_given_connection=pf/pa if pa else np.nan,
            minimum_chain_connection=float(adjacency.mean(axis=1).min()),
            maximum_chain_connection=float(adjacency.mean(axis=1).max())))
        for suffix, val in [('connection', adjacency), ('forward', forward), ('reverse', reverse)]:
            values.append(val); labels.append(f'{names[a]}__{names[b]}__{suffix}')
    # Equivalent graphs have equal scores mathematically. Canonical rounding
    # removes <1e-8 log-unit arithmetic ties from rank-based diagnostics only;
    # it never affects MCMC acceptance or sampled graph frequencies.
    values += [np.round(logs, 8), oriented.sum(axis=-1)]
    labels += ['log_posterior', 'number_of_edges']
    cube = np.stack(values, axis=-1)
    # Near-deterministic indicators are shown explicitly, not assigned fake R-hat.
    sd = cube.std(axis=(0, 1))
    active = sd > 0
    # Bernoulli tail quantiles can be constant, so tail ESS is inapplicable.
    # The existing continuous-draw diagnostic can divide by zero for those
    # deliberately degenerate tail indicators; handle/report them explicitly.
    with np.errstate(invalid='ignore', divide='ignore'):
        diag = diagnostics(cube[:, :, active], np.asarray(labels)[active].tolist())
    binary = ~diag.parameter.isin(['log_posterior', 'number_of_edges'])
    diag.loc[binary, 'tail_ESS'] = np.nan
    diag['binary_tail_ESS_not_applicable'] = binary
    inactive = pd.DataFrame({'parameter':np.asarray(labels)[~active],
        'rank_split_Rhat':np.nan, 'bulk_ESS':np.nan, 'tail_ESS':np.nan,
        'mean_MCSE':np.nan, 'binary_tail_ESS_not_applicable':True})
    diag = pd.concat([diag, inactive], ignore_index=True)
    means = dict(zip(labels, cube.mean(axis=(0,1))))
    diag['sample_mean'] = diag.parameter.map(means)
    diag['constant_in_retained_samples'] = diag.parameter.isin(np.asarray(labels)[~active])
    return pd.DataFrame(rows), diag


def standardized(frame):
    x = frame.to_numpy(dtype=float)
    sd = x.std(axis=0)
    if not np.isfinite(x).all() or (sd <= 0).any():
        raise ValueError('Nonfinite or constant input')
    return (x-x.mean(axis=0))/sd


def run(output, draws=10000, warmup=20000, thin=10):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    path = ROOT/'mlc_results/expanded_student_features.csv'
    full, policy = exclude_summer_rows(pd.read_csv(path))
    missing = full[COLUMNS].isna().sum()
    complete = full.dropna(subset=COLUMNS)
    within = complete[COLUMNS]-complete.groupby('cohort')[COLUMNS].transform('mean')
    # Hold graph dimension fixed across sensitivities; no grade components included.
    scenarios = [
        ('complete_main', complete[COLUMNS], .5, 1.),
        ('complete_sparse_prior', complete[COLUMNS], .2, 1.),
        ('complete_uniform_dag_prior', complete[COLUMNS], 2/3, 1.),
        ('complete_prior_scale_quarter', complete[COLUMNS], .5, .25),
        ('complete_prior_scale_four', complete[COLUMNS], .5, 4.),
        ('complete_within_cohort', within, .5, 1.),
        ('median_imputed', full[COLUMNS].fillna(full[COLUMNS].median()), .5, 1.),
        ('earlier_terms_only', complete.loc[complete.cohort.ne('2026 SPR'), COLUMNS], .5, 1.)]
    all_rows = []; status = []
    for name, data, q, prior_scale in scenarios:
        local = bge_local_scores(standardized(data), prior_scale)
        samples, logs, accept = sample_dags(local, q, draws=draws, warmup=warmup, thin=thin)
        edges, diag = summarize(samples, logs, COLUMNS)
        edges.insert(0, 'scenario', name);edges.insert(1, 'n', len(data));all_rows.append(edges)
        diag.to_csv(output/f'{name}_diagnostics.csv', index=False)
        np.savez_compressed(output/f'{name}_sampled_graphs.npz', parents=samples, log_posterior=logs)
        keydiag = diag[(diag.sample_mean.between(.01,.99)) | diag.parameter.isin(['log_posterior','number_of_edges'])]
        item=dict(scenario=name, n=len(data), adjacency_prior_parameter=q,
            prior_predictive_scale=prior_scale, max_Rhat_nonrare=float(keydiag.rank_split_Rhat.max()),
            min_bulk_ESS_nonrare=float(keydiag.bulk_ESS.min()),
            acceptance_per_chain=accept, mean_edges=float(np.mean([int(i).bit_count() for i in samples.ravel()])*len(COLUMNS)))
        status.append(item)
        print(json.dumps(item), flush=True)
    edges = pd.concat(all_rows, ignore_index=True)
    edges.to_csv(output/'edge_probabilities_all_scenarios.csv', index=False)
    main = edges[edges.scenario.eq('complete_main')].sort_values('p_connection', ascending=False)
    main.to_csv(output/'main_edge_probabilities.csv', index=False)
    stability = edges.groupby(['a','b']).agg(min_connection=('p_connection','min'),
        max_connection=('p_connection','max')).reset_index()
    stability = stability.merge(main[['a','b','p_connection','p_a_to_b','p_b_to_a']], on=['a','b'])
    stability.sort_values('min_connection',ascending=False).to_csv(output/'connection_stability.csv',index=False)
    metadata = dict(input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        variables=COLUMNS, labels=LABELS, input_rows=len(full), complete_rows=len(complete),
        missing_by_variable=missing.to_dict(), complete_by_term=complete.groupby('cohort').size().to_dict(),
        excluded_summer_policy=policy, draws_per_chain=draws, chains=4, warmup=warmup,
        retained_every=thin, total_retained_per_scenario=draws*4,
        score='BGe, normal-Wishart subset marginals; centered/scaled per analysis dataset',
        graph_prior='independent dyads (1-q, q/2, q/2), jointly conditioned on acyclicity; q=2/3 uniform over DAGs',
        constraints='acyclic only; no imposed arrow directions; all 7 nodes, no parent cap',
        diagnostics_note='log scores rounded to 8 decimal places for ranks only, to identify numerical ties between equivalent DAGs; binary tail ESS not applicable; constant indicators have no estimable R-hat/ESS',
        seed=7291, scenarios=status,
        scope='exploratory all-cohort association structure; not prospective validation or causal identification')
    (output/'provenance.json').write_text(json.dumps(metadata,indent=2))
    return main, stability


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--draws',type=int,default=10000);ap.add_argument('--warmup',type=int,default=20000)
    ap.add_argument('--thin',type=int,default=10)
    args=ap.parse_args();run(args.output,args.draws,args.warmup,args.thin)
