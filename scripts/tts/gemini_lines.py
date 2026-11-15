"""drafts/gemini_tts.json {"out":"media/<id>/gtts","voice":"Sadaltager","style":"...","lines":[...]} → <out>/l01.wav …
키는 GEMINI_API_KEY 환경변수(저장소 Secrets)에서만 읽고 로그에 찍지 않는다. 오늘의쓸모 scripts/tts_test/gemini_tts.py 방식."""
import base64, json, os, sys, time, requests
c = json.load(open("drafts/gemini_tts.json")); key = os.environ.get("GEMINI_API_KEY", "").strip()
if not key:
    print("GEMINI_API_KEY 없음"); sys.exit(1)
URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
os.makedirs(c["out"], exist_ok=True)
for i, t in enumerate(c["lines"], 1):
    content = {"type": "text", "text": t}
    if c.get("style"):
        content["annotations"] = [{"type": "speech_metadata", "style": c["style"]}]
    body = {"model": c.get("model", "gemini-3.8-flash-tts"), "input": [{"type": "user_input", "content": [content]}],
            "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": c.get("voice", "Sadaltager")}]}}
    for a in range(4):
        r = requests.post(URL, json=body, headers={"x-goog-api-key": key}, timeout=120)
        if r.status_code == 200:
            break
        print(i, "HTTP", r.status_code, r.text[:300]); time.sleep(6 * (a + 1))
    else:
        sys.exit(1)
    data = next((x["data"] for s in r.json().get("steps", []) for x in (s.get("content") or []) if x.get("data")), None)
    if not data:
        print(i, "오디오 없음"); sys.exit(1)
    open(f'{c["out"]}/l{i:02d}.wav', "wb").write(base64.b64decode(data)); print(i, "ok")
