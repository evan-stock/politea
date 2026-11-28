"""더피드 숏츠형 릴스 — 현우진 'bunch of ㅆㅅㄲ' (TTS 없음, 원본 소리 그대로)
원본: 유튜브 theMEGASTUDY '[메가스터디] 수학 현우진쌤 - 2028 수능 대비 현우진 커리큘럼 가이드'(oX1KPPua1XM)
      맥북 도우미 구간 받기: hw1 3:12~3:40 / hw2 4:02~4:22 (hw3 24:50~25:10 은 '남조선' 표현이라 안 씀)
화면: 원본에 자막 없음 → 인물 쪽으로 꽉 채워 자름(검정 띠 없음, 흐림 없음). 대사 자막만.
흐름: 어떤 필드든 bunch of ㅆㅅㄲ → ㅂㅅ 피하는 게 일 → 나는 잘 피했다 → 피하는 법: 안 만나면 돼 (22초 안팎)
"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
V = os.path.join(HERE, 'video')
TITLE = ["수학 일타 현우진이 말하는", "[ㅂㅅ 피하는 법] ㅋㅋ"]
XR = 0.84                    # 가로 자르기 위치(0=왼쪽, 1=오른쪽) — 인물이 오른쪽에 섬
SRC_LABEL = "영상: 유튜브 메가스터디"

SEG = [
    ('hw1', 9.50, 12.00, "어떤 필드든 마찬가지야"),
    ('hw1', 12.00, 15.00, "아 이게 [bunch of ㅆㅅㄲ]들이\n너무 많아"),
    ('hw1', 15.00, 17.50, "in this 좀만한 [country]에"),
    ('hw1', 17.50, 19.80, "이게 [ㅂㅅ 피하는 게 일]이야"),
    ('hw1', 20.10, 24.50, "그 이제 나는\nㅂㅅ을 [잘 피했죠]"),
    ('hw1', 24.50, 26.10, "물론 못 피한 적도 있어"),
    ('hw2', 11.20, 15.30, "그들을 피하는\n[가장 확실한 방법]은"),
    ('hw2', 15.30, 18.30, "[안 만나면 돼]"),
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
                        '-vf', f'scale=-2:{vh}:flags=lanczos,crop={W}:{vh}:(iw-{W})*{XR}:0,fps=30,setsar=1',
                        '-af', 'aresample=48000', '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast',
                        '-c:a', 'aac', '-b:a', '192k', p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, 'l.txt'); open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    cat = os.path.join(tmp, 'cat.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', cat], check=True)
    ov = os.path.join(tmp, 'ov.png'); sr.overlay(TITLE, ov); src_png(os.path.join(tmp, 'src.png'))
    t, times = 0.0, []
    for i, (_, s, e, txt) in enumerate(SEG):
        sub_png(txt, os.path.join(tmp, f's{i:02d}.png')); times.append((t, t + e - s)); t += e - s
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SEG))], [])
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30[bg];[bg][0:v]overlay=0:{sr.BAND}:shortest=1[a1];'
          f'[a1][1:v]overlay=0:0[a2];[a2][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e) in enumerate(times):
        fc += f";[{last}][{i + 3}:v]overlay=0:0:enable='gte(t,{s:.2f})*lt(t,{e:.2f})'[c{i}]"
        last = f'c{i}'
    fc += f';[{last}]format=yuv420p[o];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[au]'
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', cat, *ins, '-filter_complex', fc, '-map', '[o]', '-map', '[au]',
                    '-c:a', 'aac', '-b:a', '160k', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast',
                    '-movflags', '+faststart', out], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{times[1][0] + 1.0:.2f}', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out, t


if __name__ == '__main__':
    print(build())
