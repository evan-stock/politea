"""폴리티커 카드 렌더러(1080x1350 JPEG, PIL).

The Move식 '글씨 넣는 스타일'을 응용한 폴리티커 브랜드 디자인:
- 표지(0번 장): 사진 꽉 채움 + 아래 검정 그라데이션 + 'POLITEA.KR ›' 라벨 + 흰 굵은 제목(왼쪽 정렬),
  '작은따옴표' 단어 뒤에 보라 띠 강조, 선택으로 얼굴 옆 흰 말풍선(bubble)
- 안쪽 장: 위 사진 + 아래 검정, 흰 박스 소제목(sub) → 연보라 헤드라인(t) → 흰 본문(b) 가운데 정렬 → 아래 로고
- 마지막 장: 검정 바탕 공유·팔로우 카드
- 사진이 없는 장은 타이포 카드(검정 바탕)

슬라이드 필드: t(제목/헤드라인, \\n 줄바꿈, '강조'), b(본문), sub(소제목), image(경로),
              fx, fy(사진 초점 0~1), bubble({"text","x","y"}: 표지 말풍선, x·y는 0~1 비율)
"""
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .common import ROOT

W, H = 1080, 1350
VIOLET = (124, 77, 255)
LAV = (185, 163, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
FONTS = ROOT / "assets" / "fonts"
_FC = {}


def font(weight, size):
    """weight: Black | ExtraBold | Bold | SemiBold | Medium | Logo"""
    key = (weight, size)
    if key not in _FC:
        name = "ArchivoBlack-Regular.ttf" if weight == "Logo" else f"Pretendard-{weight}.otf"
        p = FONTS / name
        if not p.exists():  # 없는 굵기는 가장 가까운 것으로
            p = FONTS / "Pretendard-ExtraBold.otf"
        _FC[key] = ImageFont.truetype(str(p), size)
    return _FC[key]


def segs(line):
    """"이재명 '접대' 골프" → [("이재명 ",False),("접대",True),(" 골프",False)]"""
    return [(p, i % 2 == 1) for i, p in enumerate(line.split("'")) if p]


def plain(line):
    return line.replace("'", "")


def tw(f, text):
    return f.getlength(text)


def wrap(text, f, maxw):
    """단어 단위 줄바꿈(한글은 공백 기준, 너무 긴 단어는 글자 단위)."""
    out = []
    for para in text.replace("\\n", "\n").split("\n"):
        line = ""
        for word in para.split(" "):
            cand = (line + " " + word).strip()
            if tw(f, plain(cand)) <= maxw:
                line = cand
                continue
            if line:
                out.append(line)
            line = word
            while tw(f, plain(line)) > maxw:  # 아주 긴 단어
                k = len(line)
                while k > 1 and tw(f, plain(line[:k])) > maxw:
                    k -= 1
                out.append(line[:k])
                line = line[k:]
        if line or not para:
            out.append(line)
    return out


def cover_fit(im, w, h, fx=0.5, fy=0.4):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = int((im.width - w) * fx)
    y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def load(path):
    try:
        return Image.open(path).convert("RGB") if path else None
    except Exception as e:
        print("사진 열기 실패:", path, e)
        return None


def gradient(canvas, y0, y1, a0=0, a1=235):
    g = Image.new("L", (1, H), 0)
    for y in range(H):
        if y < y0:
            v = a0 if a0 else 0
        elif y >= y1:
            v = a1
        else:
            t = (y - y0) / (y1 - y0)
            v = int(a0 + (a1 - a0) * (t ** 1.3))
        g.putpixel((0, y), v)
    g = g.resize((W, H))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(g)
    canvas.alpha_composite(black)


def draw_line(d, x, y, line, f, color, hl_bg=None, hl_fg=None, line_h=None):
    """한 줄 그리기. 강조 구간은 hl_bg(띠 색) 또는 hl_fg(글자 색)로."""
    asc, desc = f.getmetrics()
    for text, hl in segs(line):
        w = tw(f, text)
        if hl and hl_bg:
            pad_x, top = 10, y + int(asc * 0.12)
            d.rectangle([x - pad_x, top, x + w + pad_x, y + asc + int(desc * 0.55)], fill=hl_bg)
        d.text((x, y), text, font=f, fill=(hl_fg if hl and hl_fg else color))
        x += w
    return x


def logo(d, cx, y, size=30, color=(255, 255, 255, 190)):
    """POLITEA.KR 워드마크(Archivo Black, 기울임 대신 그대로). cx: 가운데 x."""
    f = font("Logo", size)
    a, b = "POLITEA", ".KR"
    w = tw(f, a) + tw(f, b)
    x = cx - w / 2
    d.text((x, y), a, font=f, fill=color)
    d.text((x + tw(f, a), y), b, font=f, fill=VIOLET + (color[3] if len(color) == 4 else 255,))


def bubble(d, x, y, text):
    f = font("Bold", 36)
    w = tw(f, text)
    bx0, by0, bx1, by1 = x, y, x + w + 40, y + 66
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=10, fill=WHITE)
    d.polygon([(bx0 + 22, by1 - 2), (bx0 + 44, by1 - 2), (bx0 + 20, by1 + 18)], fill=WHITE)
    d.text((bx0 + 20, by0 + 11), text, font=f, fill=BLACK)


