"""폴리티커 게시 명령어:
  python -m cardnews.main tick                           승인 확인, 시간 되면 게시, 만료 처리
  python -m cardnews.main watch                          대기 게시물이 끝날 때까지 1분마다 tick
  python -m cardnews.main publish --id 20261019-lunch    수동 즉시 게시(승인 무시)
  python -m cardnews.main chat-id                        텔레그램 채팅방 ID 확인(설치용)
  python -m cardnews.main refresh-token                  인스타 토큰 갱신(새 토큰 출력)
  python -m cardnews.main ping                           텔레그램 연결 테스트
소재 조사·원고는 채팅에서 만든다(drafts/current.json → manual-draft 워크플로). Claude API는 쓰지 않는다.
"""
import argparse
import datetime as dt
import os
import shutil
import subprocess
import re
import time
import traceback

from . import instagram, telegram_bot as tg
from .common import CFG, MEDIA, all_posts, load_post, now, save_post

SLOT_LABEL = {"lunch": "점심", "evening": "저녁"}


TIP_RE = re.compile(r"\s*[(\[]?[^()\[\],]*텔레그램[^()\[\],]*[)\]]?")


def clean_credit(c):
    """캡션·화면 출처에서 '텔레그램 제보' 표기를 뺀다(사용자 결정 2026-10-21)."""
    return TIP_RE.sub("", c or "").strip(" ,·:")


def build_caption(d, credits):
    parts = [d["caption"].strip()]
    credits = [c for c in (clean_credit(c) for c in credits) if c]
    srcs = [s for s in d.get("sources", []) if "텔레그램" not in s.get("publisher", "") and "t.me/" not in s.get("url", "")]
    src = ", ".join(f"{s.get('publisher', '')} {s.get('date', '')}".strip() for s in srcs[:3])
    notes = ([f"출처: {src}"] if src else []) + (["사진·영상: " + ", ".join(credits[:6])] if credits else [])
    if notes:
        parts.append("\n".join(notes))
    tags = [h.lstrip("#") for h in d.get("hashtags", []) if h][:5]  # 인스타 해시태그 상한 5개
    if tags:
        parts.append(" ".join("#" + h for h in tags))
    return "\n\n".join(parts)


def media_url(pid, fname):
    base = os.environ.get("MEDIA_BASE_URL")
    if not base:
        repo = os.environ.get("GITHUB_REPOSITORY")
        branch = os.environ.get("GITHUB_REF_NAME", "main")
        base = f"https://raw.githubusercontent.com/{repo}/{branch}/media"
    return f"{base.rstrip('/')}/{pid}/{fname}"


def _git(*a):
    return subprocess.run(["git", *a], cwd=str(MEDIA.parent), capture_output=True, text=True)


def push_media(post):
    """게시 직전에 파일이 GitHub에 올라가 있는지 확인(인스타가 공개 주소에서 가져가므로)."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    _git("add", "-A", str(MEDIA / post["id"]))
    if _git("diff", "--cached", "--quiet").returncode != 0:
        _git("-c", "user.name=politea-bot", "-c", "user.email=politea-bot@users.noreply.github.com",
             "commit", "-m", f"politea: media {post['id']}")
        _git("pull", "--rebase", "origin", os.environ.get("GITHUB_REF_NAME", "main"))
        r = _git("push")
        print("미디어 업로드:", r.returncode, r.stderr[-200:])
        time.sleep(20)


def _remote_status(pid):
    """GitHub 최신 main에 기록된 이 게시물의 상태(오래된 체크아웃으로 중복 게시하는 것 방지)."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return None
    import json
    br = os.environ.get("GITHUB_REF_NAME", "main")
    _git("fetch", "-q", "origin", br)
    r = _git("show", f"origin/{br}:state/posts/{pid}.json")
    try:
        return json.loads(r.stdout).get("status") if r.returncode == 0 else None
    except Exception:
        return None


