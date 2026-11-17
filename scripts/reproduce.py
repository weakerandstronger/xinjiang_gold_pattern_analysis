"""Reproduce all numerical results and optionally the four publication figures."""
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, tempfile, hashlib
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src/analysis'),str(ROOT/'src/plotting')]
from decompose_orders import run as decompose

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'runs/reproduction')
    parser.add_argument('--skip-figures',action='store_true',help='Run all numerical computations without font/plot dependencies')
    args=parser.parse_args();out=args.output.resolve()
    if out.exists():raise ValueError('Output exists. Choose a new --output directory.')
    out.mkdir(parents=True)
    config=json.loads((ROOT/'configs/baseline.json').read_text(encoding='utf-8'))
    data=(ROOT/'configs'/config['input']).resolve()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='xinjiang-',dir=out) as tmp:
        stage=Path(tmp);cfg={**config,'input':str(data)}
        (stage/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
        env['XINJIANG_ANALYSIS_DIR']=str(stage)
        for name in ['run_analysis.py','export_paper_tables.py']:
            subprocess.run([sys.executable,str(ROOT/'src/analysis'/name)],env=env,check=True)
        destinations={'results':'results/baseline','tables':'tables','figures/data':'data/intermediate','audit':'validation/baseline'}
        for src,dst in destinations.items():
            target=out/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(stage/src),str(target))
    rows=decompose(out/'results/baseline',out/'results/order_decomposition',data,config)
    if not args.skip_figures:
        for folder,source in [('F1','results/baseline/features.csv'),('F2','data/intermediate/F2.csv'),('F3','data/intermediate/F3.csv')]:
            directory=out/'figures'/folder;directory.mkdir(parents=True)
            shutil.copy2(out/source,directory/'plot_data.csv')
            env['XINJIANG_FIGURE_DIR']=str(directory)
            subprocess.run([sys.executable,str(ROOT/f'src/plotting/plot_{folder.lower()}.py')],env=env,check=True)
        from plot_f4 import render
        render(rows,out/'figures/F4')
    provenance={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'figures_generated':not args.skip_figures,
        'input_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256((ROOT/'configs/baseline.json').read_bytes()).hexdigest(),
        'code_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['src','scripts'] for p in (ROOT/folder).rglob('*.py')}}
    (out/'validation/run.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'scripts/verify.py'),'--run',str(out)],check=True,env=env)
    print('Reproduction and numerical regression checks passed.')

if __name__=='__main__':main()
