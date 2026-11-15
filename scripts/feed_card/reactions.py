"""더피드 캐러셀 마지막 장 '인터넷 반응' (사용자 결정 2026-11-15, 유머채널 ㅋㅋ상회 reactions 틀과 같은 방식).
검정 바탕 + 흰 상자 + 빨간 테두리(#FF3B30), 굵은 검정 글씨로 반응을 세로로 쌓는다. 닉네임 없음. 하단 가운데 THE/FEED.
사용: python scripts/feed_card/reactions.py media/<id>/NN.jpg "반응1" "반응2" "반응3" [--head "인터넷 반응"]
반응은 실제 커뮤니티·댓글 반응을 짧게(1~3줄). 3~4개."""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'feed_reel'))
import feedlib as fl
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
RED = (255, 59, 48)


def wrap(text, f, maxw, d):
    out = []
    for para in text.split('\n'):
        cur = ''
        for ch in para:
            if d.textlength(cur + ch, font=f) <= maxw:
                cur += ch
            else:
                cut = cur.rfind(' ')
                if cut > 0:
                    out.append(cur[:cut]); cur = cur[cut + 1:] + ch
                else:
                    out.append(cur); cur = ch
        out.append(cur)
    return out


def render(items, out, head=None):
    img = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    X, BW, PX, PY, GAP = 30, 9, 40, 32, 44
    top_min, bot_max = (210 if head else 110), 1200   # 아래는 로고 자리
    size = 52
    while True:
        f = ImageFont.truetype(fl.F, size); lh = round(size * 1.42)
        blocks = [wrap(t, f, W - 2 * X - 2 * BW - 2 * PX, d) for t in items]
        hs = [len(b) * lh + 2 * PY + 2 * BW for b in blocks]
        total = sum(hs) + GAP * (len(hs) - 1)
        if total <= bot_max - top_min or size <= 34:
            break
        size -= 2
    if head:
        fl.W = W; fl.line(d, head, 150, ImageFont.truetype(fl.F, 64))
    y = top_min + (bot_max - top_min - total) // 2
    for lines, h in zip(blocks, hs):
        d.rectangle((X, y, W - X, y + h), fill=RED)
        d.rectangle((X + BW, y + BW, W - X - BW, y + h - BW), fill='white')
        yy = y + BW + PY
        for l in lines:
            d.text((X + BW + PX, yy + lh / 2), l, font=f, fill=(20, 20, 20), anchor='lm'); yy += lh
        y += h + GAP
    fl.W = W; fl.stacked_logo(d, W / 2, 1238, feed=40, center=True)
    img.save(out, quality=94); return out


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('out'); a.add_argument('items', nargs='+'); a.add_argument('--head')
    r = a.parse_args(); print(render(r.items, r.out, r.head))
