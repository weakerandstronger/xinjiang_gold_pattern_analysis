"""Single fixed-data execution. No stochastic or performance experiment dependencies."""
import argparse
import os
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from io_records import load, read_csv, write_csv, write_json, normalize
from mine_support import analyze, independent_checks

ROOT = Path(os.environ['XINJIANG_ANALYSIS_DIR']).resolve()
CN = dict(Alteration='蚀变', Fluid='流体', Geochem='化探', Geophysics='物探', HostRockUnit='赋矿岩性', IntrusiveBody='侵入体', Isotope='同位素', Mineral='矿物', Region='区域', StratUnit='地层', Structure='构造')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def stable_key(us, features):
    return json.dumps([[features[f], v] for f,v in sorted(us)], ensure_ascii=False, separators=(',', ':'))

def inputs(cfg):
    paths=[Path(cfg['input']),ROOT/'config.json']
    return {str(p.resolve()):sha(p) for p in paths}

def main():
    cfg = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    cfg['input'] = str((ROOT / cfg['input']).resolve())
    for d in ['results','tables','figures/main','figures/data','audit']:
        (ROOT/d).mkdir(parents=True,exist_ok=True)
    snapshot = inputs(cfg)
    assert sha(cfg['input']) == cfg['expected_input_sha256'], 'Input version mismatch'
    write_json(ROOT/'audit/input_snapshot.json', {Path(k).name:v for k,v in snapshot.items()})
    raw, features, names, samples, records, groups = load(cfg['input'])
    obs, im, eligible, pool, ps, fs, vs = analyze(samples, cfg['analysis'])
    checks = {'mathematics':independent_checks(samples,cfg['analysis'],obs,im,eligible,pool,ps,fs,vs)}
    assert 'Isotope' not in features and len(features)==10
    checks['feature_scope'] = dict(status='passed',excluded=['Isotope'],included=features)
    n, z = len(samples), sum(p['evidence'] for p in ps)
    us = sorted(im)
    ids = {u:f'U{i+1:04d}' for i,u in enumerate(us)}
    entity_ids = {name:f'E{i+1:03d}' for i,name in enumerate(names)}
    order = sorted(range(len(features)),key=lambda i:(-fs[i],i))
    feats = [dict(feature=features[i],feature_cn=CN[features[i]],feature_index=i,
                  observed_n=obs[i].bit_count(),total_n=n,coverage=obs[i].bit_count()/n,
                  distinct_values=sum(u[0]==i for u in us),eligible_values=sum(u[0]==i for u in eligible),
                  positive_pattern_values=sum(u[0]==i and vs.get(u,0)>0 for u in us),
                  score=fs[i],share=fs[i]/z if z else None,rank=r+1) for r,i in enumerate(order)]
    items = [dict(item_id=ids[u],feature=features[u[0]],feature_cn=CN[features[u[0]]],
                  value_raw=u[1],typed_key=stable_key([u],features),count=im[u].bit_count(),
                  score=vs.get(u,0.),global_share=vs.get(u,0.)/z if z else None,
                  within_feature_share=vs.get(u,0.)/fs[u[0]] if fs[u[0]]>0 else None) for u in us]
    byid = {r['item_id']:r for r in items}
    patterns, members = [], []
    for k,p in enumerate(ps,1):
        pid = f'P{k:05d}'
        r = dict(pattern_id=pid,stable_key=stable_key(p['items'],features),item_ids=[ids[u] for u in p['items']],
                 order=len(p['items']),feature_groups=len(p['group_counts']),count=p['count'],valid_n=p['valid_n'],
                 group_counts={features[f]:c for f,c in p['group_counts'].items()},support=p['support'],
                 group_lift=p['group_lift'],evidence=p['evidence'],
                 entity_ids=[entity_ids[names[i]] for i in range(n) if p['hits']&(1<<i)],rank=k)
        patterns.append(r)
        for u in p['items']:
            members.append(dict(pattern_id=pid,item_id=ids[u],feature=features[u[0]],value_raw=u[1]))
    group_sources = [dict(entity_id=entity_ids[name],group_name=name,csv_row_number=i+2,doc_id=raw[i]['doc_id'],raw_name=raw[i]['Deposit']) for name,rows in groups.items() for i in rows]
    entities = [dict(entity_id=entity_ids[name],group_name=name,source_row_count=len(groups[name]),
                     observed_feature_count=sum(v is not None for v in samples[i]),
                     values_by_feature={f:sorted(samples[i][j]) if samples[i][j] is not None else None for j,f in enumerate(features)}) for i,name in enumerate(names)]
    write_csv(ROOT/'results/features.csv',feats)
    write_csv(ROOT/'results/items.csv',items)
    write_csv(ROOT/'results/patterns.csv',patterns)
    write_csv(ROOT/'results/pattern_members.csv',members)
    write_csv(ROOT/'results/group_sources.csv',group_sources)
    write_csv(ROOT/'results/entities.csv',entities)
    # Display and case selections are pure queries on the full result tables.
    selected, f2 = [], []
    for row in feats:
        selected.append(dict(figure='F1',pool='all_features',pool_rank=row['rank'],selected_id=row['feature'],panel=1,display_order=row['rank'],rule='all_features_by_score_desc_then_original_column'))
    for panel, f in enumerate([f for f in feats if f['score']>0][:cfg['display']['F2_features']],1):
        candidates = sorted([r for r in items if r['feature']==f['feature']],key=lambda r:(-r['score'],r['item_id']))
        take = candidates[:cfg['display']['F2_items']]
        total = sum(r['within_feature_share'] for r in take)
        for rank,r in enumerate(take,1):
            f2.append(dict(**r,panel=panel,display_order=rank,feature_global_share=f['share'],displayed_within_share=total))
            selected.append(dict(figure='F2',pool=f['feature'],pool_rank=rank,selected_id=r['item_id'],panel=panel,display_order=rank,rule='top6_positive_features_each_top5_items'))
    f3=[]
    pools=[('全库高证据组合',patterns)]
    chosen=set()
    without = [r for r in patterns if 'Region' not in r['group_counts']]
    for panel,(label,candidates) in enumerate([pools[0],('不含Region字段的组合',without)],1):
        limit=cfg['display']['F3_overall'] if panel==1 else cfg['display']['F3_without_Region']
        picked=0
        for pool_rank,r in enumerate(candidates,1):
            if r['pattern_id'] in chosen:continue
            picked+=1; chosen.add(r['pattern_id'])
            text='\n'.join(f"{byid[i]['feature_cn']}：{byid[i]['value_raw']}" for i in r['item_ids'])
            f3.append(dict(**r,panel=panel,pool_label=label,pool_rank=pool_rank,display_order=picked,members_text=text))
            selected.append(dict(figure='F3',pool=label,pool_rank=pool_rank,selected_id=r['pattern_id'],panel=panel,display_order=picked,rule='top4_overall_then_top4_without_Region_excluding_chosen'))
            if picked==limit:break
    write_csv(ROOT/'results/display_selection.csv', selected)
    write_csv(ROOT/'figures/data/F1.csv',feats)
    write_csv(ROOT/'figures/data/F2.csv',f2)
    write_csv(ROOT/'figures/data/F3.csv',f3)
    write_csv(ROOT/'results/label_map.csv',[dict(item_id=r['item_id'],feature=r['feature'],value_raw=r['value_raw'],display_label=r['value_raw'],shortened=False,reason='原词完整保留，绘图仅换行') for r in items])
    cases=[]
    def add_case(candidates,role):
        if not candidates:return
        p=candidates[0]
        found=next((c for c in cases if c['pattern_id']==p['pattern_id']),None)
        if found:found['roles'].append(role)
        else:cases.append(dict(**p,roles=[role]))
    add_case(patterns,'全库最高证据')
    add_case(without,'不含Region最高证据')
    if cfg['display']['include_mineral_alteration_case']:
        add_case([r for r in patterns if {'Mineral','Alteration'}<=r['group_counts'].keys()],'同时含Mineral与Alteration最高证据')
    case_rows=[]; source_lookup={}
    def locate(doc_id):
        # Corrected CSV is the authority; old JSON may contain superseded values.
        return dict(base_doc_id='',title='',output_path='',set_json_path='',source_status='当前修订CSV行；未与历史JSON或原文逐项重对齐')
    for case in cases:
        pattern=ps[int(case['pattern_id'][1:])-1]
        same=0
        for ei,name in enumerate(names):
            if not pattern['hits']&(1<<ei):continue
            joint=False
            for ri in groups[name]:
                present=[ids[u] for u in pattern['items'] if records[ri][u[0]] is not None and u[1] in records[ri][u[0]]]
                full=len(present)==len(pattern['items']);joint|=full
                src=locate(raw[ri]['doc_id'])
                case_rows.append(dict(case_id=case['pattern_id'],entity_id=entity_ids[name],group_name=name,csv_row_number=ri+2,doc_id=raw[ri]['doc_id'],required_item_ids=case['item_ids'],present_required_item_ids=present,all_required_in_row=full,**src))
            same+=int(joint)
        case['same_source_row_groups']=same
        case['union_only_groups']=case['count']-same
        case['members_text']='；'.join(f"{byid[i]['feature_cn']}={byid[i]['value_raw']}" for i in case['item_ids'])
        assert 0<=same<=case['count']
    write_csv(ROOT/'results/case_record_evidence.csv',case_rows)
    write_csv(ROOT/'tables/T2_case_counts.csv',cases)
    write_json(ROOT/'results/cases.json',cases)
    write_json(ROOT/'audit/source_lookup.json',source_lookup)
    # Deterministic overlap description, not an independent validation metric.
    overlaps=[]
    from itertools import combinations
    for a,b in combinations(f3,2):
        aa,bb=set(a['entity_ids']),set(b['entity_ids'])
        overlaps.append(dict(pattern_a=a['pattern_id'],pattern_b=b['pattern_id'],intersection_n=len(aa&bb),union_n=len(aa|bb),same_match_set=aa==bb,jaccard=len(aa&bb)/len(aa|bb)))
    write_csv(ROOT/'tables/F3_match_overlap.csv',overlaps)
    stats=dict(raw_rows=len(raw),unique_doc_ids=len({r['doc_id'] for r in raw}),name_groups=n,features=len(features),
               observed_cells=sum(b.bit_count() for b in obs),unknown_cells=n*len(features)-sum(b.bit_count() for b in obs),
               multivalue_cells=sum(v is not None and len(v)>1 for row in samples for v in row),
               known_empty_cells=sum(v is not None and len(v)==0 for row in samples for v in row),
               distinct_items=len(im),singlevalue_cells=sum(v is not None and len(v)==1 for row in samples for v in row),
               attribute_occurrences=sum(len(v) for row in samples for v in row if v is not None),singletons=sum(b.bit_count()==1 for b in im.values()),eligible_items=len(eligible),
               candidates=len(pool),patterns=len(ps),pairs=sum(len(p['items'])==2 for p in ps),triples=sum(len(p['items'])==3 for p in ps),
               two_group_triples=sum(len(p['items'])==3 and len(p['group_counts'])==2 for p in ps),without_Region=len(without),
               total_evidence=z,exact_duplicate_rows=len(raw)-len({tuple(r.items()) for r in raw}),
               top3_feature_share=sum(fs[i]/z for i in order[:3]) if z else None,
               analysis_input_sha256=sha(cfg['input']))
    write_json(ROOT/'results/summary.json',stats)
    write_json(ROOT/'audit/input_snapshot.json',{Path(k).name:v for k,v in snapshot.items()})
    assert all(sha(p)==h for p,h in snapshot.items())
    checks['input_immutability']=dict(status='passed',checked_files=len(snapshot))
    checks['case_trace']=dict(status='passed',cases=len(cases),all_matching_groups_accounted=True)
    checks['visual_review']=dict(status='not_run',reason='Pending actual figure and HTML inspection')
    write_json(ROOT/'audit/checks.json',checks)
    write_json(ROOT/'audit/provenance.json',dict(executable=Path(sys.executable).name,python=sys.version,run_time=datetime.now().astimezone().isoformat(),mode=cfg['mode'],disabled=cfg['disabled'],input_sha256=sha(cfg['input']),config_sha256=sha(ROOT/'config.json'),code_hashes={p.name:sha(p) for p in Path(__file__).resolve().parent.glob('*.py')},definition='Method equations 2-11; explicit positive low-order proxy, fixed pattern game'))
    print(json.dumps(stats,ensure_ascii=True))
    print('Saved fixed-data results and record-level case evidence.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    main()
