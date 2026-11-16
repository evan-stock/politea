"""더피드 TTS형 릴스: 6개월 전 세무사 갤러리 '왜 갑자기 다들 잘해졌지?' → 수석 AI 부정행위 자백. build2.py 복사본(SC·TTS·제목만 교체).
소스: /tmp/zzsrc/v1.mp4(이돈호 변호사 유튜브 쇼츠, cardnews media/20261115-brk/video), p1_1·p1_2.jpg(X @zzal_cat 게시 세무사 갤러리 캡처)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/zz2'; os.makedirs(T, exist_ok=True); SRC = '/tmp/zzsrc'; SFX = os.path.join(ROOT, 'assets', 'sfx')
k = 2.05  # 캡처 화면좌표 → 원본
SC = [  # (화면 자막, 장면)
    (["올해 5월 세무사 갤러리", "\"왜 갑자기 [다들 잘해졌지?]\""], ('cmt', 'p1_1.jpg', (0, 0, 2652, round(560*k)), '세무사 갤러리 캡처 (2026.05.28)')),
    (["합격 난이도가", "[코스피처럼] 폭등"], ('quote', ["합격 체감난이도가", "불과 [2~3년만에]", "코스피마냥 급상승"], '세무사 갤러리 원문')),
    (["새로 온 수험생들", "다 [허수]인 줄 알았는데"], ('quote', ["진입하는 인간들", "다 [허수]라며", "정신승리했잖아"], '세무사 갤러리 원문')),
    (["\"고이다 못해", "[석유]가 되었다\" ㅋㅋ"], ('cmt', 'p1_2.jpg', (0, round(190*k), 3151, round(860*k)), '댓글 캡처')),
    (["결론: 새로 온 사람들이", "[괴수]였다"], ('quote', ["까고보니", "원래 하던놈들보다", "[괴수]들이었다 이거네?"], '댓글 원문')),
    (["그리고 6개월 뒤", "올해 [세무사 수석]이"], ('vid', 16.8, 'wide')),
    (["[AI 부정행위]", "직접 자백"], ('vid', 118, 'wide')),
    (["초소형 카메라로 찍고", "[AI]로 답 받았다"], ('vid', 40, 'wide')),
    (["그것도 모르고", "다들 [자기 탓]만 ㅠㅠ"], ('quote', ["매일 진입글 5개씩", "올라오는거 볼 때마다", "[솔직히 섬뜩했어]"], '세무사 갤러리 원문')),
    (["여러분이라면", "[눈치챘을까요?]"], ('vid', 166, 'wide')),
]
TTS = [os.path.join(HERE, 'tts', f'l{i:02d}.wav') for i in range(1, 11)]  # Gemini Fenrir(한 번에 생성 후 문장별로 자름, 1.2배속)
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
            im.crop((x, 0, x + W, VH)).save(f'{T}/i{i}.png'); img = f'{T}/i{i}.png'
        vf = (f"scale=2160:-1,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{VH}:fps=30,"
              f"{PUNCH.format(W=W, VH=VH)}")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-vf', vf, *ENC, out], check=True)
    clips.append(out)
lst = f'{T}/list.txt'; open(lst, 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-t', f'{TOTAL:.3f}', *ENC, f'{T}/body.mp4'], check=True)

# 겹칠 그림: 제목 띠(기울임) + 문장별 자막 띠
sr.overlay(["6개월 전 세무사 갤러리", "[너무 순수했다] ㅠㅠ"], f'{T}/top.png', size=80)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sc[0] == 'vid':
        d.text((W - 40, 500), "영상: 유튜브 '이돈호 변호사'", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
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
ains = sum((['-i', f] for f in TTS), []) + ['-i', f'{SFX}/boom.mp3', '-i', f'{SFX}/whoosh2.mp3', '-i', f'{SFX}/boom.mp3']
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
w5 = int((starts[5] - 0.3) * 1000); b9 = int((starts[6] - 0.05) * 1000)
fc += f';[{n0 + N}:a]volume=1.3[x1];[{n0 + N + 1}:a]adelay={w5}|{w5},volume=1.1[x2];[{n0 + N + 2}:a]adelay={b9}|{b9},volume=1.2[x3]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + f'[x1][x2][x3]amix=inputs={N + 3}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
