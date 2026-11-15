"""더피드 캐러셀(표지+영상 2장): 세무사 수석 AI 부정행위 자수 (오늘의쓸모 20261115-brk 소재 재활용, 이미지·문구 새로).
틀: 사진 꽉 + 아래 검정 그라데이션, 흰 굵은 제목 가운데·[핵심어] 빨강, 오른쪽 위 출처, 왼쪽 위 장 번호, 하단 가운데 THE/FEED 로고.
소스 사진·영상은 /tmp/taxsrc (오늘의쓸모 media/20261115-brk/cand, video/v1.mp4)."""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'feed_reel'))
import feedlib as fl
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT = os.path.dirname(os.path.abspath(__file__)); SRC = '/tmp/taxsrc'
W, H = 1080, 1350; RED = fl.RED
FT = lambda s: ImageFont.truetype(fl.F, s)
FB = lambda s: ImageFont.truetype(fl.FM, s)
FN = lambda s: ImageFont.truetype(fl.ANTON, s)
N = 2


def grad(im, y0, y1, a1=245):
    g = Image.new('L', (1, H), 0)
    for y in range(H):
        g.putpixel((0, y), 0 if y < y0 else a1 if y > y1 else int(a1 * ((y - y0) / (y1 - y0)) ** 1.3))
    black = Image.new('RGB', (W, H), (8, 8, 10))
    return Image.composite(black, im, g.resize((W, H)))


def chrome(im, k, credit):
    d = ImageDraw.Draw(im)
    if k > 1:
        d.text((56, 92), f'{k:02d}', font=FN(46), fill=(255, 255, 255), anchor='ls', stroke_width=2, stroke_fill=(0, 0, 0))
        d.text((56 + d.textlength(f'{k:02d}', font=FN(46)) + 8, 92), f'/ {N:02d}', font=FN(26),
               fill=(220, 220, 220), anchor='ls', stroke_width=2, stroke_fill=(0, 0, 0))
    if credit:
        d.text((W - 48, 80), credit, font=FB(24), fill=(235, 235, 235), anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0))
    fl.W = W
    fl.stacked_logo(d, W / 2, 1238, feed=40, center=True)


def text_block(im, title, body, fs=74, bottom=1192):
    d = ImageDraw.Draw(im); fl.W = W
    bl = body.split('\n') if body else []
    tl = title.split('\n')
    y = bottom - len(bl) * 50
    by = y + 40
    ty = y - (len(tl) - 1) * (fs + 16) - (34 if bl else 0)
    for i, t in enumerate(tl):
        fl.line(d, t, ty + i * (fs + 16), FT(fs))
    for i, b in enumerate(bl):
        fl.line(d, b, by + i * 50, FB(34), fg=(214, 214, 220))


def photo(src, fy=.4, fx=.5, zoom=1.0):
    im = Image.open(os.path.join(SRC, src)).convert('RGB')
    if zoom != 1.0:
        w, h = im.size; cw, ch = int(w / zoom), int(h / zoom)
        x0 = int((w - cw) * fx); y0 = int((h - ch) * fy); im = im.crop((x0, y0, x0 + cw, y0 + ch))
    return ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(fx, fy))


def card(k, src, title, body, credit, fy=.4, fx=.5, zoom=1.0, fs=74, g0=560):
    im = grad(photo(src, fy, fx, zoom), g0, 1080)
    text_block(im, title, body, fs)
    chrome(im, k, credit)
    im.save(os.path.join(OUT, f'{k:02d}.jpg'), quality=94)
    return im


# 1 표지: 유튜브 영상 캡처(22.5초, 자막 없는 장면)를 확대하지 않고 위쪽 폭에 맞춰 1.5배로만 + 아래 검정
fr = Image.open(os.path.join(SRC, 'yt_frame22.png')).convert('RGB').resize((W, 855), Image.LANCZOS)
cv = Image.new('RGB', (W, H), (8, 8, 10)); cv.paste(fr, (0, 0))
cv = grad(cv, 560, 850, 255)
text_block(cv, '160문제 중 159개 맞힌\n세무사 수석, 결국\n[경찰에 자수]했다', '', 86)
chrome(cv, 1, '유튜브 \'이돈호 변호사\'')
cv.save(os.path.join(OUT, '01.jpg'), quality=94)

# 2 영상 장: 위쪽 영상(원본 자막 포함) + 아래 문구
base = Image.new('RGB', (W, H), (8, 8, 10))
text_block(base, '마스크 쓰고 직접 나와\n\"[부정행위] 했습니다\"', '15일 대리인 이돈호 변호사 유튜브에서\n세무사 1·2차 모두 AI를 썼다고 밝혀')
chrome(base, 2, '유튜브 \'이돈호 변호사\'')
mask = Image.new('L', (W, H), 255)
md = ImageDraw.Draw(mask)
VH = 850
for y in range(VH):  # 영상 자리는 투명, 아래 120px은 점점 불투명(영상 → 검정 자연스럽게)
    a = 0 if y < VH - 120 else int(255 * ((y - (VH - 120)) / 120) ** 1.2)
    md.line([(0, y), (W, y)], fill=a)
ov = base.convert('RGBA'); ov.putalpha(mask)
# 장 번호·출처는 영상 위에도 보이게 다시 그림
od = ImageDraw.Draw(ov)
od.text((56, 92), '02', font=FN(46), fill=(255, 255, 255, 255), anchor='ls', stroke_width=2, stroke_fill=(0, 0, 0, 255))
od.text((56 + od.textlength('02', font=FN(46)) + 8, 92), f'/ {N:02d}', font=FN(26), fill=(220, 220, 220, 255), anchor='ls', stroke_width=2, stroke_fill=(0, 0, 0, 255))
od.text((W - 48, 80), '유튜브 \'이돈호 변호사\'', font=FB(24), fill=(235, 235, 235, 255), anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0, 255))
ov.save('/tmp/feed_tax_ov.png')
ov.convert('RGB').save(os.path.join(OUT, '02_poster.jpg'), quality=90)
if not os.environ.get('SKIP_VIDEO'):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '26', '-t', '30', '-i', os.path.join(SRC, 'v1.mp4'), '-i', '/tmp/feed_tax_ov.png',
                    '-filter_complex',
                    f'color=c=0x08080a:s={W}x{H}:r=30[bg];[0:v]crop=720:567:0:378,scale={W}:{VH}:flags=lanczos[v];'
                    '[bg][v]overlay=0:0:shortest=1[t];[t][1:v]overlay=0:0,format=yuv420p[o]',
                    '-map', '[o]', '-map', '0:a', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', os.path.join(OUT, '02.mp4')], check=True)

print('ok')