def _claim(post):
    """게시 직전에 '게시 중'으로 표시해 올린다. 다른 실행이 먼저 잡았으면 False."""
    st = _remote_status(post["id"])
    if st in ("publishing", "published"):
        print(f"{post['id']}: 이미 {st} 상태라 건너뜀(중복 게시 방지)")
        post["status"] = st
        return False
    if not os.environ.get("GITHUB_ACTIONS"):
        return True
    post["status"] = "publishing"
    save_post(post)
    _git("add", f"state/posts/{post['id']}.json")
    _git("-c", "user.name=politea-bot", "-c", "user.email=politea-bot@users.noreply.github.com",
         "commit", "-m", f"politea: publishing {post['id']}")
    _git("pull", "--rebase", "--autostash", "origin", os.environ.get("GITHUB_REF_NAME", "main"))
    if _git("push").returncode != 0:
        print(f"{post['id']}: 게시 중 표시를 올리지 못해 이번엔 건너뜀")
        _git("rebase", "--abort")
        return False
    return True


def do_publish(post, force=False):
    if not force and not _claim(post):
        return
    push_media(post)
    urls = [media_url(post["id"], os.path.basename(f)) for f in post["files"]]
    try:
        if post.get("format") == "reel":
            cover = media_url(post["id"], os.path.basename(post["cover"])) if post.get("cover") else None
            mid, link = instagram.publish_reel(urls[0], post["caption_full"], share_to_feed=True, cover_url=cover)
            post.update(status="published", ig_media_id=mid, permalink=link, published_at=now().isoformat())
            tg.send_text(f"🎬 릴스 게시 완료: {post['topic']}\n{link}\n\n🎵 음악은 앱에서 릴스 수정으로 넣을 수 있어요(원본 소리 릴스는 생략).")
        else:
            mid, link = instagram.publish_carousel(urls, post["caption_full"])
            post.update(status="published", ig_media_id=mid, permalink=link, published_at=now().isoformat())
            tg.send_text(f"🎉 게시 완료: {post['topic']}\n{link}\n\n📲 스토리 공유: 링크 열기 → 종이비행기 → '스토리에 추가'")
    except Exception as e:
        post.update(status="failed", error=str(e)[:500])
        if "2207051" in str(e):
            tg.send_text(f"⚠️ 게시 확인 필요: {post['topic']}\n인스타가 '차단' 응답(2207051)을 보냈고, 최근 게시물에서도 찾지 못했어요. "
                         "앱에서 실제로 올라갔는지 확인해주세요. 다시 올리면 중복될 수 있어요.")
        else:
            tg.send_text(f"⚠️ 게시 실패: {post['topic']}\n{str(e)[:500]}\n\nGitHub Actions 로그를 확인해주세요.")
    save_post(post)


def tick():
    for pid, act in tg.poll_decisions():
        p = load_post(pid)
        if not p or p["status"] != "pending" or act not in ("ok", "no"):
            continue
        p["status"] = "approved" if act == "ok" else "rejected"
        p["decided_at"] = now().isoformat()
        save_post(p)
        if act == "ok":
            at = dt.datetime.fromisoformat(p["publish_at"])
            tg.send_text(f"✅ 승인됨: {p['topic']}\n" + ("곧 게시해요" if now() >= at else f"{at:%m/%d %H:%M}에 게시돼요"))
        else:
            tg.send_text(f"❌ 거절됨: {p['topic']} (게시하지 않아요)")
    exp = dt.timedelta(hours=CFG["approval"]["expire_hours"])
    for p in all_posts():
        if p["status"] not in ("pending", "approved"):
            continue
        at = dt.datetime.fromisoformat(p["publish_at"])
        if p["status"] == "approved" and now() >= at:
            do_publish(p)
        elif p["status"] == "pending" and now() > at + exp:
            p["status"] = "expired"
            save_post(p)
            tg.send_text(f"⌛ 승인 시간이 지나 게시하지 않았어요: {p['topic']}")