def base_canvas(img, region_h, clear, fx=0.5, fy=0.4):
    """사진(또는 투명/검정) 바탕을 깐 RGBA 캔버스."""
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0) if clear else (0, 0, 0, 255))
    if img is not None and not clear:
        c.paste(cover_fit(img, W, region_h, fx, fy).convert("RGBA"), (0, 0))
    if clear:  # 영상 장: 사진 영역은 투명, 아래는 검정
        if region_h < H:
            c.paste(Image.new("RGBA", (W, H - region_h), (0, 0, 0, 255)), (0, region_h))
    return c


def cover_slide(s, clear=False):
    img = load(s.get("image"))
    c = base_canvas(img, H, clear, s.get("fx", 0.5), s.get("fy", 0.35))
    if img is not None or clear:
        gradient(c, 620, 1180, 0, 238)
    d = ImageDraw.Draw(c)
    f = font("Black", 92)
    lines = [l for l in s["t"].replace("\\n", "\n").split("\n") if l.strip()]
    while max(tw(f, plain(l)) for l in lines) > W - 144 and f.size > 64:
        f = font("Black", f.size - 4)
    lh = int(f.size * 1.28)
    bottom = 1250 if not s.get("sub") else 1190
    y = bottom - lh * len(lines)
    if img is None and not clear:  # 사진 없는 표지: 화면 가운데쯤
        y = (H - lh * len(lines)) // 2 + 40
    d.text((72, y - 58), "POLITEA.KR  ›", font=font("ExtraBold", 34), fill=WHITE)
    for i, l in enumerate(lines):
        draw_line(d, 72, y + i * lh, l, f, WHITE, hl_bg=VIOLET)
    if s.get("sub"):
        d.text((72, bottom + 18), s["sub"], font=font("Medium", 34), fill=GRAY)
    if s.get("bubble") and s["bubble"].get("text"):
        b = s["bubble"]
        bubble(d, int(W * b.get("x", 0.58)), int(H * b.get("y", 0.42)), b["text"])
    return c


def inner_slide(s, clear=False):
    img = load(s.get("image"))
    has_photo = img is not None or clear
    region = 760 if has_photo else 0
    c = base_canvas(img, region if region else H, clear, s.get("fx", 0.5), s.get("fy", 0.4))
    if img is not None and not clear:
        # 사진 아래쪽을 검정으로 자연스럽게 잇기
        gradient(c, 560, region, 0, 255)
        c.paste(Image.new("RGBA", (W, H - region), (0, 0, 0, 255)), (0, region))
    d = ImageDraw.Draw(c)
    maxw = W - 160
    # 사진 없는 타이포 카드는 글자를 키워 화면을 채운다
    fh, fb = (font("Black", 60), font("SemiBold", 42)) if has_photo else (font("Black", 76), font("SemiBold", 48))
    head = wrap(s.get("t", ""), fh, maxw) if s.get("t", "").strip() else []
    body = wrap(s.get("b", ""), fb, maxw) if s.get("b", "").strip() else []
    sub = s.get("sub", "").strip()
    top_y = (region + 40) if has_photo else 0
    limit = 1236

    def block_h(fh, fb, head, body):
        h = 0
        if sub:
            h += 58 + 30
        h += len(head) * int(fh.size * 1.3)
        if head and body:
            h += 26
        h += len(body) * int(fb.size * 1.45)
        return h

    # 넘치면 본문·헤드라인 글자를 줄인다
    while top_y + block_h(fh, fb, head, body) > limit and fb.size > 30:
        fb = font("SemiBold", fb.size - 2)
        if fh.size > 48:
            fh = font("Black", fh.size - 2)
        head = wrap(s.get("t", ""), fh, maxw) if head else []
        body = wrap(s.get("b", ""), fb, maxw) if body else []
    total = block_h(fh, fb, head, body)
    y = top_y if has_photo else (H - total) // 2 - 20
    if sub:
        fs = font("Bold", 32)
        sw = sum(tw(font("Black" if hl else "Bold", 32), t) for t, hl in segs(sub))
        x0 = (W - sw) / 2
        d.rectangle([x0 - 18, y, x0 + sw + 18, y + 58], fill=WHITE)
        x = x0
        for t, hl in segs(sub):
            ff = font("Black" if hl else "Bold", 32)
            d.text((x, y + 10), t, font=ff, fill=BLACK)
            x += tw(ff, t)
        y += 58 + 30
    for l in head:
        draw_line(d, (W - tw(fh, plain(l))) / 2, y, l, fh, LAV, hl_fg=WHITE)
        y += int(fh.size * 1.3)
    if head and body:
        y += 26
    for l in body:
        draw_line(d, (W - tw(fb, plain(l))) / 2, y, l, fb, WHITE, hl_fg=LAV)
        y += int(fb.size * 1.45)
    logo(d, W / 2, 1272, 30)
    return c


