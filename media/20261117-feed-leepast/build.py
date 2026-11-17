"""더피드 영상 릴스(TTS 없음, 원본 소리): 리트 만점자 과거 인터뷰 발언 모음(2026-11-17).
틀: media/20261115-feed-cheat/build2.py (위 띠 제목 sr.overlay·자막 fl.line 기울임·펀치 전환·마지막 인용 카드)를 그대로 쓰고
내레이션 대신 원본 인터뷰 소리를 깐다. 가로 원본이라 영상은 폭 1080에 맞춰 장면 칸 가운데에 둔다(카드 장면과 같은 자리).
소스(cardnews 저장소 media/): 20261117-leesearch(지금백지연 공개분), 20261117-leepast(미미미누, X @MungmungKi73338),
20261116-kk-leet(DreamSchool 이윤규, lime.now 재게시본), 20261116-leetx(DreamSchool, X @eom0x). 대사는 transcribe(faster-whisper).
실행: python3 media/20261117-feed-leepast/build.py [cardnews 저장소 경로, 기본 /home/user/cardnews]"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

CN = sys.argv[1] if len(sys.argv) > 1 else '/home/user/cardnews'
W, H, BAND = 1080, 1920, 440; VH = H - BAND
T = '/tmp/feedleepast'; os.makedirs(T, exist_ok=True); SFX = os.path.join(ROOT, 'assets', 'sfx')
BJ = f'{CN}/media/20261117-leesearch/video/y1.mp4'; MI = f'{CN}/media/20261117-leepast/video/v1.mp4'
TX = f'{CN}/media/20261116-leetx/video/v1.mp4'; KK = f'{CN}/media/20261116-kk-leet/video/v1.mp4'
NM = f'{CN}/media/20261117-leenamu/video/v1.mp4'
CROP = {BJ: 'crop=810:540:235:0', MI: 'crop=708:472:0:80', TX: 'crop=900:600:360:20',
        KK: 'delogo=x=296:y=424:w=128:h=44,crop=660:440:30:200', NM: 'crop=1180:787:0:390'}  # 박힌 자막·남의 글씨·워터마크 제거
SRCN = {BJ: "영상: 유튜브 '지금백지연'", MI: "영상: 유튜브 '미미미누'", TX: "영상: 유튜브 'DreamSchool'", KK: "영상: 유튜브 'DreamSchool'", NM: "영상: 유튜브 '미미미누'"}
SC = [  # (자막, (원본, 시작, 길이)) — 자막 하나 = 장면 하나
    (["\"디지털 디톡스를", "[하게 된 거죠]\""], (BJ, 21.3, 5.3)),
    (["(패러글라이딩 원리 글을)", "\"[무심코 집어 들었어요]\""], (BJ, 38.9, 2.8)),
    (["\"너무 잘 읽히는 거예요,", "제 [잠재력]을 보게 된 거죠\""], (BJ, 41.7, 3.9)),
    (["\"모든 요소가 [3주 동안]", "완벽하게 지켜졌거든요\""], (BJ, 51.1, 3.9)),
    (["백지연 \"그 시절엔 다들", "[공부를 잘했을까요?]\""], (BJ, 77.0, 5.3)),
    (["\"쉬는 시간에 나가서", "[뛰고 왔어요]\""], (MI, 4.2, 2.3)),
    (["\"근력운동을 하면", "[멘탈이 세지거든요]\""], (MI, 26.0, 2.83)),
    (["\"[나무위키] 켜서 검색하고", "처음부터 끝까지 다 읽어요\""], (NM, 9.0, 4.9)),
    (["\"종이사전 보신 건가요?\"", "\"[네]\""], (KK, 15.0, 2.3)),
    (["\"[종이사전]?", "이거 너무 엉뚱한데\""], (KK, 17.3, 3.7)),
    (["\"답을 바꾼 문제는", "없으셨어요?\""], (TX, 14.4, 2.0)),
    (["\"[23번]이요\"", "\"그게 유일해요?\""], (TX, 16.4, 2.9)),
    (["\"바꿔서 만점 받은 거예요?\"", "\"[네]\""], (TX, 19.3, 1.65)),
    (["그런데 시험지엔", "[25~29번] 연달아 고친 흔적"], ('quote', ["리트 시험지 25~29번", "답을 [연달아 고친 흔적]", "", "본인 해명은", "후반부에 집중력이 떨어져", "[사소한 실수]가 많았다는 것"], 'MBC 보도(11.16)', 3.2)),
]
TITLE = ["리트 만점자 과거 인터뷰", "[모아 보니] ㄷㄷ"]
SFXS = [('chills', 1, -8), ('swoosh_short', 5, -8), ('smack', 9, -7), ('dudung', 13, -6)]  # (효과음, 장면 번호, dB)
PUNCH = "scale={W}:{VH},setsar=1"  # 2026-11-17 사용자 "움직이는 모션 빼줘": 장면 펀치 확대 없음
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30']
AENC = ['-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '160k']


def quote_card(lines, i, label):
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); d = ImageDraw.Draw(bg); fl.W = W
    f = ImageFont.truetype(fl.FM, 64); lh = 92; h = lh * len(lines) + 90
    y0 = (890 - h) // 2 + 30
    d.rounded_rectangle((60, y0, W - 60, y0 + h), 26, fill=(250, 250, 250))
    d.text((W / 2, y0 - 24), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    for k, t in enumerate(lines):
        fl.line(d, t, y0 + 95 + lh * k, f, fg=(20, 20, 22))
    bg.save(f'{T}/q{i}.png'); return f'{T}/q{i}.png'


clips, durs = [], []
for i, (_, sc) in enumerate(SC):
    out = f'{T}/s{i:02d}.mp4'
    if sc[0] == 'quote':
        d = sc[3]; img = quote_card(sc[1], i, sc[2])
        vf = f"scale={W}:{VH},fps=30,setsar=1"  # 카드도 천천히 확대 없음
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-f', 'lavfi', '-t', f'{d:.3f}',
                        '-i', 'anullsrc=r=44100:cl=stereo', '-vf', vf, '-map', '0:v', '-map', '1:a', *ENC, *AENC, '-shortest', out], check=True)
    else:
        src, ss, d = sc
        # 가로 영상: 폭 1080(3:2 → 높이 720)으로 맞춰 장면 칸(890px 안쪽 카드 자리) 가운데, 바탕은 카드 장면과 같은 짙은 회색
        vf = (f"{CROP[src]},scale={W}:720:flags=lanczos,setsar=1,pad={W}:{VH}:0:105:color=0x18181c,fps=30,{PUNCH.format(W=W, VH=VH)}")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-t', f'{d:.3f}', '-i', src, '-vf', vf,
                        '-af', f'afade=t=in:d=0.04,afade=t=out:st={d - 0.06:.3f}:d=0.06', *ENC, *AENC, out], check=True)
    clips.append(out); durs.append(d)
starts = [sum(durs[:i]) for i in range(len(durs))]; TOTAL = sum(durs); ends = starts[1:] + [TOTAL]
open(f'{T}/list.txt', 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{T}/list.txt', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', f'{T}/body.mp4'], check=True)

sr.overlay(TITLE, f'{T}/top.png', size=72)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sc[0] != 'quote':
        d.text((W - 40, 500), SRCN[sc[0]], font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255), anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    y = 1471 - 100 * (len(rows) - 1) / 2 + 28
    for k, r in enumerate(rows):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fl.W = W
        yy = y + 100 * k; fl.line(ImageDraw.Draw(lay), r, yy, fb, stroke=9, sf=(0, 0, 0))
        yc = yy - fb.size * 0.35
        im.alpha_composite(lay.transform((W, H), Image.AFFINE, (1, sr.SHEAR, -sr.SHEAR * yc, 0, 1, 0), Image.BICUBIC))
    p = f'{T}/cap{i}.png'; im.save(p); caps.append(p)

inputs = ['-i', f'{T}/body.mp4', '-i', f'{T}/top.png'] + sum((['-i', p] for p in caps), [])
# 바탕은 body 영상 자체를 pad로 키워 만든다(color 소스 위 overlay는 첫 프레임이 비어 깜박임, 2026-11-17)
fc = f'[0:v]pad={W}:{H}:0:{BAND}:color=0x08080a[s0];[s0][1:v]overlay=0:0[s1]'
last = 's1'
for i in range(len(SC)):
    a = 0 if i == 0 else starts[i] - 0.02; b = ends[i] - 0.02
    fc += f";[{last}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{i}]"; last = f'c{i}'
fc += f";[{last}]setsar=1,format=yuv420p[vout]"  # 첫 화면 흔들림 없음
n0 = 2 + len(SC)
ains = sum((['-i', f'{SFX}/{n}.mp3'] for n, _, _ in SFXS), [])
fc += ';[0:a]loudnorm=I=-16:TP=-1.5[orig]'
for k, (n, sci, db) in enumerate(SFXS):
    ms = int(max(0, starts[sci] - 0.05) * 1000); fc += f';[{n0 + k}:a]adelay={ms}|{ms},volume={db}dB[x{k}]'
fc += ';[orig]' + ''.join(f'[x{k}]' for k in range(len(SFXS))) + f'amix=inputs={1 + len(SFXS)}:normalize=0,alimiter=limit=0.95,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
