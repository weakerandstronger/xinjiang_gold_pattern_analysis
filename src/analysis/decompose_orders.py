"""Split the fixed positive pattern game by item order without changing it."""
from pathlib import Path
from collections import defaultdict, Counter
import json, math
from io_records import read_csv, write_csv, write_json, load
from mine_support import analyze

def run(baseline, output, data, config):
    output.mkdir(parents=True,exist_ok=True)
    patterns=read_csv(baseline/'patterns.csv')
    features=read_csv(baseline/'features.csv')
    split={k:[p for p in patterns if int(p['order'])==k] for k in [2,3]}
    if [len(split[k]) for k in [2,3]]!=[1398,10565]:raise ValueError('Unexpected fixed-baseline pattern counts')
    totals={k:math.fsum(float(p['evidence']) for p in split[k]) for k in [2,3]}
    total=math.fsum(totals.values());scores={};residuals=[]
    for k,ps in split.items():
        grouped=defaultdict(list);itemwise=defaultdict(list)
        for p in ps:
            members=json.loads(p['stable_key']); counts=Counter(f for f,v in members)
            e=float(p['evidence'])
            for f in counts:grouped[f].append(e/len(counts))
            for f,v in members:itemwise[f].append(e/len(counts)/counts[f])
        scores[k]={f['feature']:math.fsum(grouped[f['feature']]) for f in features}
        for f,v in scores[k].items():
            residuals.append(abs(v-math.fsum(itemwise[f])))
            if not math.isclose(v,math.fsum(itemwise[f]),abs_tol=1e-12,rel_tol=1e-10):raise ValueError('Group/item allocation mismatch')
        if not math.isclose(math.fsum(scores[k].values()),totals[k],abs_tol=1e-12,rel_tol=1e-10):raise ValueError('Allocation is not conserved')
        write_csv(output/f'patterns_order{k}.csv',ps)
    # Independent pair-only mining validates the subset against the input records.
    _,fields,_,samples,_,_=load(data)
    pair=analyze(samples,{**config['analysis'],'max_order':2})
    expected={tuple(tuple(x) for x in json.loads(p['stable_key'])) for p in split[2]}
    actual={tuple((fields[f],v) for f,v in p['items']) for p in pair[4]}
    if actual!=expected:raise ValueError('Pair-only pattern membership mismatch')
    for i,f in enumerate(fields):
        if not math.isclose(pair[5][i],scores[2][f],abs_tol=1e-12,rel_tol=1e-10):raise ValueError('Pair-only score mismatch')
    rows=[]
    for r in features:
        f=r['feature'];a,b=scores[2][f],scores[3][f];reconstructed=(a+b)/total
        weighted=totals[2]/total*(a/totals[2])+totals[3]/total*(b/totals[3])
        if not math.isclose(reconstructed,float(r['share']),abs_tol=1e-12,rel_tol=1e-10):raise ValueError('Share reconstruction mismatch')
        rows.append(dict(feature=f,feature_cn=r['feature_cn'],baseline_rank=int(r['rank']),observed_n=int(r['observed_n']),total_n=int(r['total_n']),coverage=float(r['coverage']),
            order2_score=a,order3_score=b,order2_share=a/totals[2],order3_share=b/totals[3],order2_total_contribution=a/total,order3_total_contribution=b/total,
            original_score=float(r['score']),reconstructed_score=a+b,score_error=a+b-float(r['score']),original_share=float(r['share']),reconstructed_share=reconstructed,weighted_share=weighted,
            share_error=reconstructed-float(r['share']),original_F1_share=float(r['share']),order3_minus_order2_pp=100*(b/totals[3]-a/totals[2])))
    write_csv(output/'feature_reconciliation.csv',rows)
    for k in [2,3]:
        ranked=sorted(rows,key=lambda r:-r[f'order{k}_score'])
        write_csv(output/f'features_order{k}.csv',[dict(rank=i+1,feature=r['feature'],feature_cn=r['feature_cn'],score=r[f'order{k}_score'],share=r[f'order{k}_share'],total_contribution=r[f'order{k}_total_contribution'],observed_n=r['observed_n'],total_n=r['total_n'],coverage=r['coverage']) for i,r in enumerate(ranked)])
    write_json(output/'summary.json',dict(patterns_order2=len(split[2]),patterns_order3=len(split[3]),evidence_order2=totals[2],evidence_order3=totals[3],evidence_total=total,
        weight_order2=totals[2]/total,weight_order3=totals[3]/total,max_score_error=max(abs(r['score_error']) for r in rows),max_share_error=max(abs(r['share_error']) for r in rows),
        pair_only_mining_matches=True,max_item_group_error=max(residuals),within_order_share_sums={k:math.fsum(r[f'order{k}_share'] for r in rows) for k in [2,3]}))
    return rows
