"""더피드 세로형 릴스 예시(2026-11-15 유조선). 세로형 틀: 영상 9:16 꽉 / 위쪽 왼쪽 장면 자막(작은 줄 y=470, 굵은 줄 y=550) / 아래 왼쪽 제목 3줄(기준선 1435·1555·1675, 마지막 줄 빨강) / 로고 하단 중앙(THE/FEED, y=1715). S(장면)·TITLE만 바꿔 복사해 쓴다. 저장소 루트에서 python3 scripts/feed_reel/vertical_example.py"""
import subprocess, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from feedlib import runs, F, FM, RED, W, H, logo, stacked_logo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC='/home/claude/evan-stock/cardnews/media/'
VP=SRC+'20261115-xpair/video/v2.mp4'   # 부두 (@WingsSoon)
VW=SRC+'20261115-nola2/video/v1.mp4'   # 물속 승객 (@I_amMukhtar)
R='/home/claude/feed/nolaV'; os.makedirs(R,exist_ok=True)
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','media','20261115-feed-nola'); os.makedirs(OUT,exist_ok=True)
X=70
def lline(d,t,y,f,fg=(255,255,255)):
    x=X
    for s,on in runs(t): d.text((x,y),s,font=f,fill=RED if on else fg,anchor='ls'); x+=d.textlength(s,font=f)
def with_shadow(draw_fn,blur=10,alpha=.7):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); lay=Image.new('RGBA',(W,H),(0,0,0,0)); draw_fn(ImageDraw.Draw(lay))
    a=lay.getchannel('A').point(lambda v:int(v*alpha)).filter(ImageFilter.GaussianBlur(blur))
    sh=Image.new('RGBA',(W,H),(0,0,0,255)); sh.putalpha(a); im.alpha_composite(sh); im.alpha_composite(lay); return im
TITLE=['유람선 뒤집혀','강물에 빠진 승객이','[직접 찍은 영상]']
def title_layer():
    g=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(g)
    for y in range(0,420): d.line([(0,y),(W,y)],fill=(0,0,0,int(90*max(0,1-y/420))))
    for y in range(1050,H): d.line([(0,y),(W,y)],fill=(0,0,0,int(185*min(1,(y-1050)/450))))
    ft=ImageFont.truetype(F,100)
    def dr(d):
        for i,l in enumerate(TITLE): lline(d,l,1435+i*120,ft)
        stacked_logo(d,W/2,1715,feed=50,center=True)
    g.alpha_composite(with_shadow(dr)); return g
def cap_layer(a,b):
    g=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(g)
    for y in range(0,680): d.line([(0,y),(W,y)],fill=(0,0,0,int(160*max(0,1-y/680))))
    f1=ImageFont.truetype(FM,38); f2=ImageFont.truetype(F,58)
    def dr(d):
        if a: lline(d,a,470,f1,fg=(235,235,235))
        lline(d,b,550,f2)
    g.alpha_composite(with_shadow(dr,blur=8,alpha=.8)); return g
title_layer().save(f'{R}/title.png')
S=[(VP,3.5,5.5,[(0,5.5,'11월 13일 · 미국 뉴올리언스 항구','유조선이 정박한 [유람선을 들이받음]')]),
   (VW,0.0,4.3,[(0,4.3,'강물에 빠진 승객 바로 옆까지','[밀고 들어온 유조선]')]),
   (VW,4.3,8.2,[(0,4.0,'승객 129명 태운 유람선은','[옆으로 뒤집힌 채]'),(4.0,8.2,'카메라를 돌리자 바로 뒤에','길이 160m [유조선]')]),
   (VP,46.5,6.5,[(0,3.2,'구조를 기다리는 승객들','[32명] 병원 이송'),(3.2,6.5,'위독한 사람 없이','탑승자 [전원 구조]')])]
segs=[];ci=0
for k,(src,ss,dur,caps) in enumerate(S):
    inp=['-ss',str(ss),'-t',str(dur),'-i',src,'-i',f'{R}/title.png']
    fc="[0:v]setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[b0];[b0][1:v]overlay[b1]";last='b1'
    for j,(t0,t1,a,b) in enumerate(caps):
        cap_layer(a,b).save(f'{R}/cap{ci}.png'); inp+=['-i',f'{R}/cap{ci}.png']
        fc+=f";[{last}][{2+j}:v]overlay=enable='between(t,{t0},{t1-0.001})'[c{j}]";last=f'c{j}';ci+=1
    out=f'{R}/s{k}.mp4'
    subprocess.run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',fc+f";[{last}]fps=30[vo];[0:a]asetpts=PTS-STARTPTS[ao]",'-map','[vo]','-map','[ao]','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-ar','44100','-ac','2','-b:a','160k',out],check=True)
    segs.append(out)
open(f'{R}/list.txt','w').write(''.join(f"file '{s}'\n" for s in segs))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',f'{R}/list.txt','-af','loudnorm=I=-16:TP=-1.5','-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',f'{OUT}/reel.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-ss','10.3','-i',VW,'-frames:v','1',f'{R}/cbg.png'],check=True)
bg=Image.open(f'{R}/cbg.png').convert('RGB'); r=max(W/bg.width,H/bg.height); bg=bg.resize((int(bg.width*r),int(bg.height*r)),Image.LANCZOS)
bg=bg.crop(((bg.width-W)//2,0,(bg.width-W)//2+W,H)).convert('RGBA')
Image.alpha_composite(bg,Image.open(f'{R}/title.png')).convert('RGB').save(f'{OUT}/reel_cover.jpg',quality=93)
ims=[]
for t in (2,7,11,16,21,23.5):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',f'{OUT}/reel.mp4','-frames:v','1','-vf','scale=360:-1',f'{R}/chk.jpg'],check=True); ims.append(Image.open(f'{R}/chk.jpg').copy())
s=Image.new('RGB',(360*6,640));[s.paste(im,(i*360,0)) for i,im in enumerate(ims)]; s.save(f'{R}/sheet.jpg')
print('done')
