"""더피드 숏츠형 릴스: 과학 일타강사 윤도영 'AI 부정행위' 입장 → 대통령 향해 한마디(2026-11-17). 틀: media/20261115-feed-cheat/build2.py 그대로.
소스: src/v1.mp4(유튜브 윤도영통합과학시스템 'AI 부정행위에 대해' 2026-11-16, cardnews 맥북 도우미 720p), src/yt.jpg(X @donstop4886 유튜브 화면 캡처).
내레이션 tts/ (Gemini TTS Fenrir, cardnews state/tts_test/gemini_Fenrir_yoondy_0.mp3, 1.2배속·문장별 자름)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/feedyoondy'; os.makedirs(T, exist_ok=True); SRC = os.path.join(HERE, 'src'); SFX = os.path.join(ROOT, 'assets', 'sfx')
SC = [  # (화면 자막, 장면)
    (["수능 사흘 앞", "과학 일타강사 [입장 발표]"], ('card', 'yt.jpg', '유튜브 윤도영통합과학시스템')),
    (["윤도영 강사의", "[첫마디]는"], ('vid', 4.5, 'wide')),
    (["처벌이 약하니", "[시도 안 할 이유 없다]"], ('vid', 86.5, 'wide')),
    (["걸려도 손해가 적다", "[기댓값이 양수]"], ('quote', ["성공하면 의대, 일생 보장", "실패해도 처벌은 [솜방망이]", "", "수학으로 말하면", "[기댓값이 양수]"], '윤도영 강사 발언')),
    (["과학 기술로 생긴 문제는", "[과학 기술로 막아야]"], ('vid', 103.5, 'wide')),
    (["[수능 연기] 주장에 대해"], ('vid', 181.5, 'wide')),
    (["확실한 방안 있다면", "[연기도 고려]할 만"], ('vid', 189, 'wide')),
    (["3월 입학 지키려면", "[최대 2주]가 한계"], ('quote', ["내년 3월 입학 전제로", "일정을 역산하면", "", "아무리 길어도 [2주일]", "그 이상은 [3월 입학 불가]"], '윤도영 강사 발언')),
    (["그리고", "[대통령]을 향해"], ('vid', 378.5, 'wide')),
    (["\"얼마나 심각하게 보는지", "[의구심이 든다]\""], ('quote', ["대통령이 이 사안을", "얼마나 심각하게 보고 있느냐", "에 대해서는", "조금 [의구심이 듭니다]"], '윤도영 강사 발언')),
    (["대책을", "[대통령이 직접] 밝혀라"], ('vid', 424, 'wide')),
    (["교육부는", "[수능 연기 없다]"], ('vid', 502, 'wide')),
    (["이대로 수능", "[괜찮을까요?]"], ('vid', 590, 'wide')),
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

PUNCH = "scale=w='2*trunc(540*max(1,1+0.07*exp(-t*14)))':h=-2:eval=frame,crop={W}:{VH},setsar=1"
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
        vf = f'crop=540:720:430:0,scale={W}:{VH}:flags=lanczos,fps=30,{PUNCH.format(W=W, VH=VH)}'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sc[1]), '-t', f'{d:.3f}', '-i', f'{SRC}/v1.mp4', '-vf', vf, *ENC, out], check=True)
    else:
        img = (f'{SRC}/{sc[1]}' if sc[0] == 'img' else quote_card(sc[1], i, sc[2]) if sc[0] == 'quote'
               else card(sc[1], sc[2], i) if sc[0] == 'card' else comment_card(sc[1], i))
        if sc[0] == 'img':
            im = Image.open(img).convert('RGB'); r = max(W / im.width, VH / im.height)
            im = im.resize((int(im.width * r), int(im.height * r))); x = (im.width - W) // 2
            im.crop((x, 0, x + W, VH)).save(f'{T}/i{i}.png'); img = f'{T}/i{i}.png'
        vf = (f"scale=2160:-1,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{VH}:fps=30,"
              f"{PUNCH.format(W=W, VH=VH)}")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-vf', vf, *ENC, out], check=True)
    clips.append(out)
lst = f'{T}/list.txt'; open(lst, 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-t', f'{TOTAL:.3f}', *ENC, f'{T}/body.mp4'], check=True)

# 겹칠 그림: 제목 띠(기울임) + 문장별 자막 띠
sr.overlay(["수능 사흘 앞 일타강사", "[대통령 향해 한마디] ㄷㄷ"], f'{T}/top.png', size=72)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sc[0] == 'vid':
        d.text((W - 40, 500), "영상: 유튜브 '윤도영통합과학시스템'", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
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
fc = f'color=c=0x08080a:s={W}x{H}:r=30:d={TOTAL:.3f}[bg];[bg][0:v]overlay=0:{BAND}:shortest=1[s0];[s0][1:v]overlay=0:0[s1]'
last = 's1'
for i in range(len(SC)):
    a = 0 if i == 0 else starts[i] - 0.02; b = ends[i] - 0.02
    fc += f";[{last}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{i}]"; last = f'c{i}'
fc += f";[{last}]scale=w='2*trunc(540*max(1,1+0.18*exp(-t*8)*cos(t*20)))':h=-2:eval=frame,crop={W}:{H},setsar=1,format=yuv420p[vout]"
n0 = 2 + len(SC); N = len(SC)
SFXS = [('dudung', 3, -6), ('swoosh_short', 5, -8), ('swish', 8, -8), ('smack', 9, -7)]
ains = sum((['-i', f] for f in TTS), []) + sum((['-i', f'{SFX}/{n}.mp3'] for n, _, _ in SFXS), [])
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
for k, (n, sci, db) in enumerate(SFXS):
    ms = int(max(0, starts[sci] - 0.05) * 1000); fc += f';[{n0 + N + k}:a]adelay={ms}|{ms},volume={db}dB[x{k}]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + ''.join(f'[x{k}]' for k in range(len(SFXS))) + f'amix=inputs={N + len(SFXS)}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
