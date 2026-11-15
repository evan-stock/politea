"""더피드 기본 세로형 릴스 (사용자 결정 2026-11-15): 숏츠처럼 위쪽 검정 띠에 제목 2줄(기울임, 둘째 줄/[대괄호] 빨강),
그 아래는 전부 영상(화면 꽉 채우게 확대·자름), 하단 가운데 THE/FEED 로고.
'AI 생성 영상' 같은 표시는 화면에 넣지 않고 캡션에만 쓴다.

사용:
  python scripts/feed_reel/shorts_reel.py 원본.mp4 media/<id>/reel.mp4 "제목 1줄" "[제목 2줄]" [--y 0.11] [--start 0] [--dur 0]
  --y : 영상을 화면에 맞게 키운 뒤 위아래로 얼마나 잘라낼지 위치(0=위쪽만 보임, 0.5=가운데, 기본 0.5)
  커버(reel_cover.jpg)도 같은 폴더에 만든다(--cover 초, 기본 1.5).
"""
import argparse, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feedlib as fl
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440
SHEAR = 0.2  # 기울임 정도


def italic_line(ov, text, y, font):
    """[대괄호] 빨강 강조 줄을 가운데 정렬로 그리고 오른쪽으로 기울인다(Pretendard에 이탤릭이 없어 기울여 만듦)."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fl.W = W; fl.line(d, text, y, font)
    yc = y - font.size * 0.35
    lay = lay.transform((W, H), Image.AFFINE, (1, SHEAR, -SHEAR * yc, 0, 1, 0), Image.BICUBIC)
    ov.alpha_composite(lay)


def overlay(lines, path, size=84):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle((0, 0, W, BAND), fill=(8, 8, 10, 255))
    f = ImageFont.truetype(fl.F, size)
    ys = [300, 400] if len(lines) == 2 else [400] if len(lines) == 1 else [210, 305, 400]
    for t, y in zip(lines, ys):
        italic_line(ov, t, y, f)
    d = ImageDraw.Draw(ov)
    for y in range(1640, H):  # 로고 자리 은은한 그라데이션
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * ((y - 1640) / (H - 1640)) ** 1.2)))
    fl.stacked_logo(d, W / 2, 1715, feed=50, center=True)
    ov.save(path)


def make(src, out, lines, y=0.5, start=0.0, dur=0.0, cover_t=1.5):
    png = os.path.join(tempfile.mkdtemp(), 'ov.png'); overlay(lines, png)
    vh = H - BAND
    vf = (f'[0:v]scale={W}:{vh}:force_original_aspect_ratio=increase:flags=lanczos,'
          f'crop={W}:{vh}:(iw-{W})/2:(ih-{vh})*{y}[v]')
    cut = (['-ss', str(start)] if start else []) + (['-t', str(dur)] if dur else [])
    has_audio = 'audio' in subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', src],
                                          capture_output=True, text=True).stdout
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *cut, '-i', src, '-i', png, '-filter_complex',
                    f'color=c=0x08080a:s={W}x{H}:r=30[bg];{vf};[bg][v]overlay=0:{BAND}:shortest=1[t];[t][1:v]overlay=0:0,format=yuv420p[o]',
                    '-map', '[o]', *(['-map', '0:a', '-c:a', 'aac', '-b:a', '128k'] if has_audio else []),
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-movflags', '+faststart', out], check=True)
    cover = os.path.join(os.path.dirname(out) or '.', 'reel_cover.jpg')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(cover_t), '-i', out, '-frames:v', '1', '-q:v', '2', cover], check=True)
    return out, cover


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('src'); a.add_argument('out'); a.add_argument('lines', nargs='+')
    a.add_argument('--y', type=float, default=0.5); a.add_argument('--start', type=float, default=0)
    a.add_argument('--dur', type=float, default=0); a.add_argument('--cover', type=float, default=1.5)
    r = a.parse_args()
    print(make(r.src, r.out, r.lines, r.y, r.start, r.dur, r.cover))
