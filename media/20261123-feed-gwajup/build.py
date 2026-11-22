"""더피드 숏츠형(띠형) 릴스 — 과즙세연 로스트파티3 방시혁 발언 (TTS 없음, 원본 소리 그대로)
원본: 유튜브 펀치라인스 '[로스트파티3] 유튜버 사냥' (CDHTSVHf1Us) 38:01~39:15 (맥북 도우미 구간 받기)
양식: 마라톤 릴스(media/20261123-feed-runner/build.py)와 같음 — 제목 띠 + 가로 영상 전체(위아래 검정)
      + 영상 아래 해설 자막 + 하단 THE/FEED. 영상에 흐림·모자이크 없음(원본 자막 그대로).
"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SRC = os.path.join(HERE, 'video/v1.mp4')
TITLE = ["방시혁 루머에 과즙세연이", "[직접 날린 한마디] ㄷㄷ"]
START, END = 1.0, 73.0          # 클립(38:01 기준) 안에서 쓸 구간
SH = 608                         # 1920x1080 → 1080x608
SY = 720                         # 영상 띠 위 끝

# 해설 자막 (클립 기준 초)
SUB = [
    (1.0, 12.0, "방시혁 루머에\n과즙세연이 [직접 입 열었다]"),
    (12.0, 22.0, "[2024년 LA]에서\n방 의장과 함께 포착"),
    (22.0, 31.0, "열애설에 돈 루머까지\n[계속 따라붙었는데]"),
    (31.0, 36.0, "결론은 [\"안 잤다\"]"),
    (36.0, 47.5, "오히려 [자산 차이]로\n맞받아친 과즙세연"),
    (47.5, 52.0, "현장은 [환호] ㅋㅋ"),
    (52.0, 68.0, "본인 식사권은\n[700만 원]이라고"),
    (68.0, 73.0, "로스트파티3\n(8월 30일 녹화)"),
]
SRC_LABEL = "영상: 유튜브 펀치라인스"


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


def build(src=SRC):
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, 'ov.png'); sr.overlay(TITLE, ov); src_png(os.path.join(tmp, 'src.png'))
    for i, (_, _, t) in enumerate(SUB):
        sub_png(t, os.path.join(tmp, f's{i:02d}.png'))
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SUB))], [])
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30[bg];'
          f'[0:v]setpts=PTS-STARTPTS,scale={W}:{SH}:flags=lanczos[front];'
          f'[bg][front]overlay=0:{SY}:shortest=1[a1];'
          f'[a1][1:v]overlay=0:0[a2];[a2][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e, _) in enumerate(SUB):
        s2, e2 = max(0, s - START), e - START
        fc += f";[{last}][{i + 3}:v]overlay=0:0:enable='gte(t,{s2:.2f})*lt(t,{e2:.2f})'[c{i}]"
        last = f'c{i}'
    fc += f';[{last}]format=yuv420p[o];[0:a]asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.5:LRA=11[au]'
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{START:.2f}', '-t', f'{END - START:.2f}', '-i', src, *ins,
                    '-filter_complex', fc, '-map', '[o]', '-map', '[au]', '-c:a', 'aac', '-b:a', '160k',
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-movflags', '+faststart', out], check=True)
    # 커버: '700만 원 내야 합니다' 장면
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{57 - START}', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv) > 1 else SRC))
