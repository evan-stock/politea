"""더피드 TTS형 릴스: 세무사 수석 AI 부정행위 자백 → '사이비' 취급받던 강성태 재평가. 한 문장 = 한 장면.
참고: 유튜브 쇼츠 '이슈냥'(구성), X @kingwest0219(소재). 소스: video/v1.mp4(이돈호 변호사 영상 인스타 릴스, 오늘의쓸모 fetch),
video/img*.(기사 사진·유튜브 캡처). 내레이션 tts/ (Gemini TTS Fenrir, 1.2배속). build2.py(세무사 펨코 편) 틀 그대로."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/kangbuild'; os.makedirs(T, exist_ok=True); SRC = os.path.join(HERE, 'video'); SFX = os.path.join(ROOT, 'assets', 'sfx')
YT = "영상: 유튜브 '이돈호 변호사'"
SC = [  # (화면 자막, 장면, 출처)
    (["세무사 시험 수석", "[AI 부정행위] 자백"], ('vid', 39), YT),
    (["그런데 뜻밖의", "[이 사람]이 소환됐다"], ('img', 'img1.png', 0.35), "사진: MBN '동치미'(2019)"),
    (["'공부의 신'", "[강성태]"], ('img', 'img9.jpg', 0.55), "사진: 유튜브 '공부의신 강성태'"),
    (["2년 전 갑자기", "[공부의 시대는 끝났다]"], ('card', 'img2.png', "'공부의신 강성태' 채널 · 2년 전 영상들"), ""),
    (["인간 뇌에", "[AI를 심어야] 한다"], ('quote', ["AI에 지배받지 않으려면", "인간 뇌에", "[AI를 심어야] 한다"], "2024년 강성태 영상 속 주장 (언론 보도)"), ""),
    (["반응은", "[싸늘]"], ('quote', ["\"교회 [간증 타임] 같다\""], "2024년 당시 누리꾼 반응 (뉴시스 보도)"), ""),
    (["연관검색어에", "[사이비 종교·정신병]"], ('quote', ["강성태 연관검색어", "", "[사이비 종교]", "[정신병]"], "강성태 본인 발언 (11월 14일 영상)"), ""),
    (["그런데 지금", "[그 말이 현실로]"], ('img', 'img3.png', 0.5), "사진: 유튜브 '공부의신 강성태'"),
    (["토익·국가자격시험", "[AI 안경 커닝] 적발"], ('img', 'img7.jpg', 0.42), "사진: 연합뉴스"),
    (["결국 세무사 수석까지", "[AI로 부정 합격]"], ('vid', 58), YT),
    (["어제 새 영상에서", "[강성태의 경고]"], ('img', 'img6.jpg', 0.5), "사진: 유튜브 '공부의신 강성태'"),
    (["\"안 걸린 건 [수십 배]\"", "\"이미 [부정 합격자] 있다\""], ('img', 'img3.png', 0.5, 'zoom'), "사진: 유튜브 '공부의신 강성태'"),
    (["\"이번 수능에서도", "[부정행위 일어난다]\""], ('img', 'img6.jpg', 0.5, 'zoom'), "사진: 유튜브 '공부의신 강성태'"),
    (["수능은 [이번 주 목요일]", "[막을 수 있을까?]"], ('img', 'img8.jpg', 0.5), "사진: 뉴스1"),
]
N = len(SC)
TTS = [os.path.join(HERE, 'tts', f'l{i:02d}.wav') for i in range(1, N + 1)]


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
TOTAL = t + 0.6
ends = starts[1:] + [TOTAL]; seg = [ends[i] - (starts[i] if i else 0) for i in range(N)]

PUNCH = "scale=w='2*trunc(540*max(1,1+0.07*exp(-t*14)))':h=-2:eval=frame,crop={W}:{VH},setsar=1"
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', '-an']
DARK = (24, 24, 28)


def quote_card(lines, label, i):
    bg = Image.new('RGB', (W, VH), DARK); d = ImageDraw.Draw(bg); fl.W = W
    f = ImageFont.truetype(fl.F, 76); lh = 108; h = lh * len(lines) + 100
    y0 = (900 - h) // 2 + 40
    d.rounded_rectangle((60, y0, W - 60, y0 + h), 26, fill=(250, 250, 250))
    d.text((W / 2, y0 - 24), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    for k, t in enumerate(lines):
        if t:
            fl.line(d, t, y0 + 108 + lh * k, f, fg=(20, 20, 22))
    p = f'{T}/q{i}.png'; bg.save(p); return p


def card(name, label, i):
    c = Image.open(f'{SRC}/{name}').convert('RGB'); s = 1000 / c.width; c = c.resize((1000, int(c.height * s)), Image.LANCZOS)
    bg = Image.new('RGB', (W, VH), DARK); y = (900 - c.height) // 2 + 30
    m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c.width - 1, c.height - 1), 22, fill=255)
    bg.paste(c, ((W - c.width) // 2, y), m); d = ImageDraw.Draw(bg)
    d.text((W / 2, y - 24), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    p = f'{T}/k{i}.png'; bg.save(p); return p


def photo(name, fx, i, zoom=False):  # 화면 꽉 채우기(가로 위치 fx), zoom이면 얼굴 쪽으로 더 당김
    im = Image.open(f'{SRC}/{name}').convert('RGB'); r = max(W / im.width, VH / im.height) * (1.25 if zoom else 1)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x = int(min(max(im.width * fx - W / 2, 0), im.width - W)); y = int((im.height - VH) * (0.2 if zoom else 0.5))
    p = f'{T}/i{i}.png'; im.crop((x, y, x + W, y + VH)).save(p); return p


clips = []
for i, (_, sc, _c) in enumerate(SC):
    out = f'{T}/s{i:02d}.mp4'; d = seg[i] + 0.05
    if sc[0] == 'vid':  # 원본 박힌 자막·알약 자리만 흐림
        vf = (f'crop=563:770:78:375,scale={W}:{VH}:flags=lanczos,fps=30,split[m][b];[b]crop={W}:290:0:885,boxblur=22:2[bl];[m][bl]overlay=0:885,'
              f'{PUNCH.format(W=W, VH=VH)}')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sc[1]), '-t', f'{d:.3f}', '-i', f'{SRC}/v1.mp4', '-filter_complex', vf, *ENC, out], check=True)
    else:
        img = (photo(sc[1], sc[2], i, len(sc) > 3) if sc[0] == 'img' else quote_card(sc[1], sc[2], i) if sc[0] == 'quote'
               else card(sc[1], sc[2], i))
        vf = (f"scale=2160:-1,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{VH}:fps=30,"
              f"{PUNCH.format(W=W, VH=VH)}")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-vf', vf, *ENC, out], check=True)
    clips.append(out)
lst = f'{T}/list.txt'; open(lst, 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-t', f'{TOTAL:.3f}', *ENC, f'{T}/body.mp4'], check=True)

sr.overlay(["사이비 취급받던 강성태", "[지금 재평가 중] ㄷㄷ"], f'{T}/top.png', size=80)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc, cr) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if cr:
        d.text((W - 40, 500), cr, font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
               anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    y = 1471 - 100 * (len(rows) - 1) / 2 + 28
    for k, r in enumerate(rows):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fl.W = W
        yy = y + 100 * k; fl.line(ImageDraw.Draw(lay), r, yy, fb, stroke=9, sf=(0, 0, 0))
        yc = yy - fb.size * 0.35
        im.alpha_composite(lay.transform((W, H), Image.AFFINE, (1, sr.SHEAR, -sr.SHEAR * yc, 0, 1, 0), Image.BICUBIC))
    p = f'{T}/cap{i}.png'; im.save(p); caps.append(p)

inputs = ['-i', f'{T}/body.mp4', '-i', f'{T}/top.png'] + sum((['-i', p] for p in caps), [])
fc = f'color=c=0x08080a:s={W}x{H}:r=30:d={TOTAL:.3f}[bg];[bg][0:v]overlay=0:{BAND}:shortest=1[s0];[s0][1:v]overlay=0:0[s1]'
last = 's1'
for i in range(N):
    a = 0 if i == 0 else starts[i] - 0.02; b = ends[i] - 0.02
    fc += f";[{last}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{i}]"; last = f'c{i}'
fc += f";[{last}]scale=w='2*trunc(540*max(1,1+0.18*exp(-t*8)*cos(t*20)))':h=-2:eval=frame,crop={W}:{H},setsar=1,format=yuv420p[vout]"
n0 = 2 + N
ains = sum((['-i', f] for f in TTS), []) + ['-i', f'{SFX}/boom.mp3', '-i', f'{SFX}/whoosh2.mp3', '-i', f'{SFX}/boom.mp3']
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
w2 = int((starts[7] - 0.3) * 1000); b2 = int((starts[9] - 0.05) * 1000)  # 2막(그런데 지금) whoosh, '결국 세무사 수석까지' boom
fc += f';[{n0 + N}:a]volume=1.3[x1];[{n0 + N + 1}:a]adelay={w2}|{w2},volume=1.1[x2];[{n0 + N + 2}:a]adelay={b2}|{b2},volume=1.2[x3]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + f'[x1][x2][x3]amix=inputs={N + 3}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(starts[2] + 0.5), '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
