"""텔레그램으로 미리보기를 보내고 승인/거절 버튼 응답을 받아온다(getUpdates 폴링)."""
import json

import requests

from .common import env, read_text, write_text


def _api(method, files=None, **data):
    url = f"https://api.telegram.org/bot{env('TELEGRAM_BOT_TOKEN')}/{method}"
    r = requests.post(url, data=data, files=files, timeout=120)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"텔레그램 {method} 실패: {j}")
    return j["result"]


def chat_id():
    return env("TELEGRAM_CHAT_ID")


def send_text(text, buttons=None, reply_to=None):
    data = {"chat_id": chat_id(), "text": text[:4000], "disable_web_page_preview": "true"}
    if buttons:
        data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    if reply_to:
        data["reply_to_message_id"] = reply_to
    return _api("sendMessage", **data)


def send_album(paths):
    media, files = [], {}
    for i, p in enumerate(paths[:10]):
        key = f"f{i}"
        files[key] = open(p, "rb")
        media.append({"type": "video" if str(p).lower().endswith(".mp4") else "photo", "media": f"attach://{key}"})
    try:
        return _api("sendMediaGroup", files=files, chat_id=chat_id(), media=json.dumps(media))
    finally:
        for f in files.values():
            f.close()


def send_photo(path, caption=""):
    with open(path, "rb") as f:
        return _api("sendPhoto", files={"photo": f}, chat_id=chat_id(), caption=caption[:1000])


def send_video(path, caption=""):
    with open(path, "rb") as f:
        return _api("sendVideo", files={"video": f}, chat_id=chat_id(), caption=caption[:1000],
                    supports_streaming="true", width=1080, height=1920)


def send_document(path, caption=""):
    with open(path, "rb") as f:
        return _api("sendDocument", files={"document": f}, chat_id=chat_id(), caption=caption[:1000])


def send_preview(post, cover=None):
    files = [str(f) for f in post["files"]]
    if len(files) == 1 and files[0].lower().endswith(".mp4"):
        send_video(files[0], "🎬 릴스 미리보기")
        if cover:
            send_photo(cover, "🖼 릴스 커버")
    else:
        send_album(files)
    when = post["publish_at"][5:16].replace("T", " ")
    src = "\n".join(f"- {s.get('publisher', '')} {s.get('date', '')} {s.get('url', '')}" for s in post["sources"])
    risk = f"\n⚠️ 확인할 점: {post['risk']}" if post.get("risk") else ""
    kind = "릴스" if post.get("format") == "reel" else "카드뉴스"
    state = "✅ 이미 승인됨(예약)" if post.get("status") == "approved" else "승인하면 그 시각에 게시돼요. (이미 지났으면 바로 게시)"
    text = (f"🟣 [폴리티커 {kind} · {when} 게시 예정] {post['topic']}\n"
            f"분야: {post.get('category', '')} · 핵심: {post.get('core', '')}{risk}\n\n"
            f"──── 게시물 본문 ────\n{post['caption_full']}\n\n출처 확인:\n{src}\n\n{state}")
    msg = send_text(text, buttons=[[{"text": "✅ 승인", "callback_data": f"ok:{post['id']}"},
                                    {"text": "❌ 거절", "callback_data": f"no:{post['id']}"}]])
    send_text(post["caption_full"])  # 본문만 단독 메시지(앱에서 직접 올릴 때 길게 눌러 복사)
    return msg["message_id"]


def poll_decisions():
    """새 버튼 응답을 [(post_id, 'ok'|'no')]로 반환. 등록된 채팅방 외의 응답은 무시."""
    offset = int(read_text("telegram_offset.txt", "0") or 0)
    ups = _api("getUpdates", offset=offset + 1 if offset else 0, timeout=0,
               allowed_updates=json.dumps(["callback_query", "message"]))
    out = []
    for u in ups:
        offset = max(offset, u["update_id"])
        cq = u.get("callback_query")
        if not cq:
            continue
        if str(cq.get("message", {}).get("chat", {}).get("id")) != str(chat_id()):
            continue
        try:
            act, pid = cq["data"].split(":", 1)
        except ValueError:
            continue
        out.append((pid, act))
        try:
            _api("answerCallbackQuery", callback_query_id=cq["id"],
                 text={"ok": "승인했어요. 게시 시각에 올라가요.", "no": "거절했어요."}.get(act, ""))
        except Exception:
            pass
    write_text("telegram_offset.txt", offset)
    return out
