"""더피드 숏츠형 릴스 — 미국 '더 데일리 쇼'(11.10) 젠슨 황 풍자: "용서 못 할 짓, 근데 다 용서" → 세계 경제는 젠슨 황 거시기에 달렸다.
TTS 없음, 원본 소리. 틀: media/20261123-feed-runner/build.py(가로 영상 위아래 검정, 흐림 없음).
원본: cardnews media/20261124-dailyshow/video/v2.mp4(조시 존슨 코너 전체, 재업로드본). 위 워터마크·아래 영어 자막 띠는 잘라냄(crop y 34~905).
대사: cardnews 받아쓰기(v2.srt, words.json) + 게시글 대사 전문 대조.
실행: python3 media/20261124-feed-dailyshow/build.py [cardnews 저장소 경로]"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

CN = sys.argv[1] if len(sys.argv) > 1 else '/home/user/cardnews'
W, H = 1080, 1920
SRC = f'{CN}/media/20261124-dailyshow/video/v2.mp4'
T0, T1 = 31.4, 74.3                 # 원본에서 쓸 구간
CROP = (240, 34, 1440, 871)         # x, y, w, h
SH = round(W * CROP[3] / CROP[2] / 2) * 2   # ≈ 654
SY = 640
TITLE = ["세계 경제의 진짜 핵심", "[젠슨 황 거시기]였다 ㅋㅋ"]
SRC_LABEL = "영상: 더 데일리 쇼(코미디센트럴)"
S = [  # (원본 시작초, 자막)
    (31.58, "젠슨은 어떤 대가를\n치를까요?"),
    (36.06, "아뇨, 그냥\n[넘어갈] 거예요"),
    (40.10, "방금 우리 모두\n위험하다면서요?"),
    (43.88, "네, 100%요"),
    (45.20, "용서받을 수 없는\n짓이죠"),
    (46.96, "그리고 우린\n[다 용서할 거예요]"),
    (50.06, "왜요? 대가는\n치러야죠"),
    (53.32, "제가 쉽게\n설명해 드릴게요"),
    (55.90, "세계 경제는\n[AI 거품]에 달렸고"),
    (58.94, "AI 거품은\n[엔비디아 칩]에 달렸고"),
    (62.16, "엔비디아는\n[젠슨 황]에게 달렸고"),
    (65.22, "젠슨 황은\n[그의 거시기]에 달렸죠"),
    (70.28, "정리하면 세계 경제는\n[이 거시기]에 달렸어요"),
]
SUB = [(s - T0, (S[i + 1][0] if i + 1 < len(S) else T1) - T0, t) for i, (s, t) in enumerate(S)]


def src_png(path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(fl.FM, 26)
    tw = d.textlength(SRC_LABEL, font=f)
    d.text((W - 28 - tw, SY - 40), SRC_LABEL, font=f, fill=(255, 255, 255, 200), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    lay.save(path)


def sub_png(text, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(fl.F, 76); fl.W = W
    ls = text.split('\n')
    ys = [1430] if len(ls) == 1 else [1395, 1495]
    for t, y in zip(ls, ys):
        fl.line(d, t, y, f, stroke=9)
    yc = sum(ys) / len(ys) - 28
    lay = lay.transform((W, H), Image.AFFINE, (1, sr.SHEAR, -sr.SHEAR * yc, 0, 1, 0), Image.BICUBIC)
    lay.save(path)


def build(src=SRC):
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, 'ov.png'); sr.overlay(TITLE, ov, size=76); src_png(os.path.join(tmp, 'src.png'))
    for i, (_, _, t) in enumerate(SUB):
        sub_png(t, os.path.join(tmp, f's{i:02d}.png'))
    x, y, w, h = CROP; dur = T1 - T0
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SUB))], [])
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30:d={dur:.2f}[bg];'
          f'[0:v]crop={w}:{h}:{x}:{y},scale={W}:{SH}:flags=lanczos,setpts=PTS-STARTPTS[front];'
          f'[bg][front]overlay=0:{SY}:shortest=1[a1];'
          f'[a1][1:v]overlay=0:0[a2];[a2][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e, _) in enumerate(SUB):
        fc += f";[{last}][{i + 3}:v]overlay=0:0:enable='gte(t,{s:.2f})*lt(t,{e:.2f})'[c{i}]"
        last = f'c{i}'
    fc += f';[{last}]format=yuv420p[o];[0:a]asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.5:LRA=11[au]'
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(T0), '-t', f'{dur:.2f}', '-i', src, *ins, '-filter_complex', fc,
                    '-map', '[o]', '-map', '[au]', '-t', f'{dur:.2f}', '-c:a', 'aac', '-b:a', '160k',
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-movflags', '+faststart', out], check=True)
    # 커버: '젠슨 황은 그의 거시기에 달렸죠' 장면
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{65.8 - T0:.2f}', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out


if __name__ == '__main__':
    print(build())
