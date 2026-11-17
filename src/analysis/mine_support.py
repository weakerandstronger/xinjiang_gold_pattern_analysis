"""Fixed low-order Group-Lift game and exact grouped allocation; stdlib only."""
from collections import defaultdict, Counter
from itertools import combinations
import math

def index(samples):
    obs = [0] * len(samples[0])
    items = defaultdict(int)
    for n, row in enumerate(samples):
        for f, values in enumerate(row):
            if values is not None:
                obs[f] |= 1 << n
                for value in values:
                    items[f, value] |= 1 << n
    return obs, dict(items)

def metric(us, obs, im, n):
    by = defaultdict(list)
    for u in us:
        by[u[0]].append(u)
    valid = (1 << n) - 1
    for f in by:
        valid &= obs[f]
    hits = valid
    for u in us:
        hits &= im[u]
    nm, count = valid.bit_count(), hits.bit_count()
    if nm == 0 or count == 0:
        return None
    gc = {}
    for f, members in by.items():
        b = valid
        for u in members:
            b &= im[u]
        gc[f] = b.bit_count()
    support = count / nm
    lift = support / math.prod(c / nm for c in gc.values())
    return dict(items=us, count=count, valid_n=nm, group_counts=gc,
                support=support, group_lift=lift,
                evidence=count / n * max(math.log(lift), 0), hits=hits)

def analyze(samples, cfg):
    obs, im = index(samples)
    eligible = sorted(u for u, b in im.items() if b.bit_count() >= max(cfg['min_item_count'], cfg['min_pattern_count']))
    pairs, adjacency, pool = {}, defaultdict(list), []
    def emit(us):
        if len({u[0] for u in us}) < 2:
            return
        p = metric(us, obs, im, len(samples))
        if p and p['valid_n'] >= cfg['min_observed'] and p['support'] >= cfg['min_support']:
            pool.append(p)
    for a, b in combinations(eligible, 2):
        bits = im[a] & im[b]
        if bits.bit_count() >= cfg['min_pattern_count']:
            pairs[a, b] = bits
            adjacency[a].append(b)
            emit((a, b))
    if cfg['max_order'] == 3:
        for a, others in adjacency.items():
            for b, c in combinations(others, 2):
                if (b, c) in pairs and (pairs[a, b] & im[c]).bit_count() >= cfg['min_pattern_count']:
                    emit((a, b, c))
    elif cfg['max_order'] != 2:
        raise ValueError('max_order must be 2 or 3')
    patterns = sorted((p for p in pool if p['group_lift'] > 1 + cfg['lift_epsilon']), key=lambda p: (-p['evidence'], p['items']))
    # Preserve the original summation order for a transparent numerical regression.
    feature_scores = [0.] * len(obs)
    scores = defaultdict(float)
    for p in patterns:
        counts = Counter(f for f, _ in p['items'])
        for u in p['items']:
            share = p['evidence'] / (len(counts) * counts[u[0]])
            scores[u] += share
            feature_scores[u[0]] += share
    return obs, im, eligible, pool, patterns, feature_scores, dict(scores)

def independent_checks(samples, cfg, obs, im, eligible, pool, patterns, feature_scores, scores):
    """Exhaustive eligible 2/3-item scan plus direct set counts, independent of prefix pruning."""
    expected = set()
    for k in range(2, cfg['max_order'] + 1):
        for us in combinations(eligible, k):
            if len({u[0] for u in us}) < 2:
                continue
            bits = (1 << len(samples)) - 1
            valid = bits
            for f, v in us:
                bits &= im[f, v]
                valid &= obs[f]
            if bits.bit_count() >= cfg['min_pattern_count'] and valid.bit_count() >= cfg['min_observed'] and bits.bit_count()/valid.bit_count() >= cfg['min_support']:
                expected.add(us)
    assert expected == {p['items'] for p in pool}, 'Candidate enumeration differs from exhaustive scan'
    max_lift_error, max_evidence_error, max_group_allocation_error = 0., 0., 0.
    for p in patterns:
        by = {f: {v for j, v in p['items'] if j == f} for f in {j for j, v in p['items']}}
        domain = [row for row in samples if all(row[f] is not None for f in by)]
        count = sum(all(required <= row[f] for f, required in by.items()) for row in domain)
        gc = {f: sum(required <= row[f] for row in domain) for f, required in by.items()}
        assert len(domain) == p['valid_n'] and count == p['count'] and gc == p['group_counts']
        assert 0 < count <= len(domain) <= len(samples) and all(count <= v <= len(domain) for v in gc.values())
        lift = (count/len(domain))/math.prod(v/len(domain) for v in gc.values())
        evidence = count/len(samples)*math.log(lift)
        max_lift_error = max(max_lift_error, abs(lift-p['group_lift']))
        max_evidence_error = max(max_evidence_error, abs(evidence-p['evidence']))
        assert math.isclose(lift,p['group_lift'],abs_tol=1e-10,rel_tol=1e-8)
        assert math.isclose(evidence,p['evidence'],abs_tol=1e-10,rel_tol=1e-8)
        assert p['support']==count/len(domain)
        assert lift > 1 + cfg['lift_epsilon']
        allocation = sum(p['evidence']/len(by)/len(by[f]) for f, _ in p['items'])
        max_group_allocation_error = max(max_group_allocation_error, abs(allocation-p['evidence']))
    z = sum(p['evidence'] for p in patterns)
    residuals = [abs(sum(feature_scores)-z), abs(sum(scores.values())-z)]
    direct_feature_residual=max((abs(feature_scores[f]-math.fsum(p['evidence']/len(p['group_counts']) for p in patterns if f in p['group_counts'])) for f in range(len(feature_scores))),default=0)
    assert direct_feature_residual <= 1e-10 + 1e-8*abs(z)
    within = [abs(sum(v for u, v in scores.items() if u[0]==f)/s-1) for f,s in enumerate(feature_scores) if s>0]
    assert max(residuals, default=0) <= 1e-10 + 1e-8*abs(z)
    assert max(within, default=0) <= 1e-10
    return dict(status='passed', atol=1e-10, rtol=1e-8, exhaustive_eligible_candidates=len(expected),
                direct_set_counts_all_patterns=True, max_lift_error=max_lift_error,
                max_evidence_error=max_evidence_error, max_single_pattern_allocation_error=max_group_allocation_error,
                feature_total_residual=residuals[0], item_total_residual=residuals[1],
                direct_feature_formula_max_residual=direct_feature_residual,
                within_feature_normalization_residual=max(within, default=0),
                global_normalization_residual=abs(sum(v/z for v in feature_scores)-1) if z else None)
