"""폴리티커 릴스(1080x1920) 만들기.

레이아웃(The Move식 글씨 배치 응용):
- 바탕 검정
- 위쪽 가운데 제목 2줄(Pretendard ExtraBold, '강조' 단어는 연보라)
- 가운데 원본 영상(가로 영상은 폭 1080, 세로·정사각 영상은 높이 900)
- 영상 아래 POLITEA.KR 로고 + '영상: 매체명'
- 원본 소리 유지
"""
import json
import subprocess

from PIL import Image, ImageDraw

from .render import LAV, VIOLET, WHITE, font, plain, segs, tw

W, H = 1080, 1920
SOFT_LAV = (159, 123, 255)  # 검정 위 강조색(#9F7BFF)


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation", "-of", "json", src],
                         capture_output=True, text=True).stdout
    st = json.loads(out)["streams"][0]
    w, h = st["width"], st["height"]
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        rot = abs(int(sd.get("rotation", 0)))
    return (h, w) if rot in (90, 270) else (w, h)


def window(vw, vh):
    """영상이 놓일 자리 (x, y, w, h)와 로고 y."""
    if vw / vh >= 1.0:
        w, h = W, round(W * vh / vw / 2) * 2
        h = min(h, 1080)
        y = 600
    else:
        h = 900
        w = round(h * vw / vh / 2) * 2
        y = 560
    return (W - w) // 2, y, w, h, y + h + 70


def overlay(title, credit, vw, vh, path, with_frame=None):
    """제목·로고·출처를 그린 PNG. with_frame(이미지)이 있으면 영상 자리에 그 프레임을 넣은 커버 JPG를 만든다."""
    x, y, w, h, logo_y = window(vw, vh)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0 if with_frame is None else 255))
    if with_frame is not None:
        fr = with_frame.convert("RGB").resize((w, h), Image.LANCZOS)
        c.paste(fr, (x, y))
    d = ImageDraw.Draw(c)
    lines = [l for l in title.replace("\\n", "\n").split("\n") if l.strip()]
    f = font("ExtraBold", 70)
    while max(tw(f, plain(l)) for l in lines) > W - 100 and f.size > 50:
        f = font("ExtraBold", f.size - 2)
    lh = int(f.size * 1.32)
    ty = y - 70 - lh * len(lines)
    ty = max(ty, 250)  # 프로필 격자(가운데 3:4)·상단 UI 안전 영역
    for i, l in enumerate(lines):
        xx = (W - tw(f, plain(l))) / 2
        for t, hl in segs(l):
            d.text((xx, ty + i * lh), t, font=f, fill=SOFT_LAV if hl else WHITE)
            xx += tw(f, t)
    fl = font("Logo", 54)
    a, b = "POLITEA", ".KR"
    lw = tw(fl, a) + tw(fl, b)
    lx = (W - lw) / 2
    d.text((lx, logo_y), a, font=fl, fill=WHITE)
    d.text((lx + tw(fl, a), logo_y), b, font=fl, fill=VIOLET)
    if credit:
        fc = font("Medium", 26)
        d.text(((W - tw(fc, credit)) / 2, logo_y + 84), credit, font=fc, fill=(138, 138, 138))
    if with_frame is not None:
        c.convert("RGB").save(path, quality=93)
    else:
        c.save(path)
    return path, (x, y, w, h)


def make(src, title, credit, out, cover_out, start=0.0, dur=30.0, frame=1.5, keep_audio=True, crop=None):
    """crop: 원본에서 잘라낼 영역 [x,y,w,h](로고·자막 제거용, 픽셀). 없으면 전체."""
    vw, vh = probe(src)
    if crop:
        vw, vh = crop[2], crop[3]
    ov, (x, y, w, h) = overlay(title, credit, vw, vh, out.rsplit(".", 1)[0] + "_overlay.png")
    pre = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else ""
    fc = (f"color=c=black:s={W}x{H}:r=30:d={dur}[bg];"
          f"[0:v]{pre}scale={w}:{h}:flags=lanczos,setsar=1,unsharp=5:5:0.5,fps=30[v];"
          f"[bg][v]overlay={x}:{y}:shortest=1[b];[b][1:v]overlay=0:0,format=yuv420p[o]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(dur), "-i", src, "-i", ov]
    has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    if keep_audio and has_audio:
        amap = ["-map", "0:a"]
    else:
        cmd += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo"]
        amap = ["-map", "2:a"]
    cmd += ["-filter_complex", fc, "-map", "[o]", *amap, "-shortest", "-c:v", "libx264", "-profile:v", "high",
            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    # 커버: 같은 레이아웃에 대표 프레임
    tmp = out.rsplit(".", 1)[0] + "_frame.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start + frame), "-i", src, "-frames:v", "1",
                    *(["-vf", pre.rstrip(",")] if crop else []), "-q:v", "2", tmp], check=True)
    overlay(title, credit, vw, vh, cover_out, with_frame=Image.open(tmp))
    return out, cover_out
