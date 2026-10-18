"""장마다 다른 배경 사진 고르기: 위키미디어 커먼즈(공개 라이선스) → 없으면 AI 생성."""
import base64
import os
import re

import requests

from .common import CFG, strip_html

COMMONS = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "today-worthy-cardnews/1.0 (https://github.com/%s)" % os.environ.get("GITHUB_REPOSITORY", "")}
OK_LICENSE = re.compile(r"^(public domain|pd|cc0|cc by(-sa)? ?[0-9.]*|cc-by(-sa)?-[0-9.]+|copyrighted free use)", re.I)


def commons_candidates(query, limit=12):
    r = requests.get(COMMONS, headers=UA, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrlimit": limit, "gsrsearch": f"{query} filetype:bitmap",
        "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1280})
    r.raise_for_status()
    pages = (r.json().get("query") or {}).get("pages") or {}
    out = []
    for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata") or {}
        lic = strip_html((m.get("LicenseShortName") or {}).get("value", ""))
        if not OK_LICENSE.match(lic) or ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if min(ii.get("width", 0), ii.get("height", 0)) < 600:
            continue
        out.append({
            "title": p["title"][5:], "url": ii.get("thumburl") or ii.get("url"), "license": lic,
            "artist": strip_html((m.get("Artist") or {}).get("value", ""))[:60] or "unknown",
            "page": ii.get("descriptionurl", "")})
    return out


def download(url, path):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)


def ai_image(prompt, path):
    key = os.environ.get("OPENAI_API_KEY")
    if CFG["images"].get("ai_fallback") != "openai" or not key or not prompt:
        return False
    r = requests.post("https://api.openai.com/v1/images/generations", timeout=300,
                      headers={"Authorization": f"Bearer {key}"},
                      json={"model": CFG["images"]["openai_model"], "prompt": prompt,
                            "size": CFG["images"]["openai_size"], "n": 1})
    if r.status_code != 200:
        print("AI 이미지 실패:", r.status_code, r.text[:200])
        return False
    data = r.json()["data"][0]
    if data.get("b64_json"):
        open(path, "wb").write(base64.b64decode(data["b64_json"]))
    else:
        download(data["url"], path)
    return True


BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36", "Accept-Language": "ko,en;q=0.8"}
SKIP_IMG = re.compile(r"(logo|icon|sprite|avatar|profile|banner|btn|button|ad[s_/-]|pixel|blank|placeholder|emoji|author|byline|headshot|web-bio|newsletter|\.svg|\.gif)", re.I)


def _abs(base, u):
    from urllib.parse import urljoin
    return urljoin(base, u.strip())


def page_images(url):
    """기사·영상 페이지에서 쓸 만한 사진 주소 목록(대표 이미지 먼저)."""
    from urllib.parse import parse_qs, urlparse
    host = urlparse(url).netloc.lower()
    # 유튜브: 썸네일
    if "youtube.com" in host or "youtu.be" in host:
        vid = parse_qs(urlparse(url).query).get("v", [None])[0] or urlparse(url).path.strip("/").split("/")[-1]
        return [f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg", f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"] if vid else []
    # 틱톡: oEmbed 썸네일
    if "tiktok.com" in host:
        r = requests.get("https://www.tiktok.com/oembed", params={"url": url}, headers=BROWSER_UA, timeout=20)
        t = r.json().get("thumbnail_url") if r.ok else None
        return [t] if t else []
    r = requests.get(url, headers=BROWSER_UA, timeout=30)
    r.raise_for_status()
    html = r.text
    out = []
    for prop in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
        for m in re.finditer(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*>' % re.escape(prop), html, re.I):
            c = re.search(r'content=["\']([^"\']+)', m.group(0))
            if c:
                out.append(_abs(url, c.group(1)))
    body = re.search(r"<article[\s\S]*?</article>", html, re.I)
    for m in re.finditer(r'<img[^>]+(?:data-src|data-original|src)=["\']([^"\']+)', body.group(0) if body else html, re.I):
        out.append(_abs(url, m.group(1)))
    if len(out) < 5:  # 본문 사진이 적으면 리더 서비스로 기사 본문 이미지 추가 확보
        try:
            jr = requests.get("https://r.jina.ai/" + url, timeout=60)
            if jr.ok:
                out += re.findall(r"!\[[^\]]*\]\((https?://[^)\s]+)", jr.text)
        except Exception as e:
            print("리더 서비스 실패:", e)
    import html as _html
    out = [_html.unescape(u).split("#")[0] for u in out]
    seen, res = set(), []
    for u in out:
        if u.startswith("http") and u not in seen and not SKIP_IMG.search(u):
            seen.add(u)
            res.append(u)
    return res[:15]


def _dhash(path):
    from PIL import Image
    with Image.open(path) as im:
        g = im.convert("L").resize((9, 8))
        px = list(g.getdata())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])


def _good_image(path):
    from PIL import Image
    try:
        with Image.open(path) as im:
            w, h = im.size
            if min(w, h) < 300 or not (0.4 <= w / h <= 2.6):
                return False
            rgb = im.convert("RGB")
        rgb.save(path, "JPEG", quality=92)  # webp·png도 진짜 JPEG로 통일
        return True
    except Exception as e:
        print("이미지 검사 실패:", path, e)
        return False