def sync_repo():
    """GitHub Actions에서: 상태 변경을 커밋하고 최신 main을 받아온 뒤 올린다."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    _git("config", "user.name", "politea-bot")
    _git("config", "user.email", "politea-bot@users.noreply.github.com")
    _git("add", "-A", "state", "media")
    if _git("diff", "--cached", "--quiet").returncode != 0:
        _git("commit", "-m", f"politea: watch sync {now():%H%M}")
    r = _git("pull", "--rebase", "--autostash", "origin", os.environ.get("GITHUB_REF_NAME", "main"))
    if r.returncode != 0:
        print("동기화 실패:", r.stderr[-300:])
        _git("rebase", "--abort")
        return
    _git("push")


def watch(hours=6):
    """GitHub 예약 실행이 자주 밀려서, 대기 중인 게시물이 끝날 때까지 1분마다 직접 확인한다."""
    end = now() + dt.timedelta(hours=hours)
    while now() < end:
        sync_repo()
        try:
            tick()
        except Exception:
            traceback.print_exc()
        if not any(p["status"] in ("pending", "approved") for p in all_posts()):
            print("대기 중인 게시물 없음, 종료")
            return
        time.sleep(60)


def prune(days=7):
    """게시·거절·만료된 지 오래된 미디어 폴더 정리(저장소 용량 관리)."""
    cut = now() - dt.timedelta(days=days)
    for p in all_posts():
        try:
            if dt.datetime.fromisoformat(p["created_at"]) < cut and p["status"] in ("published", "rejected", "expired", "failed"):
                shutil.rmtree(MEDIA / p["id"], ignore_errors=True)
        except Exception:
            pass


def chat_id_helper():
    me = tg._api("getMe")
    print("연결된 봇:", "@" + me.get("username", ""), me.get("first_name", ""))
    seen = {}
    for u in tg._api("getUpdates"):
        c = (u.get("message") or {}).get("chat") or {}
        if c:
            seen[c["id"]] = c.get("username") or c.get("title") or c.get("first_name")
    print(seen or "봇에게 먼저 아무 메시지나 보낸 뒤 다시 실행하세요.")
    if seen:
        tg_text = "\n".join(f"{k} ({v})" for k, v in seen.items())
        print("TELEGRAM_CHAT_ID 후보:\n" + tg_text)


def check():
    """인스타 토큰·계정 확인(게시하지 않음) 후 결과를 텔레그램으로."""
    try:
        me = instagram._req("GET", "me", fields="user_id,username,account_type,media_count")
        msg = (f"✅ 인스타 연결 확인: @{me.get('username')} ({me.get('account_type')}) "
               f"게시물 {me.get('media_count', 0)}개\nIG_USER_ID 일치: {str(me.get('user_id')) == os.environ.get('IG_USER_ID')}")
    except Exception as e:
        msg = f"⚠️ 인스타 연결 실패: {str(e)[:400]}"
    print(msg)
    tg.send_text(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tick", "watch", "publish", "chat-id", "refresh-token", "prune", "ping", "check"])
    ap.add_argument("--id")
    a = ap.parse_args()
    if a.cmd == "watch":
        watch()
    elif a.cmd == "tick":
        sync_repo()  # 예약 실행은 예전 커밋으로 시작할 수 있어서 최신 상태부터 받는다
        tick()
        prune()
    elif a.cmd == "publish":
        do_publish(load_post(a.id), force=True)
    elif a.cmd == "chat-id":
        chat_id_helper()
    elif a.cmd == "refresh-token":
        print(instagram.refresh_token())
    elif a.cmd == "prune":
        prune()
    elif a.cmd == "check":
        check()
    elif a.cmd == "ping":
        tg.send_text("✅ 폴리티커 자동화 연결 테스트 성공!\nGitHub Actions → 텔레그램 연결이 잘 됐어요.")


if __name__ == "__main__":
    main()
