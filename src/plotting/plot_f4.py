"""Plot order-specific shares with the original F1 colors and typography."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import argparse, csv, hashlib, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

COLOR = dict(bar='#3F6F8E', grid='#E9EDF0', text='#30363B', axis='#687783')
SIZE = dict(category=10.5, label=10.5, value=10, title=11.5, panel=13, tick=9.5)

def one_decimal(value):
    return str(Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

def render(rows, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: int(r['baseline_rank']))
    available = {f.name for f in font_manager.fontManager.ttflist}
    cn = next(f for f in ['Noto Sans CJK SC','Source Han Sans CN','Microsoft YaHei','SimHei'] if f in available)
    latin = next((f for f in ['Arial','Helvetica','DejaVu Sans'] if f in available), cn)
    plt.rcParams.update({'font.family':[latin,cn], 'font.size':10,
        'text.color':COLOR['text'], 'axes.labelcolor':COLOR['text'],
        'xtick.color':COLOR['axis'], 'ytick.color':COLOR['text'],
        'axes.unicode_minus':False, 'pdf.fonttype':42, 'ps.fonttype':42,
        'svg.fonttype':'path', 'savefig.facecolor':'white'})
    fig = plt.figure(figsize=(9,5), facecolor='white')
    gs = fig.add_gridspec(1,2,width_ratios=[1,1.05],left=.13,right=.97,bottom=.15,top=.86,wspace=.25)
    left=fig.add_subplot(gs[0]); right=fig.add_subplot(gs[1],sharey=left)
    annotations=[]; displayed=[]
    for ax,k,panel,title in [(left,2,'a','二项模式的特征支撑份额'),(right,3,'b','三项模式的特征支撑份额')]:
        values=[float(r[f'order{k}_share'])*100 for r in rows]
        ax.barh(range(len(rows)),values,height=.58,color=COLOR['bar'],edgecolor='none',zorder=3)
        ax.set_xlim(0,30);ax.set_xticks([0,10,20,30]);ax.set_ylim(len(rows)-.45,-.55)
        for x in [10,20]:ax.axvline(x,color=COLOR['grid'],lw=.7,zorder=0)
        for i,(r,v) in enumerate(zip(rows,values)):
            label=one_decimal(v)
            annotations.append(ax.annotate(label,(v,i),xytext=(5,0),textcoords='offset points',va='center',fontsize=SIZE['value']))
            displayed.append(dict(order=k,feature=r['feature'],feature_cn=r['feature_cn'],share=float(r[f'order{k}_share']),percent=v,display_label=label))
        for edge in ['top','right','left']:ax.spines[edge].set_visible(False)
        ax.spines['bottom'].set_color('#CCD5DC');ax.spines['bottom'].set_linewidth(.65)
        ax.tick_params(axis='y',length=0,pad=9)
        ax.tick_params(axis='x',length=3,width=.65,pad=4,labelsize=SIZE['tick'])
        annotations.append(ax.text(0,1.075,panel,transform=ax.transAxes,fontweight='bold',fontsize=SIZE['panel'],va='bottom'))
        annotations.append(ax.text(.075,1.075,title,transform=ax.transAxes,fontsize=SIZE['title'],va='bottom',fontfamily=cn))
        ax.set_xlabel('特征支撑份额（%）',fontsize=SIZE['label'],labelpad=11)
    left.set_yticks(range(len(rows)),[r['feature_cn'] for r in rows],fontsize=SIZE['category'])
    right.tick_params(axis='y',labelleft=False)
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    for t in annotations:
        b=t.get_window_extent(renderer)
        if not (fig.bbox.contains(b.x0,b.y0) and fig.bbox.contains(b.x1,b.y1)):
            raise ValueError(f'Text outside canvas: {t.get_text()}')
    for i in range(len(rows)):
        if abs(left.transData.transform((0,i))[1]-right.transData.transform((0,i))[1])>1e-8:
            raise ValueError('Panel rows misaligned')
    stem='feature_support_order2_order3'
    for ext in ['png','pdf','svg']:fig.savefig(output/f'{stem}.{ext}',dpi=600,facecolor='white')
    plt.close(fig)
    with (output/'display_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(displayed[0]));w.writeheader();w.writerows(displayed)
    (output/'figure_metadata.json').write_text(json.dumps(dict(fonts=[cn,latin],bar_color=COLOR['bar'],figsize_inches=[9,5],png_dpi=600,
        normalization='Each order independently sums to 1',row_order='Original combined F1 feature ranking, shared across panels',rounding='Decimal ROUND_HALF_UP, 1 decimal; display only',geometry_checks='passed'),ensure_ascii=False,indent=2),encoding='utf-8')
