import os
"""Matplotlib scientific forest-table. Read original F3 data beside this script."""
from pathlib import Path
import csv,json,argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec,GridSpecFromSubplotSpec
from matplotlib import font_manager
from matplotlib.lines import Line2D

OUT=Path(os.environ['XINJIANG_FIGURE_DIR'])
COLOR=dict(a='#3F718D',b='#2A8A72',text='#263742',field='#71828D',secondary='#7E8C96',grid='#E7ECEF',row='#E3E8EB',section='#D5DEE3',baseline='#CCD5DA')
FIGSIZE=(11.5,7.5)
RATIOS=[50,27,15,8]

def fonts():
    names={f.name for f in font_manager.fontManager.ttflist}
    cn=next((f for f in ['Noto Sans CJK SC','Source Han Sans CN','Microsoft YaHei','PingFang SC','SimHei'] if f in names),None)
    if not cn:raise RuntimeError('A CJK sans font is required.')
    en=next(f for f in ['Arial','DejaVu Sans'] if f in names)
    return cn,en

def draw_group_header(ax,y,letter,title,color):
    ax.text(0,y,letter,fontsize=12,weight='bold',va='center',color=color)
    ax.text(.042,y,title,fontsize=11,weight='medium',va='center',color=color)

def draw_pattern(axes,y,row,color,draft):
    text,plot,number,co,lift=axes
    pairs=[line.split('：',1) for line in row['members_text'].splitlines()]
    spacing=.225 if draft else .29
    artists=[]
    for i,(field,value) in enumerate(pairs):
        yi=y+(i-(len(pairs)-1)/2)*spacing
        artists.append(text.text(0,yi,field,fontsize=9.5,color=COLOR['field'],va='center'))
        artists.append(text.text(.105,yi,value,fontsize=10.3,va='center'))
    evidence=float(row['evidence'])
    plot.hlines(y,0,evidence,color=color,lw=1.2 if draft else 1.05,zorder=3)
    plot.plot(evidence,y,'o',ms=4.8 if draft else 4.3,color=color,zorder=4)
    artists.append(number.text(.98,y,f'{evidence:.3f}',ha='right',va='center',fontsize=10))
    artists.append(co.text(.65,y,f"{row['count']}/{row['valid_n']}",ha='right',va='center',fontsize=10))
    artists.append(lift.text(.98,y,f"{float(row['group_lift']):.2f}",ha='right',va='center',fontsize=10))
    return artists

def main():
    p=argparse.ArgumentParser();p.add_argument('--draft',action='store_true');args=p.parse_args()
    cn,en=fonts()
    plt.rcParams.update({'font.family':[en,cn],'text.color':COLOR['text'],'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'path'})
    with (OUT/'plot_data.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    assert len(rows)==8
    fig=plt.figure(figsize=FIGSIZE,facecolor='white')
    outer=GridSpec(1,4,figure=fig,width_ratios=RATIOS,left=.04,right=.975,bottom=.035,top=.895,wspace=.075)
    inside=GridSpecFromSubplotSpec(1,2,subplot_spec=outer[1],width_ratios=[.74,.26],wspace=.10)
    axes=[fig.add_subplot(outer[0]),fig.add_subplot(inside[0]),fig.add_subplot(inside[1]),fig.add_subplot(outer[2]),fig.add_subplot(outer[3])]
    text,plot,number,co,lift=axes
    for ax in axes:
        ax.set_ylim(9.25,-.5);ax.set_xlim(0,1);ax.set_axis_off()
    plot.set_xlim(0,.45)
    for x in [0,.2,.4]:
        plot.vlines(x,.72,9.0,color=COLOR['baseline'] if x==0 else COLOR['grid'],lw=.6 if x==0 else .45,zorder=0)
        plot.text(x,-.40,f'{x:.1f}',ha='center',va='center',fontsize=8.8,color=COLOR['secondary'])
    centers=[1.08,2.08,3.08,4.08,5.65,6.65,7.65,8.65]
    draw_group_header(text,.24,'a','全库高证据组合',COLOR['a'])
    draw_group_header(text,4.85,'b','不含 Region 字段的组合',COLOR['b'])
    artists=[]
    for i,(y,row) in enumerate(zip(centers,rows)):
        artists.extend(draw_pattern(axes,y,row,COLOR['a'] if i<4 else COLOR['b'],args.draft))
    # One header per quantity; Evidence heading covers plot and numeric subcolumn.
    def heading(x,label,ha='left'):fig.text(x,.950,label,ha=ha,va='center',fontsize=10,weight='medium')
    heading(text.get_position().x0,'共现模式及属性组成')
    heading((plot.get_position().x0+number.get_position().x1)/2,'证据分数','center')
    heading((co.get_position().x0+co.get_position().x1)/2,'共现数/共同观测数','center')
    heading(lift.get_position().x1,'Lift','right')
    def rule(y,color,lw):
        fy=fig.transFigure.inverted().transform(text.transData.transform((0,y)))[1]
        fig.add_artist(Line2D([.04,.975],[fy,fy],transform=fig.transFigure,color=color,lw=lw,zorder=0))
    for y in [1.58,2.58,3.58,6.15,7.15,8.15]:rule(y,COLOR['row'],.40 if args.draft else .30)
    rule(4.55,COLOR['section'],.65)
    rule(9.12,COLOR['row'],.4)
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    for y in centers:
        coords=[ax.transData.transform((0,y))[1] for ax in axes]
        assert max(coords)-min(coords)<1e-8
    for t in artists:
        b=t.get_window_extent(renderer);a=t.axes.get_window_extent(renderer)
        assert b.x0>=a.x0-1 and b.x1<=a.x1+1,t.get_text()
    assert not any('P000' in t.get_text() or '项/' in t.get_text() for ax in axes for t in ax.texts)
    stem='draft_v1' if args.draft else 'high_order_pattern_forest_table'
    for ext in (['png'] if args.draft else ['png','pdf','svg']):fig.savefig(OUT/f'{stem}.{ext}',dpi=180 if args.draft else 600,facecolor='white')
    if not args.draft:
        (OUT/'figure_metadata.json').write_text(json.dumps({'figure_inches':FIGSIZE,'fonts':[cn,en],'area_ratios':RATIOS,'evidence_axis':[0,.45],'evidence_precision':3,'lift_precision':2,'alignment':'all row centers passed','text_bounds':'passed','denominator':'pattern-specific jointly observed name groups','data':'unmodified experimental F3.csv; IDs retained only in provenance CSV, excluded from figure'},ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig)
    print(stem,cn,en)
if __name__=='__main__':main()