def press_images(pages, outdir, limit=16):
    """출처 기사·영상에서 사진을 모은다. [(경로, 출처표기)]"""
    import hashlib
    from urllib.parse import urlparse
    os.makedirs(outdir, exist_ok=True)
    got, hashes, dhs = [], set(), []
    for page in pages:
        try:
            urls = page_images(page)
        except Exception as e:
            print("기사 사진 수집 실패:", page, e)
            continue
        credit = urlparse(page).netloc.replace("www.", "")
        for u in urls:
            if len(got) >= limit:
                return got
            path = os.path.join(outdir, f"press{len(got) + 1:02d}.jpg")
            try:
                r = requests.get(u, headers={**BROWSER_UA, "Referer": page}, timeout=30)
                if not r.ok or "image" not in r.headers.get("content-type", "image"):
                    continue
                h = hashlib.md5(r.content).hexdigest()
                if h in hashes:
                    continue
                open(path, "wb").write(r.content)
                if not _good_image(path):
                    os.remove(path)
                    continue
                dh = _dhash(path)
                if any(bin(dh ^ o).count("1") <= 10 for o in dhs):  # 거의 같은 사진
                    os.remove(path)
                    continue
                dhs.append(dh)
                hashes.add(h)
                got.append((path, credit))
            except Exception:
                continue
    return got


def relevant_only(pool, story):
    """Claude가 사진을 직접 보고 이 이야기와 관련 있는 사진만 남긴다(표지감 순서로 정렬)."""
    import base64, io, json, re as _re
    from PIL import Image
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not pool or not key or not story:
        return pool
    content = []
    for k, (path, _) in enumerate(pool):
        im = Image.open(path).convert("RGB")
        im.thumbnail((512, 512))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        content += [{"type": "text", "text": f"사진 {k}"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                  "data": base64.b64encode(buf.getvalue()).decode()}}]
    content.append({"type": "text", "text": (
        f"이야기: {story}\n\n위 사진들은 기사 페이지에서 긁어온 것이라 관련 없는 사진(다른 기사 썸네일, 광고, 기자·앵커 얼굴, "
        "이야기와 무관한 정치인·유명인, 로고, 그래픽 배너)이 섞여 있어요. 이 이야기의 사람·동물·장소·장면을 실제로 보여주는 사진 번호만 골라, "
        "표지로 가장 강렬한 것부터 순서대로 JSON 배열로만 답하세요. 예: [3,0,5]. 확실하지 않으면 빼세요.")})
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=120, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": CFG["images"].get("vision_model", "claude-haiku-5-5"), "max_tokens": 200,
                  "messages": [{"role": "user", "content": content}]})
        r.raise_for_status()
        txt = "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
        idx = [int(x) for x in json.loads(_re.search(r"\[[\d,\s]*\]", txt).group(0)) if 0 <= int(x) < len(pool)]
        print("관련 사진:", idx, "/", len(pool))
        return [pool[i] for i in dict.fromkeys(idx)]
    except Exception as e:
        print("사진 관련성 검사 실패(전부 사용 안 함):", e)
        return pool[:1]


def pick_images(slides, outdir, pages=None, publishers=None, story=""):
    """slides마다 사진 파일 경로를 채운다.
    순서: 기사·영상 원본 사진(images.press) → 위키미디어 공개 사진 → AI 생성. 같은 사진은 한 번만."""
    os.makedirs(outdir, exist_ok=True)
    used, credits = set(), []
    pool = press_images(pages or [], outdir) if CFG["images"].get("press", True) else []
    pool = relevant_only(pool, story)
    if len(pool) > 1:  # 표지는 관련 사진 중 해상도가 가장 큰 것(작은 사진을 키우면 흐려짐)
        from PIL import Image as _I
        def _area(p):
            try:
                w, h = _I.open(p[0]).size
                return w * h
            except Exception:
                return 0
        best = max(range(min(len(pool), 6)), key=lambda k: _area(pool[k]))
        pool.insert(0, pool.pop(best))
    names = publishers or {}
    for i, s in enumerate(slides):
        s["image"] = None
        if i == len(slides) - 1 and i > 0 and slides[0].get("image"):
            s["image"] = slides[0]["image"]  # 팔로우 카드는 표지 사진을 어둡게 재사용(사이드바 잡사진 방지)
            continue
        if pool:
            path, src = pool.pop(0)
            s["image"] = path
            credits.append(names.get(src, src))
            continue
        if i > 0:
            continue  # 관련 사진이 없으면 그 장은 빼고 올린다(엉뚱한 사진 금지)
        path = os.path.join(outdir, f"bg{i + 1:02d}.jpg")
        if CFG["images"].get("commons") and s.get("photo_query"):
            try:
                for c in commons_candidates(s["photo_query"]):
                    if c["title"] in used:
                        continue
                    download(c["url"], path)
                    used.add(c["title"])
                    s["image"] = path
                    credits.append(f"{c['artist']}({c['license']})")
                    break
            except Exception as e:
                print("커먼즈 검색 실패:", s["photo_query"], e)
        if not s["image"]:
            try:
                if ai_image(s.get("ai_prompt"), path):
                    s["image"] = path
                    credits.append("AI 생성 이미지")
            except Exception as e:
                print("AI 이미지 오류:", e)
    # 중복 제거한 출처 문구
    seen, uniq = set(), []
    for c in credits:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq
