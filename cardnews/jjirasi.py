"""텔레그램 공개 채널(기본 @koreajjirasi)에서 반응 좋은 사진·영상 글을 골라 후보로 모은다.

  python -m cardnews.jjirasi scan      채널 미리보기(t.me/s/…)를 읽어 후보 상위 N개를 내려받고
                                       state/jjirasi/candidates.json + media/<id>/ 에 저장
  python -m cardnews.jjirasi seen ID…  이미 쓴(또는 버린) 글 번호를 기록해 다음 후보에서 뺀다

후보 고르기·문구 작성·안전 판단은 채팅(예약 작업)의 Claude가 하고, 게시는 기존 텔레그램 승인 흐름을 탄다.
Claude API는 쓰지 않는다.
"""
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys

import requests
from bs4 import BeautifulSoup

from .common import MEDIA, STATE, now
from .images import BROWSER_UA

CHANNEL = os.environ.get("JJ_CHANNEL", "koreajjirasi")
DIR = STATE / "jjirasi"
SEEN = DIR / "seen.json"
CANDS = DIR / "candidates.json"
BAD_REACTIONS = {"🖕"}


def _num(s):
    s = (s or "").strip().upper().replace(",", "")
    m = re.match(r"([\d.]+)\s*([KM]?)", s)
    if not m:
        return 0
    return int(float(m.group(1)) * {"": 1, "K": 1000, "M": 1000000}[m.group(2)])


def _dur(s):
    p = [int(x) for x in re.findall(r"\d+", s or "")]
    sec = 0
    for x in p:
        sec = sec * 60 + x
    return sec


def _bg_url(style):
    m = re.search(r"background-image:\s*url\(['\"]?([^'\")]+)", style or "")
    return m.group(1) if m else None


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for m in soup.select("div.tgme_widget_message[data-post]"):
        post = m["data-post"]  # koreajjirasi/124
        num = int(post.rsplit("/", 1)[1])
        t = m.select_one("time[datetime]")
        when = dt.datetime.fromisoformat(t["datetime"]) if t else None
        txt = m.select_one(".tgme_widget_message_text")
        text = txt.get_text("\n", strip=True) if txt else ""
        vw = m.select_one(".tgme_widget_message_views")
        views = _num(vw.get_text() if vw else "")
        reacts = {}
        for r in m.select(".tgme_reaction"):
            emo = r.select_one("b")
            e = emo.get_text(strip=True) if emo else "?"
            cnt = r.get_text("", strip=True)
            if e != "?":
                cnt = cnt.replace(e, "", 1)
            reacts[e] = reacts.get(e, 0) + _num(cnt)
        photos = [u for u in (_bg_url(a.get("style")) for a in m.select("a.tgme_widget_message_photo_wrap")) if u]
        videos, too_big = [], False
        for v in m.select("video"):
            if v.get("src"):
                videos.append(v["src"])
        for d in m.select(".tgme_widget_message_video_player, .tgme_widget_message_roundvideo_player"):
            if "not_supported" in " ".join(d.get("class", [])) or "too big" in d.get_text(" ").lower():
                too_big = True
        durs = [_dur(x.get_text()) for x in m.select(".message_video_duration")]
        link = m.select_one("a.tgme_widget_message_link_preview")
        out.append({"num": num, "url": f"https://t.me/{post}", "date": when.isoformat() if when else None,
                    "text": text[:1500], "views": views, "reactions": reacts,
                    "photos": photos, "videos": videos, "durations": durs, "too_big": too_big,
                    "link": link.get("href") if link else None})
    return out


def fetch(pages=3):
    """최신 글부터 pages 쪽(쪽당 약 20개) 읽는다."""
    posts, before = {}, None
    for _ in range(pages):
        url = f"https://t.me/s/{CHANNEL}" + (f"?before={before}" if before else "")
        r = requests.get(url, headers=BROWSER_UA, timeout=40)
        r.raise_for_status()
        got = parse(r.text)
        if not got:
            break
        for p in got:
            posts[p["num"]] = p
        before = min(p["num"] for p in got)
    return sorted(posts.values(), key=lambda p: p["num"])


def merge_albums(posts):
    """미리보기에서 앨범(사진 여러 장)은 한 글 블록에 같이 나오므로 그대로 쓴다."""
    return [{**p, "nums": [p["num"]]} for p in posts]


