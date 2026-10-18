"""설정, 시간, 상태 파일 등 공통 유틸."""
import datetime as dt
import json
import os
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
POSTS = STATE / "posts"
MEDIA = ROOT / "media"


def load_config():
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = load_config()
TZ = ZoneInfo(CFG.get("timezone", "Asia/Seoul"))


def now():
    return dt.datetime.now(TZ)


def env(name, required=True, default=None):
    v = os.environ.get(name, default)
    if required and not v:
        raise SystemExit(f"환경변수 {name} 가 없어요. GitHub 저장소 Settings → Secrets 에 추가해주세요.")
    return v


def slot_time(slot, day=None):
    """해당 슬롯의 게시 시각(오늘 기준)."""
    day = day or now().date()
    hh, mm = map(int, CFG["slots"][slot]["publish_at"].split(":"))
    return dt.datetime.combine(day, dt.time(hh, mm), tzinfo=TZ)


def new_post_id(slot):
    return now().strftime("%Y%m%d") + "-" + slot


def load_post(pid):
    p = POSTS / f"{pid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save_post(post):
    POSTS.mkdir(parents=True, exist_ok=True)
    (POSTS / f"{post['id']}.json").write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding="utf-8")


def all_posts():
    POSTS.mkdir(parents=True, exist_ok=True)
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(POSTS.glob("*.json"))]


def recent_topics(days):
    cut = now() - dt.timedelta(days=days)
    out = []
    for p in all_posts():
        try:
            if dt.datetime.fromisoformat(p["created_at"]) >= cut and p.get("topic"):
                out.append(p["topic"])
        except Exception:
            pass
    return out


def read_text(path, default=""):
    p = STATE / path
    return p.read_text(encoding="utf-8").strip() if p.exists() else default


def write_text(path, text):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / path).write_text(str(text), encoding="utf-8")


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()
