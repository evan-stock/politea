# 폴리티커(@politea.kr) 게시 자동화

정치·사회·경제 카드뉴스(캐러셀)와 릴스를 채팅에서 만들고, GitHub Actions가 렌더 → 텔레그램 승인 → 인스타 자동 게시까지 처리합니다. 컴퓨터를 켜 두지 않아도 되고, Claude API 비용은 들지 않습니다.

## 흐름
1. 채팅에서 소재 조사·원고 작성 → `drafts/current.json` push
2. `manual-draft` 워크플로가 렌더(카드 `media/<id>/01.jpg…` 또는 릴스 `reel.mp4` + `reel_cover.jpg`)
3. `"mode":"send"`면 텔레그램으로 미리보기 + [✅ 승인] [❌ 거절] 버튼
4. 승인하면 게시 시각에 `pipeline` 워크플로(watch)가 인스타에 게시하고 링크를 텔레그램으로 보냄

## 원고 형식 (drafts/current.json, 여러 개면 목록)
카드뉴스:
```json
{"id": "20261019-coin", "slot": "evening", "mode": "collect | render | send",
 "topic": "코인 과세 또 유예", "category": "경제", "core": "한 줄 핵심", "risk": "확인할 점",
 "image_pages": ["기사 주소"], "images": ["press03", "https://...jpg", null],
 "slides": [
   {"t": "코인 과세 또 미룬다?\n'2030 투자자'만 헷갈린다", "fx": 0.5, "fy": 0.35,
    "bubble": {"text": "또 유예?", "x": 0.6, "y": 0.3}},
   {"sub": "정부가 밝힌 '시행 시점'", "t": "2027년 1월, 이번엔 진짜?", "b": "본문 2~4문장"},
   {"t": "", "b": ""}
 ],
 "caption": "[대괄호 제목]\n\n본문…", "hashtags": ["코인과세"],
 "sources": [{"publisher": "연합뉴스", "date": "2026.10.19", "url": "https://..."}],
 "photo_credits": ["연합뉴스"],
 "publish_at": "2026-10-19T21:00:00+09:00", "approved": false, "publish_now": false}
```
- 0번 장 = 표지, 마지막 장 = 공유·팔로우 카드(글이 비면 기본 문구), 사이 = 안쪽 장.
- `'작은따옴표'`로 감싼 말은 강조(표지는 보라 띠, 안쪽은 색 강조).
- 사진이 없는 장은 검정 타이포 카드로 렌더됩니다.
- 영상 장: 슬라이드에 `"video": {"src": "video/v1.mp4", "start": 0, "dur": 10}`.

릴스:
```json
{"id": "20261019-protest", "format": "reel", "slot": "evening", "mode": "send",
 "topic": "…", "title": "시위대로부터 도망치는 경찰\n통제 불능 상태 '프랑스'", "credit": "영상: KBS",
 "video": {"src": "video/v1.mp4", "start": 3, "dur": 30, "frame": 2, "audio": true, "crop": [0, 0, 1280, 640]},
 "caption": "…", "hashtags": [], "sources": [], "photo_credits": ["KBS"]}
```
영상은 `drafts/video.json`(`{"id": "...", "urls": ["유튜브·X·틱톡·mp4 주소"], "frames": 2}`)을 push하면 `fetch-video`가 `media/<id>/video/`에 받아 둡니다(frames를 주면 장면 모아보기만 만들고 영상은 지움).

## 명령 (Actions → politea → Run workflow)
- `ping` 텔레그램 연결 테스트 · `chat-id` 채팅방 ID 확인 · `tick` 승인 반영 · `watch` 대기 게시물 감시 · `publish` (id 입력) 즉시 게시

## 필요한 Secrets (Settings → Secrets and variables → Actions → New repository secret)
| Name | 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather가 준 새 봇 토큰 |
| `TELEGRAM_CHAT_ID` | `chat-id` 명령으로 확인한 숫자 |
| `IG_USER_ID` | @politea.kr 인스타 사용자 ID |
| `IG_ACCESS_TOKEN` | @politea.kr 인스타 장기 토큰(60일, 매달 1·15일 자동 갱신) |
| `GH_PAT` | 이 저장소 Secrets 읽기·쓰기 권한 토큰(토큰 자동 갱신용) |

## 디자인
- 브랜드: 검정 + 흰 굵은 제목 + 보라(#7C4DFF)·연보라(#B9A3FF) 강조, POLITEA.KR 로고
- 글꼴: Pretendard(OFL), Archivo Black(OFL) — `assets/fonts`
- 렌더러: `cardnews/render.py`(카드), `cardnews/reel.py`(릴스)
