"""더피드 숏츠형 릴스 — 마라톤 통제에 폭발한 운전자 (TTS 없음, 원본 소리 그대로)
원본: YTN 보도 화면(인스타 @themovemag_ 릴스 DgBuB0mzTC6로 받음). 릴스 안 가로 영상 띠 y 437~798만 사용.
양식: shorts_reel.py 제목 띠·로고 + 공통 자막. 가로 영상이라 꽉 채우면 4배 확대돼 뭉개짐 →
      가로 전체를 보여주고 위아래는 검정. 영상에 흐림·모자이크 넣지 않음(2026-11-23 사용자).
"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SRC = os.path.join(HERE, 'video/v1.mp4')
STRIP = (0, 437, 720, 361)          # x, y, w, h (원본 릴스 안 가로 영상)
TITLE = ["주말마다 막히는 서울 도심", "[결국 폭발한 운전자] ㄷㄷ"]
SH = round(W * STRIP[3] / STRIP[2] / 2) * 2   # 띠 높이(1080 폭 기준) ≈ 542
SY = 760                                        # 띠 위치(위 끝)

# 해설 자막(대사 받아쓰기 아님). 원본 자막은 영상 띠 안, 해설은 띠 아래 검정 공간 y≈1471.
SUB = [
    (0.0, 4.0, "[주말마다] 도로 막는\n도심 마라톤"),
    (4.0, 8.0, "버스·차량은 줄줄이 우회"),
    (8.0, 12.0, "참다 못한 운전자\n결국 [폭발]"),
    (12.0, 16.0, "서울 마라톤 대회\n4년 새 [3배] 늘어"),
    (16.0, 19.5, "교통 불편 민원은\n[10배] 넘게 폭증"),
    (19.5, 22.2, "결국 [경찰이 대신 사과]\nㅠㅠ"),
]
_SUB_OLD = [
    (0.0, 1.0, "[@#?!%&*]"),
    (1.0, 2.0, "[그만 좀 해라]"),
    (2.0, 4.5, "여기서 어디로 가야 돼요\n도대체"),
    (4.5, 5.0, "마라톤 끝났어요?"),
    (5.0, 6.0, "(경찰) 안 끝났어요…"),
    (6.0, 7.0, "안 끝났어요?"),
    (7.0, 7.5, "(경찰) 예…"),
    (7.5, 8.5, "그럼 저 쪽으로 가려면"),
    (8.5, 9.5, "[어떻게 가야 되냐고!!]"),
    (9.5, 12.0, "(경찰) 서대문까지\n가셔야 돼요"),
    (12.0, 14.0, "[주말마다] 이게\n뭐 하는 거야"),
    (14.0, 15.5, "[도대체가!!]"),
    (15.5, 17.5, "[불편하게] 이게 뭐냐고!!!"),
    (17.5, 19.5, "(경찰) 한 시간만 해요…"),
    (19.5, 20.5, "(경찰) 제가 대신\n사과 드릴게요"),
    (20.5, 22.2, "(경찰) 오늘만 좀\n돌아가 주세요"),
]
SRC_LABEL = "영상: YTN"


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
    vh = H - sr.BAND
    x, y, w, h = STRIP
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SUB))], [])
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30[bg];'
          f'[0:v]crop={w}:{h}:{x}:{y},scale={W}:{SH}:flags=lanczos[front];'
          f'[bg][front]overlay=0:{SY}:shortest=1[a1];'
          f'[a1][1:v]overlay=0:0[a2];[a2][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e, _) in enumerate(SUB):
        fc += f";[{last}][{i + 3}:v]overlay=0:0:enable='gte(t,{s:.2f})*lt(t,{e:.2f})'[c{i}]"
        last = f'c{i}'
    fc += f';[{last}]format=yuv420p[o];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[au]'
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, *ins, '-filter_complex', fc,
                    '-map', '[o]', '-map', '[au]', '-c:a', 'aac', '-b:a', '160k',
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-movflags', '+faststart', out], check=True)
    # 커버: '주말마다 이게 뭐 하는 거야' 장면
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '12.8', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv) > 1 else SRC))
