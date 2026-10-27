"""인스타그램 API(Instagram 로그인 방식)로 캐러셀 게시."""
import time

import requests

from .common import CFG, env


_ACCT = None  # None = 오늘의쓸모(기본), "furball" = 오늘의 털뭉치 → IG_ACCESS_TOKEN_FURBALL / IG_USER_ID_FURBALL


def use(account=None):
    """이후 호출을 어느 인스타 계정으로 할지 정한다."""
    global _ACCT
    _ACCT = account


def _sfx():
    return f"_{_ACCT.upper()}" if _ACCT else ""


def configured(account):
    import os
    sfx = f"_{account.upper()}" if account else ""
    return bool(os.environ.get("IG_ACCESS_TOKEN" + sfx) and os.environ.get("IG_USER_ID" + sfx))


def _base():
    return f"{CFG['instagram']['api_host']}/{CFG['instagram']['api_version']}"


def _req(method, path, **params):
    r = requests.request(method, f"{_base()}/{path}", timeout=120,
                         headers={"Authorization": f"Bearer {env('IG_ACCESS_TOKEN' + _sfx())}"},
                         **({"json": params} if method == "POST" else {"params": params}))
    j = r.json()
    if r.status_code != 200 or "error" in j:
        raise RuntimeError(f"인스타 API 오류 {r.status_code}: {j}")
    return j


def _wait_ready(cid, tries=10):
    for _ in range(tries):
        st = _req("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"컨테이너 {cid} 상태 {st}")
        time.sleep(30)
    raise RuntimeError(f"컨테이너 {cid} 준비 시간 초과")


def _publish(cid, tries=6):
    """media_publish. '아직 준비 안 됨'(2207027) 오류는 잠시 뒤 다시 시도."""
    ig = env("IG_USER_ID" + _sfx())
    for k in range(tries):
        try:
            return _req("POST", f"{ig}/media_publish", creation_id=cid)["id"]
        except RuntimeError as e:
            if "2207027" not in str(e) or k == tries - 1:
                raise
            time.sleep(20)


def _norm(s):
    return " ".join((s or "").split())[:80]


def _find_recent(caption, since):
    """최근 게시물 중 같은 캡션으로 since(유닉스 초) 이후 올라간 것을 찾는다. (id, permalink) 또는 None."""
    import datetime as _dt
    ig = env("IG_USER_ID" + _sfx())
    want = _norm(caption[:2200])
    for wait in (15, 45, 90):
        time.sleep(wait)
        try:
            items = _req("GET", f"{ig}/media", fields="id,caption,timestamp,permalink", limit=5).get("data", [])
        except Exception as e:
            print("게시 확인 조회 실패:", str(e)[:200])
            continue
        for m in items:
            try:
                ts = _dt.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
            except Exception:
                ts = since
            if ts >= since - 300 and _norm(m.get("caption")) == want:
                return m["id"], m.get("permalink", "")
    return None


def _publish_checked(cid, caption, since):
    """media_publish 후 오류가 나도 실제로 올라갔으면 성공으로 본다.
    인스타가 게시는 해 놓고 403(code 4, 2207051 'action is blocked')을 돌려주는 경우가 있어서."""
    try:
        mid = _publish(cid)
    except RuntimeError as e:
        found = _find_recent(caption, since)
        if found:
            print(f"media_publish 오류가 났지만 실제로 게시됨({found[0]}): {str(e)[:200]}")
            return found
        raise
    link = ""
    try:
        link = _req("GET", mid, fields="permalink").get("permalink", "")
    except Exception:
        pass
    return mid, link


def publish_carousel(image_urls, caption):
    ig = env("IG_USER_ID" + _sfx())
    since = time.time()
    children = []
    for u in image_urls[:10]:
        if u.lower().endswith(".mp4"):
            children.append(_req("POST", f"{ig}/media", media_type="VIDEO", video_url=u, is_carousel_item=True)["id"])
        else:
            children.append(_req("POST", f"{ig}/media", image_url=u, is_carousel_item=True)["id"])
    for c in children:
        _wait_ready(c)
    car = _req("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(children), caption=caption[:2200])["id"]
    _wait_ready(car)
    time.sleep(10)
    return _publish_checked(car, caption, since)


def publish_reel(video_url, caption, share_to_feed=False, cover_url=None):
    """9:16 mp4 를 릴스로 게시. cover_url 이 있으면 그 이미지를 커버로."""
    ig = env("IG_USER_ID" + _sfx())
    extra = {"cover_url": cover_url} if cover_url else {}
    since = time.time()
    cid = _req("POST", f"{ig}/media", media_type="REELS", video_url=video_url,
               caption=caption[:2200], share_to_feed=share_to_feed, **extra)["id"]
    _wait_ready(cid, tries=20)
    return _publish_checked(cid, caption, since)


def publish_story(image_url):
    """이미지 스토리 게시(스티커·링크는 API로 붙일 수 없음)."""
    ig = env("IG_USER_ID" + _sfx())
    cid = _req("POST", f"{ig}/media", media_type="STORIES", image_url=image_url)["id"]
    _wait_ready(cid)
    return _publish(cid)


def refresh_token(account=None):
    """장기 토큰(60일) 갱신. 새 토큰 문자열 반환. account 가 있으면 그 계정 토큰."""
    use(account)
    r = requests.get(f"{CFG['instagram']['api_host']}/refresh_access_token", timeout=60,
                     params={"grant_type": "ig_refresh_token", "access_token": env("IG_ACCESS_TOKEN" + _sfx())})
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"토큰 갱신 실패: {j}")
    return j["access_token"]