def score(p):
    good = sum(v for k, v in p["reactions"].items() if k not in BAD_REACTIONS)
    age_h = 1.0
    if p["date"]:
        age_h = max(1.0, (now() - dt.datetime.fromisoformat(p["date"])).total_seconds() / 3600)
    # 반응 1개 ≈ 조회 40회. 오래된 글일수록 조회가 쌓이므로 나이로 나눠 '속도'를 본다.
    return round((p["views"] + 40 * good) / math.sqrt(age_h + 2), 1)


def _get(url, path):
    r = requests.get(url, headers={**BROWSER_UA, "Referer": "https://t.me/"}, timeout=120)
    r.raise_for_status()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(r.content)
    return path


def _probe(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", path], capture_output=True, text=True).stdout
    try:
        j = json.loads(o)
        s = j["streams"][0]
        return {"w": s["width"], "h": s["height"], "dur": round(float(j["format"]["duration"]), 1)}
    except Exception:
        return {}


def download(c):
    """후보 하나의 사진·영상을 media/<id>/ 에 받는다. 사진=cand/tgNN.jpg, 영상=video/vN.mp4 + 장면 모아보기."""
    base = MEDIA / c["id"]
    files = {"photos": [], "videos": []}
    for k, u in enumerate(c["photos"], 1):
        try:
            files["photos"].append(os.path.relpath(_get(u, str(base / "cand" / f"tg{k:02d}.jpg")), base))
        except Exception as e:
            print("사진 실패", c["url"], e)
    for k, u in enumerate(c["videos"], 1):
        try:
            p = _get(u, str(base / "video" / f"v{k}.mp4"))
            info = _probe(p)
            sheet = str(base / "video" / f"v{k}_sheet.jpg")
            step = max(1.0, (info.get("dur") or 10) / 12)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-vf",
                            f"fps=1/{step},scale=320:-2,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontcolor=yellow:fontsize=18:box=1:boxcolor=black@0.5,tile=4x3",
                            "-frames:v", "1", "-q:v", "4", sheet])
            files["videos"].append({"src": os.path.relpath(p, base), **info,
                                    "sheet": os.path.relpath(sheet, base) if os.path.exists(sheet) else None})
        except Exception as e:
            print("영상 실패", c["url"], e)
    return files


def load_seen():
    return set(json.loads(SEEN.read_text())) if SEEN.exists() else set()


def save_seen(s):
    DIR.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(sorted(s)))


def scan(top=4, hours=36):
    seen = load_seen()
    posts = merge_albums(fetch())
    cut = now() - dt.timedelta(hours=hours)
    pool = []
    for p in posts:
        if set(p["nums"]) & seen or not (p["photos"] or p["videos"]):
            continue
        if p["date"] and dt.datetime.fromisoformat(p["date"]) < cut:
            continue
        if p["too_big"] and not p["videos"] and not p["photos"]:
            continue
        p["score"] = score(p)
        pool.append(p)
    pool.sort(key=lambda p: -p["score"])
    # 지난 후보 폴더 정리(게시 대기에 올라간 것은 state/posts 쪽에서 관리되므로 jj- 후보만)
    keep = {f"{now():%Y%m%d}-jj{p['num']}" for p in pool[:top]}
    for d in MEDIA.glob("*-jj*"):
        if d.name not in keep and not (STATE / "posts" / f"{d.name}.json").exists():
            subprocess.run(["rm", "-rf", str(d)])
    cands = []
    for p in pool[:top]:
        c = {**p, "id": f"{now():%Y%m%d}-jj{p['num']}"}
        c["files"] = download(c)
        if c["files"]["photos"] or c["files"]["videos"]:
            cands.append(c)
    DIR.mkdir(parents=True, exist_ok=True)
    CANDS.write_text(json.dumps({"scanned_at": now().isoformat(), "channel": CHANNEL,
                                 "total_posts": len(posts), "candidates": cands}, ensure_ascii=False, indent=1))
    print(f"글 {len(posts)}개 중 후보 {len(cands)}개")
    for c in cands:
        print(c["score"], c["url"], c["views"], c["reactions"], len(c["photos"]), "사진", len(c["videos"]), "영상", c["text"][:40])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        scan()
    elif cmd == "seen":
        s = load_seen()
        s |= {int(x) for x in sys.argv[2:]}
        save_seen(s)
        print("기록:", sys.argv[2:])
