"""더피드 숏츠형 릴스 — 과즙세연 로스트파티3 방시혁 발언 (TTS 없음, 원본 소리 그대로)
원본: 유튜브 펀치라인스 '[로스트파티3] 유튜버 사냥' (CDHTSVHf1Us) 38:01~39:15
양식: scripts/feed_reel/shorts_reel.py (위 검정 띠 제목 2줄 + 영상 + 하단 THE/FEED)
자막: 운영규칙 5절 공통 자막(Pretendard Black 80, 흰 + 검정 외곽선 9, 0.2 기울임, y≈1471, 핵심 [빨강])

사용: python media/20261123-feed-gwajup/build.py [원본.mp4] [--off 초]
  --off : 원본 파일에서 38:01 지점이 몇 초인지(구간 받기 파일이면 0)
"""
import os, sys, subprocess, tempfile, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
TITLE = ["방시혁 루머에 과즙세연이", "[직접 날린 한마디] ㄷㄷ"]
START, END = 1.0, 73.0   # 클립 안에서 쓸 구간(38:02~39:14)

# (시작, 끝, 자막) — 클립(38:01 기준) 초. 욕설은 자막에서 가림.
SUB = [
    (2.0, 7.5,  "마지막으로\n[방시혁 사건]에 대해서"),
    (12.0, 14.5, "말씀 좀 드릴게요"),
    (14.5, 18.5, "아무리 아니라고 해도"),
    (18.5, 22.0, "[돈 때문에] 방시혁이랑\n잤냐고 왜 물어봐요?"),
    (22.0, 30.0, "아 너네는 돈 때문에\n[방시혁이랑 자고 싶구나]"),
    (30.0, 33.0, "[안 잤습니다]"),
    (33.0, 36.0, "돈 얘기하시는 분들께\n한 마디만 할게요"),
    (36.0, 42.5, "나랑 방시혁 자산 차이보다"),
    (42.5, 46.0, "[나랑 너희들 자산 차이]가\n훨씬 커요"),
    (46.0, 48.5, "[거지XX들아]"),
    (52.0, 55.0, "잘 들으세요"),
    (55.0, 62.0, "저랑 밥 먹는 식사권\n[700만 원] 내야 합니다"),
    (62.0, 68.0, "오늘 공연 끝나고\n[700만 원 내고] 뒤풀이 안 감"),
    (68.0, 72.0, "감사합니다\n과즙세연이었습니다"),
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


def build(src, off=0.0, y=0.5):
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, 'ov.png'); sr.overlay(TITLE, ov); src_png(os.path.join(tmp, 'src.png'))
    for i, (_, _, t) in enumerate(SUB):
        sub_png(t, os.path.join(tmp, f's{i:02d}.png'))
    vh = H - sr.BAND
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SUB))], [])
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30[bg];'
          f'[0:v]setpts=PTS-STARTPTS,scale={W}:{vh}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{vh}:(iw-{W})/2:(ih-{vh})*{y}[v];'
          f'[bg][v]overlay=0:{sr.BAND}:shortest=1[a0];[a0][1:v]overlay=0:0[a1];[a1][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e, _) in enumerate(SUB):
        s2, e2 = max(0, s - START), e - START
        fc += f';[{last}][{i + 3}:v]overlay=0:0:enable=\'gte(t,{s2:.2f})*lt(t,{e2:.2f})\'[c{i}]'
        last = f'c{i}'
    fc += f';[{last}]format=yuv420p[o];[0:a]asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.5:LRA=11[au]'
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{off + START:.2f}', '-t', f'{END - START:.2f}', '-i', src, *ins,
                    '-filter_complex', fc, '-map', '[o]', '-map', '[au]', '-c:a', 'aac', '-b:a', '160k',
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-movflags', '+faststart', out], check=True)
    # 커버: '식사권 700만 원' 자막 장면
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{57 - START}', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('src', nargs='?', default=os.path.join(HERE, 'video/v1.mp4'))
    a.add_argument('--off', type=float, default=0.0)
    a.add_argument('--y', type=float, default=0.5)
    r = a.parse_args()
    print(build(r.src, r.off, r.y))
