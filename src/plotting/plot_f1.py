import os
"""Run with Python + Matplotlib; outputs are saved beside this script."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import csv, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

with (Path(os.environ['XINJIANG_FIGURE_DIR'])/'plot_data.csv').open(encoding='utf-8-sig') as f:
    ROWS=list(csv.DictReader(f))
DATA=[(x['feature_cn'],float(x['share'])*100,int(x['observed_n'])) for x in ROWS]
TOTAL=int(ROWS[0]['total_n'])
COLORS = dict(bar='#3F6F8E', dot='#819AA7', track='#DEE5E9', grid='#E9EDF0', text='#30363B', axis='#687783')
SIZES = dict(category=10.5, label=10.5, value=10, title=11.5, panel=13, tick=9.5)
FIGSIZE = (9, 5)
OUT = Path(os.environ['XINJIANG_FIGURE_DIR'])

def one_decimal(value):
    # Decimal half-up: avoid binary-float surprises at 7.15 and 6.85.
    return str(Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

def select_fonts():
    available = {f.name for f in font_manager.fontManager.ttflist}
    cn = next((f for f in ['Noto Sans CJK SC','Source Han Sans CN','Microsoft YaHei','SimHei'] if f in available), None)
    if cn is None:
        raise RuntimeError('Install a CJK font: Noto Sans CJK SC / Source Han Sans CN / Microsoft YaHei / SimHei.')
    latin = next((f for f in ['Arial','Helvetica','DejaVu Sans'] if f in available), cn)
    return cn, latin

def main():
    cn, latin = select_fonts()
    plt.rcParams.update({'font.family':[latin,cn], 'font.size':10,
        'text.color':COLORS['text'], 'axes.labelcolor':COLORS['text'],
        'xtick.color':COLORS['axis'], 'ytick.color':COLORS['text'],
        'axes.unicode_minus':False, 'pdf.fonttype':42, 'ps.fonttype':42,
        'svg.fonttype':'path', 'savefig.facecolor':'white'})
    fig = plt.figure(figsize=FIGSIZE, facecolor='white')
    gs = fig.add_gridspec(1,2,width_ratios=[1,1.05],left=.13,right=.97,bottom=.15,top=.86,wspace=.25)
    left = fig.add_subplot(gs[0]); right = fig.add_subplot(gs[1],sharey=left)
    y = list(range(len(DATA)))
    left.barh(y,[r[1] for r in DATA],height=.58,color=COLORS['bar'],edgecolor='none',zorder=3)
    left.set_xlim(0,30); left.set_xticks([0,10,20,30])
    left.set_yticks(y,[r[0] for r in DATA],fontsize=SIZES['category'])
    left.set_ylim(9.55,-.55)
    for x in [10,20]:left.axvline(x,color=COLORS['grid'],lw=.7,zorder=0)
    annotations=[]
    for i,(_,support,observed) in enumerate(DATA):
        annotations.append(left.annotate(one_decimal(support),(support,i),xytext=(5,0),textcoords='offset points',va='center',fontsize=SIZES['value']))
        coverage=observed/TOTAL*100
        right.plot([0,100],[i,i],color=COLORS['track'],lw=1.5,solid_capstyle='round',zorder=1)
        right.scatter([coverage],[i],s=48,color=COLORS['dot'],edgecolor='white',linewidth=.55,zorder=3,clip_on=False)
        # Place only near-boundary labels to the left; no extra data-axis padding needed.
        near_edge=coverage>90
        annotations.append(right.annotate(one_decimal(coverage),(coverage,i),xytext=(-7 if near_edge else 7,0),textcoords='offset points',ha='right' if near_edge else 'left',va='center',fontsize=SIZES['value'],zorder=4,bbox=dict(facecolor='white',edgecolor='none',pad=.6)))
    right.set_xlim(0,105);right.set_xticks([0,50,100])
    right.axvline(50,color=COLORS['grid'],lw=.7,zorder=0)
    right.tick_params(axis='y',labelleft=False)
    right.spines['bottom'].set_bounds(0,100)
    for ax,panel,title in [(left,'a','特征支撑份额'),(right,'b','特征观测覆盖率')]:
        for name in ['top','right','left']:ax.spines[name].set_visible(False)
        ax.spines['bottom'].set_color('#CCD5DC');ax.spines['bottom'].set_linewidth(.65)
        ax.tick_params(axis='y',length=0,pad=9)
        ax.tick_params(axis='x',length=3,width=.65,pad=4,labelsize=SIZES['tick'])
        ax.text(0,1.075,panel,transform=ax.transAxes,fontweight='bold',fontsize=SIZES['panel'],va='bottom')
        ax.text(.065,1.075,title,transform=ax.transAxes,fontsize=SIZES['title'],va='bottom',fontfamily=cn)
        ax.set_xlabel(title+'（%）',fontsize=SIZES['label'],labelpad=11)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    assert all(abs(left.transData.transform((0,i))[1]-right.transData.transform((0,i))[1])<1e-8 for i in y)
    assert all(fig.bbox.contains(t.get_window_extent(renderer).x0,t.get_window_extent(renderer).y0) and fig.bbox.contains(t.get_window_extent(renderer).x1,t.get_window_extent(renderer).y1) for t in annotations)
    for ext in ['png','pdf','svg']:
        fig.savefig(OUT/f'feature_support_coverage.{ext}',dpi=600,facecolor='white')
    with (OUT/'display_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['feature','support_percent','observed','total','coverage_percent','support_label','coverage_label'])
        for name,s,n in DATA:w.writerow([name,s,n,TOTAL,n/TOTAL*100,one_decimal(s),one_decimal(n/TOTAL*100)])
    (OUT/'figure_metadata.json').write_text(json.dumps({'fonts':{'chinese':cn,'latin':latin},'figsize_inches':FIGSIZE,'png_dpi':600,'png_pixels':[5400,3000],'row_alignment':'passed','numeric_labels_inside_canvas':'passed','rounding':'Decimal ROUND_HALF_UP; display only, source values unchanged','total':TOTAL},ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig)
    print(f'Completed: {OUT}; fonts: {cn}, {latin}')

if __name__=='__main__':main()
