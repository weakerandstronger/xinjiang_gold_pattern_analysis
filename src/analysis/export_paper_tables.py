"""Export manuscript tables from the saved fixed-data analysis."""
import json
import os
from pathlib import Path
from io_records import read_csv,write_csv,write_json
ROOT=Path(os.environ['XINJIANG_ANALYSIS_DIR']).resolve()
def main():
    ps=read_csv(ROOT/'results/patterns.csv')
    entities={r['entity_id']:r['group_name'] for r in read_csv(ROOT/'results/entities.csv')}
    specs=[('区域—流体—构造',set(),'全库证据最高模式','按区域与构造条件定位流体资料'),('岩性—蚀变—矿物',{'Mineral','Alteration'},'同时含矿物与蚀变的最高证据模式','对照岩性背景与蚀变、矿物记载'),('元素异常—矿物—地层',{'Geochem','Mineral'},'同时含化探与矿物的最高证据模式','联查元素异常、矿物及地层信息')]
    topic=[]
    for theme,required,rule,use in specs:
        p=next(r for r in ps if required<=set(json.loads(r['group_counts'])))
        topic.append(dict(theme=theme,pattern_id=p['pattern_id'],selection_rule=rule,members=json.loads(p['stable_key']),count=int(p['count']),valid_n=int(p['valid_n']),group_lift=float(p['group_lift']),evidence=float(p['evidence']),matched_names=[entities[x] for x in json.loads(p['entity_ids'])],reading_use=use))
    write_json(ROOT/'tables/T3_topic_patterns.json',topic)
    write_csv(ROOT/'tables/T3_topic_patterns.csv',topic)
    s=json.loads((ROOT/'results/summary.json').read_text(encoding='utf-8'))
    values=[('来源记录',s['raw_rows']),('不同来源标识',s['unique_doc_ids']),('名称组',s['name_groups']),('特征',s['features']),('样本—特征单元',s['name_groups']*s['features']),('已观测单元',s['observed_cells']),('未知单元',s['unknown_cells']),('单值单元',s['singlevalue_cells']),('多值单元',s['multivalue_cells']),('显式空集合',s['known_empty_cells']),('类型化属性值',s['distinct_items']),('属性出现总次数',s['attribute_occurrences'])]
    write_csv(ROOT/'tables/T1_dataset_statistics.csv',[dict(statistic=k,value=v) for k,v in values])
    write_csv(ROOT/'tables/T2_analysis_settings.csv',[dict(parameter=k,value=v) for k,v in json.loads((ROOT/'config.json').read_text(encoding='utf-8'))['analysis'].items()])
    expected={'raw_rows': 355, 'unique_doc_ids': 355, 'name_groups': 76, 'features': 10, 'observed_cells': 555, 'unknown_cells': 205, 'singlevalue_cells': 161, 'multivalue_cells': 394, 'distinct_items': 1037, 'attribute_occurrences': 2364, 'patterns': 11963, 'pairs': 1398, 'triples': 10565}
    assert all(s[k]==v for k,v in expected.items()),'Results do not match manuscript snapshot'
    write_json(ROOT/'audit/paper_consistency.json',dict(status='passed',expected=expected,topic_patterns=[p['pattern_id'] for p in topic]))
    print('Manuscript tables exported; snapshot assertions passed.')
if __name__=='__main__':main()
