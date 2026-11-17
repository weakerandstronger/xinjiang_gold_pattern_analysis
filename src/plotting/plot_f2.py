import os
"""Reproduce with Python + Matplotlib; reads the supplied, unmodified plot_data.csv."""
from pathlib import Path
import csv,json,argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib import font_manager

OUT=Path(os.environ['XINJIANG_FIGURE_DIR'])
C=dict(bar='#477A96',primary='#263746',secondary='#7E8C96',tertiary='#8D99A2',grid='#E7ECEF',separator='#DCE4E8',baseline='#CCD5DA')
SIZE=dict(title=11.5,panel=12,label=9.5,value=9.5,count=9,summary=9.2,top5=8.4,col=8,tick=8.5)
FIGSIZE=(11,7)
RATIOS=(.34,.48,.18)

def fonts():
    available={f.name for f in font_manager.fontManager.ttflist}
    cn=next((f for f in ['Noto Sans CJK SC','Source Han Sans CN','Microsoft YaHei','PingFang SC','SimHei'] if f in available),None)
    if not cn:raise RuntimeError('Install a CJK sans font before running.')
    en=next(f for f in ['Arial','DejaVu Sans'] if f in available)
    return cn,en

def create_panel(fig,subspec,panel_letter,feature_name,global_support,top5_share,labels,shares,counts,cn,en,show_xticklabels=False,draft=False):
    nested=GridSpecFromSubplotSpec(2,3,subplot_spec=subspec,width_ratios=RATIOS,height_ratios=[.32,1],hspace=.06,wspace=.06)
    head=fig.add_subplot(nested[0,:]);head.set_axis_off()
    head.text(0,.77,panel_letter,weight='bold',fontsize=SIZE['panel'],va='center',transform=head.transAxes)
    head.text(.047,.77,feature_name,fontsize=SIZE['title'],weight='medium',fontfamily=cn,va='center',transform=head.transAxes)
    # Fixed-size indicator; its area does not encode support.
    head.scatter([.68],[.79],s=23,color=C['bar'],transform=head.transAxes,clip_on=False)
    head.text(.715,.79,'全局支撑',fontsize=SIZE['summary'],color=C['secondary'],va='center',transform=head.transAxes)
    head.text(1,.79,f'{global_support:.1f}%',fontsize=SIZE['summary'],ha='right',va='center',transform=head.transAxes)
    head.text(1,.27,f'Top-5累计  {top5_share:.1f}%',fontsize=SIZE['top5'],color=C['secondary'],ha='right',va='center',transform=head.transAxes)
    head.plot([0,1],[-.025,-.025],color=C['separator'],lw=.55,transform=head.transAxes,clip_on=False)
    label_ax=fig.add_subplot(nested[1,0]);bar_ax=fig.add_subplot(nested[1,1]);num_ax=fig.add_subplot(nested[1,2])
    for ax in [label_ax,bar_ax,num_ax]:ax.set_ylim(4.65,-.9);ax.set_yticks([])
    label_ax.set_axis_off();num_ax.set_axis_off()
    label_ax.set_xlim(0,1);num_ax.set_xlim(0,1)
    texts=[]
    for i,(label,share,count) in enumerate(zip(labels,shares,counts)):
        texts.append(label_ax.text(.98,i,label,ha='right',va='center',fontsize=SIZE['label']))
        texts.append(num_ax.text(.55,i,f'{share:.1f}',ha='right',va='center',fontsize=SIZE['value']))
        texts.append(num_ax.text(.98,i,str(count),ha='right',va='center',fontsize=SIZE['count'],color=C['secondary']))
    num_ax.text(.55,-.70,'份额/%',ha='right',va='center',fontsize=SIZE['col'],color=C['tertiary'])
    num_ax.text(.98,-.70,'n',ha='right',va='center',fontsize=SIZE['col'],color=C['tertiary'])
    bar_ax.set_xlim(0,35);bar_ax.set_xticks([0,10,20,30])
    for x in [10,20,30]:bar_ax.vlines(x,-.35,4.35,color=C['grid'],lw=.45,zorder=0)
    bar_ax.vlines(0,-.35,4.35,color=C['baseline'],lw=.65,zorder=1)
    bar_ax.barh(range(5),shares,height=.56 if draft else .52,color=C['bar'],edgecolor='none',zorder=3)
    for spine in bar_ax.spines.values():spine.set_visible(False)
    bar_ax.tick_params(axis='x',labelbottom=show_xticklabels,length=2.5 if show_xticklabels else 0,width=.5,color=C['baseline'],labelcolor=C['secondary'],labelsize=SIZE['tick'],pad=3)
    if show_xticklabels:
        bar_ax.spines['bottom'].set_visible(True);bar_ax.spines['bottom'].set_color(C['baseline']);bar_ax.spines['bottom'].set_linewidth(.5)
    return (label_ax,bar_ax,num_ax,head,texts)

