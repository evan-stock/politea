"""더피드 TTS 릴스: 교육부 장관 "제 나이가 있어서 그런지 저는 못 할 것 같다" 종합(2026-11-18).
틀: media/20261115-feed-cheat/build2.py (위 띠 제목·기울임 자막·quote 카드). 원본 영상 없음(맥북 꺼짐) → 기사 사진 + 인용 카드.
움직임 없음(사용자 11/17: 더피드 모션 빼기), 바탕은 pad(깜박임 방지). 내레이션 tts/ (Gemini Fenrir, 1.2배속 후 문장별 자름).
사실: 세계일보·디지털타임스·서울신문·데일리안(11.17), JTBC(차관 참석), 총리 담화·대통령 X(11.17)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/feedchoigj'; os.makedirs(T, exist_ok=True); SRC = os.path.join(HERE, 'src'); SFX = os.path.join(ROOT, 'assets', 'sfx')
SC = [  # (화면 자막, 장면) — 한 문장 = 한 장면
    (["AI 커닝 [100%]", "잡을 수 있냐는 질문에"], ('img', 'minister_assembly.jpg', (.75, .5))),
    (["교육부 장관의", "[대답은]"], ('img', 'minister_kim.jpg', (.8, .4))),
    (["\"저는 [못 할 것] 같다\""], ('quote', ["\"제 [나이가 있어서]", "그런지,", "저는 [못 할 것] 같다\""], '최교진 교육부 장관 · 국회 교육위원회')),
    (["16일 [국회 교육위원회]", "에서 나온 말"], ('img', 'minister_assembly.jpg', (.85, .5))),
    (["[여당 대표]마저", "\"우려 자아내는 장면\""], ('img', 'kim.jpg', (.5, .4))),
    (["\"[빨리 정정]했어야\""], ('quote', ["\"우려를 자아내는", "장면이었다\"", "", "\"[빨리 정정]했어야", "했다\""], '김민석 더불어민주당 대표')),
    (["교육부 해명은", "\"감독관 고충에 [공감]\""], ('quote', ["수능 현장 감독관들의", "어려움에 [공감]을", "표현한 것"], '교육부 해명')),
    (["다음 날엔", "[직무유기] 고발까지"], ('quote', ["직무유기 혐의로", "[서울경찰청]에 고발"], '이종배 전 서울시의원(국민의힘) · 11.17')),
    (["그런데 그날", "[총리 대국민 담화] 자리엔"], ('img', 'pm_speech.jpg', (.55, .35))),
    (["장관 대신", "[차관]이 나왔다"], ('quote', ["담화 자리엔", "교육부 [차관]이 왔고", "장관은 [참석하지 않았다]"], 'JTBC 보도 · 11.17')),
    (["총리는 [퇴학]에", "[10년] 입학 금지"], ('img', 'pm.jpg', (.5, .35))),
    (["대통령은", "신고 포상금 [1억 이상]"], ('img', 'president.jpg', (.5, .2))),
    (["장관은 못 잡는다는데", "수능은 [바로 내일]"], ('img', 'exam.jpg', (.5, .5))),
]
TTS = [os.path.join(HERE, 'tts', f'l{i:02d}.wav') for i in range(1, 14)]  # Gemini Fenrir(한 번에 생성 후 문장별로 자름, 1.2배속)
def trim(f, k):  # 문장 앞뒤 무음 잘라 텀 줄이기
    o = f'{T}/t{k:02d}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-af',
                    'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.02',
                    o], check=True); return o
TTS = [trim(f, k) for k, f in enumerate(TTS)]
dur = [float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                            capture_output=True, text=True).stdout) for f in TTS]
starts = []; t = INTRO
for d in dur:
    starts.append(t); t += d + GAP
TOTAL = t + 0.5
ends = starts[1:] + [TOTAL]; seg = [ends[i] - (starts[i] if i else 0) for i in range(len(SC))]  # 첫 장면은 0초부터

PUNCH = "scale={W}:{VH},setsar=1"  # 움직임 없음
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', '-an']


def quote_card(lines, i, label='펨코 댓글 원문'):
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); d = ImageDraw.Draw(bg); fl.W = W
    f = ImageFont.truetype(fl.FM, 64); lh = 92; h = lh * len(lines) + 90
    y0 = (890 - h) // 2 + 30
    d.rounded_rectangle((60, y0, W - 60, y0 + h), 26, fill=(250, 250, 250))
    d.text((W / 2, y0 - 24), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    for k, t in enumerate(lines):
        fl.line(d, t, y0 + 95 + lh * k, f, fg=(20, 20, 22))
    bg.save(f'{T}/q{i}.png'); return f'{T}/q{i}.png'


def card(name, label, i):
    c = Image.open(f'{SRC}/{name}').convert('RGB'); s = 1000 / c.width; c = c.resize((1000, int(c.height * s)), Image.LANCZOS)
    if c.height > 780:
        c = c.resize((int(c.width * 780 / c.height), 780), Image.LANCZOS)
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); y = (890 - c.height) // 2 + 25
    m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c.width - 1, c.height - 1), 22, fill=255)
    bg.paste(c, ((W - c.width) // 2, y), m); d = ImageDraw.Draw(bg)
    d.text((W / 2, y - 24), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    bg.save(f'{T}/k{i}.png'); return f'{T}/k{i}.png'


def comment_card(box, i):
    c = Image.open(f'{SRC}/fm_comment.png').convert('RGB').crop(box)
    s = 1000 / c.width; c = c.resize((1000, int(c.height * s)), Image.LANCZOS)
    if c.height > 780:
        c = c.resize((int(c.width * 780 / c.height), 780), Image.LANCZOS)
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); y = (890 - c.height) // 2 + 25
    bg.paste(c, ((W - c.width) // 2, y)); d = ImageDraw.Draw(bg)
    d.text((W / 2, y - 26), '펨코 댓글 캡처', font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    if box[1] > 18:  # 확대 장면엔 빨간 테두리
        d.rectangle(((W - c.width) // 2 - 8, y - 8, (W + c.width) // 2 + 8, y + c.height + 8), outline=fl.RED, width=6)
    bg.save(f'{T}/c{i}.png'); return f'{T}/c{i}.png'


clips = []
for i, (_, sc) in enumerate(SC):
    out = f'{T}/s{i:02d}.mp4'; d = seg[i] + 0.05
    if sc[0] == 'vid':
        crop = 'crop=563:770:78:375' if sc[2] == 'wide' else 'crop=430:588:145:400'
        vf = (f'{crop},scale={W}:{VH}:flags=lanczos,fps=30,split[m][b];[b]crop={W}:290:0:885,boxblur=22:2[bl];[m][bl]overlay=0:885,'
              f'{PUNCH.format(W=W, VH=VH)}')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sc[1]), '-t', f'{d:.3f}', '-i', f'{SRC}/v1.mp4', '-filter_complex', vf, *ENC, out], check=True)
    else:
        img = (f'{SRC}/{sc[1]}' if sc[0] == 'img' else quote_card(sc[1], i, sc[2]) if sc[0] == 'quote'
               else card(sc[1], sc[2], i) if sc[0] == 'card' else comment_card(sc[1], i))
        if sc[0] == 'img':
            ImageOps.fit(Image.open(img).convert('RGB'), (W, VH), Image.LANCZOS, centering=sc[2]).save(f'{T}/i{i}.png'); img = f'{T}/i{i}.png'
        vf = f"scale={W}:{VH},fps=30,setsar=1"  # 천천히 확대 없음
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-vf', vf, *ENC, out], check=True)
    clips.append(out)
lst = f'{T}/list.txt'; open(lst, 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-t', f'{TOTAL:.3f}', *ENC, f'{T}/body.mp4'], check=True)

# 겹칠 그림: 제목 띠(기울임) + 문장별 자막 띠
sr.overlay(["교육부 장관 \"AI 커닝", "[못 잡을 것 같다]\" ㄷㄷ"], f'{T}/top.png', size=72)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sc[0] == 'img':
        d.text((W - 40, 500), "사진: 보도사진", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
               anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    y = 1471 - 100 * (len(rows) - 1) / 2 + 28
    for k, r in enumerate(rows):  # 자막도 기울임(제목과 같은 0.2)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fl.W = W
        yy = y + 100 * k; fl.line(ImageDraw.Draw(lay), r, yy, fb, stroke=9, sf=(0, 0, 0))
        yc = yy - fb.size * 0.35
        im.alpha_composite(lay.transform((W, H), Image.AFFINE, (1, sr.SHEAR, -sr.SHEAR * yc, 0, 1, 0), Image.BICUBIC))
    d = ImageDraw.Draw(im)
    p = f'{T}/cap{i}.png'; im.save(p); caps.append(p)

inputs = ['-i', f'{T}/body.mp4', '-i', f'{T}/top.png'] + sum((['-i', p] for p in caps), [])
fc = f'[0:v]pad={W}:{H}:0:{BAND}:color=0x08080a[s0];[s0][1:v]overlay=0:0[s1]'  # pad 바탕(깜박임 방지)
last = 's1'
for i in range(len(SC)):
    a = 0 if i == 0 else starts[i] - 0.02; b = ends[i] - 0.02
    fc += f";[{last}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{i}]"; last = f'c{i}'
fc += f";[{last}]setsar=1,format=yuv420p[vout]"
n0 = 2 + len(SC); N = len(SC)
SFXS = [('dudung', 2, -8), ('huh', 4, -9), ('buzz_wrong', 7, -9), ('chills', 8, -8), ('swoosh_short', 10, -9), ('dudung', 12, -8)]  # (효과음, 장면, dB)
ains = sum((['-i', f] for f in TTS), []) + sum((['-i', f'{SFX}/{n}.mp3'] for n, _, _ in SFXS), [])
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
for k, (n, sci, db) in enumerate(SFXS):
    ms = int(max(0, starts[sci] - 0.05) * 1000); fc += f';[{n0 + N + k}:a]adelay={ms}|{ms},volume={db}dB[x{k}]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + ''.join(f'[x{k}]' for k in range(len(SFXS))) + f'amix=inputs={N + len(SFXS)}:normalize=0,alimiter=limit=0.95,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
