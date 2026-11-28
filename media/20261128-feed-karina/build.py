"""더피드 숏츠형 릴스 — 에스파 6주년 팬미팅 산타복 카리나 (TTS 없음)
원본: 인스타 @bythepulse 게시물 DgSZifJo3v3 (영상 5개 묶음, 영상에 소리 없음)
      cardnews drafts/video.json 으로 받음 → video/item3~7.mp4 (880x1100, item7 은 560x700 저화질이라 안 씀)
소리: 원본이 무음이라 브금 Kevin MacLeod 'Jingle Bells'(incompetech, CC BY 4.0 → 캡션에 표기) 65초부터.
화면: 원본 자막 없음 → 인물 쪽으로 꽉 채워 자름(검정 띠 없음, 흐림 없음). 대사가 없어 해설 자막만.
"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
V = os.path.join(HERE, 'video')
TITLE = ["에스파 팬미팅 드레스코드", "[산타 카리나] 실물 ㄷㄷ"]
SRC_LABEL = "영상: 인스타그램 @bythepulse"
BGM, BGM_START = os.path.join(V, 'jingle_bells.mp3'), 65.0

SEG = [
    ('item3', 0.0, 4.0, "에스파 데뷔 6주년 팬미팅"),
    ('item3', 6.0, 9.5, "이날 드레스코드는 [산타]"),
    ('item4', 0.5, 4.5, "멤버 전원이\n[산타복] 맞춰 입고"),
    ('item5', 0.3, 4.3, "[징글벨 락]·[산타 베이비]\n무대까지"),
    ('item6', 0.0, 4.0, "공연 끝나자마자\n직캠이 쏟아졌는데"),
    ('item5', 6.0, 10.0, "반응은 [호평 일색]"),
    ('item6', 7.0, 11.0, "올해 산타는\n[카리나]로 정함"),
]


def sub_png(text, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(fl.F, 80); fl.W = W
    ls = text.split('\n')
    ys = [1471] if len(ls) == 1 else [1421, 1521]
    for t, y in zip(ls, ys):
        fl.line(d, t, y, f, stroke=9)
    yc = sum(ys) / len(ys) - 28
    lay = lay.transform((W, H), Image.AFFINE, (1, sr.SHEAR, -sr.SHEAR * yc, 0, 1, 0), Image.BICUBIC)
    lay.save(path)


def src_png(path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(fl.FM, 26)
    tw = d.textlength(SRC_LABEL, font=f)
    d.text((W - 28 - tw, sr.BAND + 22), SRC_LABEL, font=f, fill=(255, 255, 255, 200), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    lay.save(path)


def build():
    tmp = tempfile.mkdtemp()
    vh = H - sr.BAND
    parts = []
    for i, (k, s, e, _) in enumerate(SEG):
        p = os.path.join(tmp, f'p{i:02d}.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s}', '-t', f'{e - s:.2f}', '-i', os.path.join(V, f'{k}.mp4'),
                        '-vf', f'scale=-2:{vh}:flags=lanczos,crop={W}:{vh}:(iw-{W})/2:0,fps=30,setsar=1',
                        '-an', '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast', p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, 'l.txt'); open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    cat = os.path.join(tmp, 'cat.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', cat], check=True)
    ov = os.path.join(tmp, 'ov.png'); sr.overlay(TITLE, ov); src_png(os.path.join(tmp, 'src.png'))
    t, times = 0.0, []
    for i, (_, s, e, txt) in enumerate(SEG):
        sub_png(txt, os.path.join(tmp, f's{i:02d}.png')); times.append((t, t + e - s)); t += e - s
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SEG))], [])
    ins += ['-ss', f'{BGM_START}', '-t', f'{t:.2f}', '-i', BGM]
    ai = len(SEG) + 3
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30[bg];[bg][0:v]overlay=0:{sr.BAND}:shortest=1[a1];'
          f'[a1][1:v]overlay=0:0[a2];[a2][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e) in enumerate(times):
        fc += f";[{last}][{i + 3}:v]overlay=0:0:enable='gte(t,{s:.2f})*lt(t,{e:.2f})'[c{i}]"
        last = f'c{i}'
    fc += (f';[{last}]format=yuv420p[o];[{ai}:a]afade=t=in:d=0.3,afade=t=out:st={t - 1.2:.2f}:d=1.2,'
           f'loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[au]')
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', cat, *ins, '-filter_complex', fc, '-map', '[o]', '-map', '[au]',
                    '-c:a', 'aac', '-b:a', '160k', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast',
                    '-movflags', '+faststart', '-t', f'{t:.2f}', out], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out, t


if __name__ == '__main__':
    print(build())