LAST_BG = ROOT / "assets" / "last_bg.jpg"  # 마지막 장 고정 배경(태극기 등). 없으면 표지 사진을 어둡게 깐다.


def follow_icon(d, cx, cy, size, color):
    """사람+플러스 아이콘(선)."""
    r = size * 0.18
    w = max(4, int(size * 0.07))
    d.ellipse([cx - r - size * 0.08, cy - size * 0.36, cx + r - size * 0.08, cy - size * 0.36 + 2 * r], outline=color, width=w)
    d.arc([cx - size * 0.42, cy - size * 0.02, cx + size * 0.26, cy + size * 0.62], 180, 360, fill=color, width=w)
    px, py = cx + size * 0.40, cy + size * 0.06
    d.line([px - size * 0.12, py, px + size * 0.12, py], fill=color, width=w)
    d.line([px, py - size * 0.12, px, py + size * 0.12], fill=color, width=w)


def shadow_text(c, xy, text, f, fill, blur=10, alpha=200):
    """글자 뒤에 부드러운 그림자(사진 배경 위 가독성)."""
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(xy, text, font=f, fill=(0, 0, 0, alpha))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(c).text(xy, text, font=f, fill=fill)


def last_slide(s, cover_img=None):
    """우파 채널 정체성 + 팔로우 유도 마지막 장.
    위: 로고 / 가운데(태극기 아래): 선언 문구 / 아래: 앱 팔로우 버튼 모양 알약 CTA.
    s.t: 선언 문구(\\n 줄바꿈), s.b: CTA 위 한 줄."""
    c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    bg = load(str(LAST_BG)) if LAST_BG.exists() else None
    if bg is not None:
        c.alpha_composite(cover_fit(bg, W, H, 0.5, 0.5).convert("RGBA"))
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 60)))
        # 위·아래를 어둡게 덮어 배경 이미지 이음매를 가린다
        top = Image.new("L", (1, H), 0)
        for yy in range(380):
            top.putpixel((0, yy), int(245 * (1 - yy / 380) ** 1.2))
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shade.putalpha(top.resize((W, H)))
        c.alpha_composite(shade)
        gradient(c, 760, 1060, 0, 240)
    elif cover_img is not None:
        c.alpha_composite(cover_fit(cover_img, W, H).filter(ImageFilter.GaussianBlur(30)).convert("RGBA"))
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 205)))
    d = ImageDraw.Draw(c)
    logo(d, W / 2, 96, 64, (255, 255, 255, 255))
    # 선언 문구(태극기 아래)
    lines = (s.get("t") or "자유·시장·안보\n대한민국을 지키는 시선으로\n오늘의 정치를 읽습니다").replace("\\n", "\n").split("\n")
    y = 835
    for i, l in enumerate(lines):
        f = font("Black", 60) if i == 0 else font("Bold", 40)
        shadow_text(c, ((W - tw(f, l)) / 2, y), l, f, WHITE)
        y += int(f.size * 1.42) + (14 if i == 0 else 0)
    d = ImageDraw.Draw(c)
    # CTA: 한 줄 + 앱 팔로우 버튼 모양 알약
    line = s.get("b") or "같은 생각이라면, 팔로우하고 친구에게 공유해주세요"
    fl = font("SemiBold", 31)
    shadow_text(c, ((W - tw(fl, line)) / 2, 1112), line, fl, (235, 235, 235))
    d = ImageDraw.Draw(c)
    fp = font("Black", 40)
    label = "@politea.kr  팔로우"
    pw = tw(fp, label) + 150
    px0, py0 = (W - pw) / 2, 1172
    px1, py1 = px0 + pw, py0 + 92
    d.rounded_rectangle([px0, py0, px1, py1], radius=46, fill=VIOLET)
    # 플러스 원
    cx, cy, r = px0 + 58, (py0 + py1) / 2, 26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.line([cx - 12, cy, cx + 12, cy], fill=VIOLET, width=6)
    d.line([cx, cy - 12, cx, cy + 12], fill=VIOLET, width=6)
    d.text((px0 + 104, py0 + 20), label, font=fp, fill=WHITE)
    return c


def render(slides, outdir, sty=None, col=None, overlays=()):
    """slides 순서대로 01.jpg… 를 만든다. overlays: 영상 장 인덱스 → 그 장은 사진 자리가 투명한 NN_overlay.png 도 만든다."""
    os.makedirs(outdir, exist_ok=True)
    files = []
    n = len(slides)
    cover_img = load(slides[0].get("image")) if slides else None
    for i, s in enumerate(slides):
        if i == 0:
            im = cover_slide(s)
        elif i == n - 1 and n > 1 and s.get("kind", "last") == "last":
            im = last_slide(s, cover_img)
        else:
            im = inner_slide(s)
        fp = os.path.join(outdir, f"{i + 1:02d}.jpg")
        im.convert("RGB").save(fp, quality=93)
        files.append(fp)
        if i in overlays:
            ov = cover_slide(s, clear=True) if i == 0 else inner_slide(s, clear=True)
            ov.save(os.path.join(outdir, f"{i + 1:02d}_overlay.png"))
    return files
