"""더피드 TTS형 릴스: 수능 부정 신고 포상금 1억, 수험생 커뮤니티 반응은 싸늘(찬반). feed-sagal/build.py(=build2.py) 복사본(SC·TTS·제목·효과음만 교체).
움직임 효과 없음(2026-11-17 사용자). 사진: cardnews media/20261118-feed-reward/cand press01·press13(대통령 수능 비상 점검회의). 인용은 조선일보 11.18·매일경제 11.17 기사 문장."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/feedreward'; os.makedirs(T, exist_ok=True); SRC = os.path.join(HERE, 'src'); SFX = os.path.join(ROOT, 'assets', 'sfx')
SC = [  # (화면 자막, 장면)
    (["수능 부정행위 신고하면", "[포상금 1억 원]"], ('img', 'press01.jpg')),
    (["대통령이 수능 이틀 전", "[직접 지시]"], ('img', 'press13.jpg')),
    (["가담 인원만큼", "포상금 [더 얹어준다]"], ('quote', ["부정 한 건당", "[1억 원 이상] 포상", "인원수만큼 추가"], '대통령 지시 내용 (11.17)')),
    (["함께 하다 신고하면", "[처벌도 감면]"], ('quote', ["함께 부정행위 하다", "신고한 사람은", "[처벌 감면]"], '대통령 지시 내용 (11.17)')),
    (["감독관만으론", "[막기 어렵다]는 이유"], ('quote', ["감독관 역량에만", "의존하기엔", "[한계가 있다]"], '정부 설명 (매일경제 11.17)')),
    (["그런데 수험생 커뮤니티", "[반응은 달랐다]"], ('img', 'press01.jpg')),
    (["\"내가 [마녀사냥] 당할까", "걱정된다\""], ('quote', ["포상금 1억원?", "내가 다른 학생에게", "[마녀 사냥] 당할까 걱정된다"], '수험생·학부모 커뮤니티 (조선일보 11.18)')),
    (["\"전 국민을", "[1억 수능 파파라치]로\""], ('quote', ["지금까지 손 놓고 있다가", "이제 와서 전 국민을", "[1억 수능 파파라치]로"], '수험생·학부모 커뮤니티 (조선일보 11.18)')),
    (["시험 보는 수험생이", "[감독까지] 해야 할까"], ('img', 'press13.jpg')),
    (["기준과 근거는", "[아직 안 나왔다]"], ('quote', ["포상금 지급 기준", "법적 근거", "[아직 미발표]"], '11.18 현재 검토 지시 단계')),
    (["1억 포상금", "[찬성] vs [반대]"], ('img', 'press01.jpg')),
]
TTS = [os.path.join(HERE, 'tts', f'l{i:02d}.wav') for i in range(1, 12)]  # Gemini Fenrir(한 번에 생성 후 문장별로 자름, 1.2배속)
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

PUNCH = "setsar=1"  # 2026-11-17 사용자: 릴스는 움직임·깜박임 없이(컷만)
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', '-an']


def quote_card(lines, i, label):
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


def comment_card(name, box, label, i):
    c = Image.open(f'{SRC}/{name}').convert('RGB').crop(box)
    s = 1000 / c.width; c = c.resize((1000, int(c.height * s)), Image.LANCZOS)
    if c.height > 780:
        c = c.resize((int(c.width * 780 / c.height), 780), Image.LANCZOS)
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); y = (890 - c.height) // 2 + 25
    bg.paste(c, ((W - c.width) // 2, y)); d = ImageDraw.Draw(bg)
    d.text((W / 2, y - 26), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
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
               else card(sc[1], sc[2], i) if sc[0] == 'card' else comment_card(sc[1], sc[2], sc[3], i))
        if sc[0] == 'img':
            im = Image.open(img).convert('RGB'); r = max(W / im.width, VH / im.height)
            im = im.resize((int(im.width * r), int(im.height * r))); x = (im.width - W) // 2
            yy = (im.height - VH) // 2; im.crop((x, yy, x + W, yy + VH)).save(f'{T}/i{i}.png'); img = f'{T}/i{i}.png'
        vf = f"scale={W}:{VH},fps=30,{PUNCH}"
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-vf', vf, *ENC, out], check=True)
    clips.append(out)
lst = f'{T}/list.txt'; open(lst, 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-t', f'{TOTAL:.3f}', *ENC, f'{T}/body.mp4'], check=True)

# 겹칠 그림: 제목 띠(기울임) + 문장별 자막 띠
sr.overlay(["수능 부정 신고 포상금 1억", "[수험생 반응은 싸늘] ㄷㄷ"], f'{T}/top.png', size=80)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sc[0] == 'img':
        d.text((W - 40, 500), "사진: 수능 비상 점검회의 (11.17)", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
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
fc += f";[{last}]setsar=1,format=yuv420p[vout]"
n0 = 2 + len(SC); N = len(SC)
ains = sum((['-i', f] for f in TTS), []) + ['-i', f'{SFX}/dudung.mp3', '-i', f'{SFX}/huh.mp3', '-i', f'{SFX}/tiring.mp3']
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
w5 = int(starts[5] * 1000); b9 = int(starts[9] * 1000)  # dudung=첫 장면, huh=반응 전환, tiring=기준 미발표
fc += f';[{n0 + N}:a]volume=-7dB[x1];[{n0 + N + 1}:a]adelay={w5}|{w5},volume=-8dB[x2];[{n0 + N + 2}:a]adelay={b9}|{b9},volume=-8dB[x3]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + f'[x1][x2][x3]amix=inputs={N + 3}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