def main():
    args=argparse.ArgumentParser();args.add_argument('--draft',action='store_true');opt=args.parse_args()
    cn,en=fonts()
    plt.rcParams.update({'font.family':[en,cn],'text.color':C['primary'],'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'path'})
    with (OUT/'plot_data.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    assert len(rows)==30
    fig=plt.figure(figsize=FIGSIZE,facecolor='white')
    outer=GridSpec(3,2,figure=fig,left=.035,right=.978,top=.965,bottom=.093,wspace=.115,hspace=.205 if opt.draft else .17)
    panels=[]
    for k in range(6):
        data=[r for r in rows if int(r['panel'])==k+1]
        assert len(data)==5
        s=[float(r['within_feature_share'])*100 for r in data]
        top=float(data[0]['displayed_within_share'])*100
        assert abs(sum(s)-top)<1e-8
        panels.append(create_panel(fig,outer[k//2,k%2],chr(97+k),data[0]['feature_cn'],float(data[0]['feature_global_share'])*100,top,[r['value_raw'] for r in data],s,[int(r['count']) for r in data],cn,en,k>=4,opt.draft))
    fig.supxlabel('特征内部份额（%）',y=.022,fontsize=10.5)
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    starts=[p[1].get_position().x0 for p in panels];widths=[p[1].get_position().width for p in panels]
    assert max(widths)-min(widths)<1e-12
    assert all(abs(starts[k]-starts[k%2])<1e-12 for k in range(6))
    for label_ax,bar_ax,num_ax,head,texts in panels:
        for i in range(5):
            assert abs(label_ax.transData.transform((0,i))[1]-bar_ax.transData.transform((0,i))[1])<1e-8
            assert abs(num_ax.transData.transform((0,i))[1]-bar_ax.transData.transform((0,i))[1])<1e-8
        for t in texts[:]:
            box=t.get_window_extent(renderer);axbox=t.axes.get_window_extent(renderer)
            assert box.x0>=axbox.x0-1 and box.x1<=axbox.x1+1,(t.get_text(),box,axbox)
    stem='draft_v1' if opt.draft else 'feature_internal_support_v3'
    for ext in (['png'] if opt.draft else ['png','pdf','svg']):fig.savefig(OUT/f'{stem}.{ext}',dpi=180 if opt.draft else 600,facecolor='white')
    if not opt.draft:
        (OUT/'figure_metadata.json').write_text(json.dumps({'figsize_inches':FIGSIZE,'fonts':{'chinese':cn,'latin':en},'column_ratios':RATIOS,'bar_color':C['bar'],'bar_axis_widths_fraction':widths,'bar_axis_left_fraction':starts,'geometry_checks':'passed: equal widths, same-column left edges, aligned label/bar/numeric rows, no label overflow','data':'unmodified experimental F2.csv; original unrounded shares; display precision only'},ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig)
    print(stem,cn,en)
if __name__=='__main__':main()
