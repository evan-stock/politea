"""더피드(@thefeed.kr) 릴스 공용 함수: 글꼴 경로, [대괄호] 빨강 강조 줄, 로고(stacked_logo = 프로필과 같은 THE/FEED/빨간 점)."""
import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
from PIL import Image, ImageDraw, ImageFont
F=os.path.join(ROOT,'assets/fonts/')+'Pretendard-Black.otf'; FM=os.path.join(ROOT,'assets/fonts/')+'Pretendard-Bold.otf'; ANTON=''+os.path.join(ROOT,'assets/fonts/Anton-Regular.ttf')+''
RED=(255,59,48); W,H=1080,1920
def cover(im,w,h,fy=.45):
    r=max(w/im.width,h/im.height); im=im.resize((int(im.width*r),int(im.height*r)),Image.LANCZOS)
    x=(im.width-w)//2; y=int((im.height-h)*fy); return im.crop((x,y,x+w,y+h))
def runs(line):
    out=[];cur='';on=False
    for ch in line:
        if ch in '[]':
            if cur: out.append((cur,on))
            cur='';on=(ch=='[');continue
        cur+=ch
    if cur: out.append((cur,on))
    return out
def line(d,t,y,f,fg=(255,255,255),hl=RED,stroke=0,sf=(0,0,0),x0=None):
    rs=runs(t); w=sum(d.textlength(s,font=f) for s,_ in rs); x=(W-w)/2 if x0 is None else x0
    for s,on in rs: d.text((x,y),s,font=f,fill=hl if on else fg,anchor='ls',stroke_width=stroke,stroke_fill=sf); x+=d.textlength(s,font=f)
def logo(d,y,color=(255,255,255),size=40,cx=W/2):
    fa=ImageFont.truetype(ANTON,size); sp=size*.2
    lw=sum(d.textlength(c,font=fa) for c in 'THE FEED')+sp*7; x=cx-(lw+size*.6)/2
    for c in 'THE FEED': d.text((x,y),c,font=fa,fill=color,anchor='ls'); x+=d.textlength(c,font=fa)+sp
    r=size*.17; d.ellipse((x+r,y-2*r,x+3*r,y),fill=RED)

def stacked_logo(d, left, top, feed=64, color=(255,255,255), center=False):
    """프로필과 같은 모양: 작은 THE(자간 넓게) / 큰 FEED / 아래 빨간 점. 반환: 아래 끝 y"""
    A=''+os.path.join(ROOT,'assets/fonts/Anton-Regular.ttf')+''
    f2=ImageFont.truetype(A,feed); f1=ImageFont.truetype(A,int(feed*.5))
    sp2=feed*.022; fw=sum(d.textlength(c,font=f2) for c in 'FEED')+sp2*3
    tw0=sum(d.textlength(c,font=f1) for c in 'THE'); sp1=(fw*.62-tw0)/2
    tw=tw0+sp1*2
    x0=left-(fw/2 if center else 0)
    b1=d.textbbox((0,0),'THE',font=f1); b2=d.textbbox((0,0),'FEED',font=f2)
    y=top-b1[1]; x=x0+(fw-tw)/2
    for c in 'THE': d.text((x,y),c,font=f1,fill=color); x+=d.textlength(c,font=f1)+sp1
    y=top+(b1[3]-b1[1])+feed*.09-b2[1]; x=x0
    for c in 'FEED': d.text((x,y),c,font=f2,fill=color); x+=d.textlength(c,font=f2)+sp2
    yb=top+(b1[3]-b1[1])+feed*.09+(b2[3]-b2[1])+feed*.17; r=feed*.1
    d.ellipse((x0+fw/2-r,yb,x0+fw/2+r,yb+2*r),fill=RED)
    return yb+2*r
