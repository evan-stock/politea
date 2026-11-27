"""더피드 숏츠형 릴스 — 사이렌 울리는 119 구급차 앞을 그냥 달린 마라톤 참가자들 (TTS 없음, 원본 소리 그대로)
원본: 유튜브 '닥신TV'(내과 전문의 신제욱) 쇼츠 RCqKBsrdGXs(2026.11.16). video/v1.mp4 = 원본 97~108.3·24~29.5·37~45.5·30~37초를 이어 붙인 것.
세로 원본에서 위 영상 제목·아래 원본 자막을 피해 y 300~790 띠만 사용(흐림 없음).
사실: 아시아경제·SBS(11.26) 약 30명·10초 넘게, 한겨레(서울 마라톤 2021 50개→2025 154개).
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
STRIP = (0, 300, 720, 490)          # x, y, w, h (세로 원본에서 도로 부분)
TITLE = ["119 구급차 길까지 막은", "[민폐 마라톤] 실화냐"]
SH = round(W * STRIP[3] / STRIP[2] / 2) * 2   # 띠 높이(1080 폭 기준) ≈ 542
SY = 560                                        # 띠 위치(위 끝)

# 해설 자막(대사 받아쓰기 아님). 원본 자막은 영상 띠 안, 해설은 띠 아래 검정 공간 y≈1471.
SUB = [
    (0.0, 3.2, "사이렌 울리며\n[유턴하려는 119]"),
    (3.2, 6.1, "\"119 유턴할 땐\n[잠깐 멈춰야 하지 않을까]\""),
    (6.1, 11.3, "약 [30명] 지나간 뒤에야\n겨우 유턴"),
    (11.3, 16.8, "[건국대병원] 바로 앞\n하프마라톤 날"),
    (16.8, 25.3, "길 건너는 법 묻자\n[틈 나면 같이 뛰라고]"),
    (25.3, 28.8, "서울 마라톤 대회\n4년 새 [3배]"),
    (28.8, 32.4, "생명보다 [기록]?\nㅠㅠ"),
]
SRC_LABEL = "영상: 유튜브 닥신TV"


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
    # 커버: 구급차가 참가자들 사이에 갇힌 장면
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '2.5', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv) > 1 else SRC))
