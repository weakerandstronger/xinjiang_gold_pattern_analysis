"""Compare regenerated numerical artifacts against the packaged reference results."""
from pathlib import Path
import argparse,csv,json,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
def check_csv(a,b):
    def read(p):
        with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.reader(f))
    x,y=read(a),read(b)
    if len(x)!=len(y):raise ValueError(f'Row count differs: {a.name}')
    if x[0]!=y[0]:raise ValueError(f'Columns differ: {a.name}')
    for i,(r,s) in enumerate(zip(x,y)):
        if len(r)!=len(s):raise ValueError(f'Column count differs at {a.name}:{i}')
        for c,d in zip(r,s):
            if c==d:continue
            try:ok=math.isclose(float(c),float(d),rel_tol=1e-10,abs_tol=1e-12)
            except ValueError:ok=False
            if not ok:raise ValueError(f'Value differs at {a.name}:{i}: {c!r} != {d!r}')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);args=p.parse_args()
    results=[]
    for folder in ['results/baseline','results/order_decomposition','tables','data/intermediate']:
        for reference in sorted((ROOT/folder).glob('*.csv')):
            relative=reference.relative_to(ROOT);candidate=args.run/relative
            check_csv(reference,candidate)
            results.append({'path':relative.as_posix(),'match':True,'byte_identical':reference.read_bytes()==candidate.read_bytes()})
    for rel in ['results/baseline/summary.json','results/baseline/cases.json']:
        if json.loads((ROOT/rel).read_text(encoding='utf-8'))!=json.loads((args.run/rel).read_text(encoding='utf-8')):raise ValueError(f'JSON differs: {rel}')
    figure_checks=[]
    for reference in sorted((ROOT/'figures').rglob('*.png')):
        rel=reference.relative_to(ROOT);candidate=args.run/rel
        if candidate.exists():figure_checks.append({'path':rel.as_posix(),'byte_identical':reference.read_bytes()==candidate.read_bytes()})
    report={'status':'passed','csv_files':len(results),'csv_byte_identical':sum(r['byte_identical'] for r in results),'atol':1e-12,'rtol':1e-10,'files':results,'figures':figure_checks,'figure_note':'Font/platform-dependent image identity is reported separately from numerical regression.'}
    (args.run/'validation').mkdir(exist_ok=True)
    (args.run/'validation/regression.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'csv_files':report['csv_files'],'byte_identical':report['csv_byte_identical'],'figures':figure_checks},indent=2))
if __name__=='__main__':main()
