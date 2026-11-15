"""더피드 숏츠형 릴스 v2: 세무사 수석 자수 → '그 방법, 펨코 댓글에 이미 있었다'. 한 문장 = 한 장면(빠른 전환).
소스: /tmp/taxsrc/v1.mp4(이돈호 변호사 유튜브 쇼츠, 오늘의쓸모 media/20261115-brk/video), note_cover.jpg(블로그 사진·모자이크),
fm_comment.png(커뮤니티 댓글 캡처). 내레이션 tts2/ (edge-tts 인준 +70% 속도, +25Hz)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/cheat2'; os.makedirs(T, exist_ok=True); SRC = '/tmp/taxsrc'; SFX = os.path.join(ROOT, 'assets', 'sfx')
SC = [  # (화면 자막, 장면)
    (["세무사 시험 수석", "결국 [경찰 자수]"], ('vid', 16.8, 'wide')),
    (["160문제 중 [159개] 정답", "'AI 안경' 의혹 받던 사람"], ('img', 'note_cover.jpg')),
    (["안경이 아니라", "[초소형 카메라]"], ('vid', 40, 'wide')),
    (["찍어서 [AI]로 보내고", "답은 [스마트폰]으로"], ('vid', 60, 'wide')),
    (["그런데 이 방법", "이미 [펨코]에 있었다"], ('cmt', (18, 18, 630, 478))),
    (["셔츠 단추에 [초소형 카메라]", "귀에는 [초소형 이어폰]"], ('quote', ["초소형카메라(wifi됨)", "[셔츠단추] 뚫어서 달고", "초소형이어폰(쌀알만함)", "[귀속]에 넣은 다음에"])),
    (["사진 찍으면 [AI가 풀고]", "이어폰으로 [정답]"], ('quote', ["5초마다 사진찍어서", "[ai가 풀게]하고", "이어폰으로", "몇번에 [정답] 몇번", "이렇게 나옴."])),
    (["\"3분 뒤 삭제함\"", "다들 [구라]라고 넘겼는데"], ('quote', ["지금까지 비밀이었는데", "이제 그냥 밝힘ㅋ", "", "[3분있다 삭제함]"])),
    (["그게 [진짜]였다"], ('vid', 118, 'wide')),
    (["쌀알만 한 [무선 이어폰]", "온라인에서 [6만 원대]"], ('card', 'k_ear.png', '온라인 쇼핑몰 판매 화면')),
    (["방송에서도", "[이 댓글] 그대로 소개"], ('card', 'k_mbn.png', 'MBN 보도 화면')),
    (["\"공무원 시험엔 [브로커]까지\"", "(커뮤니티 주장)"], ('card', 'k_chat.png', '커뮤니티 단톡방 캡처')),
    (["시험장 전자기기 검사", "[이대로 괜찮을까?]"], ('vid', 166, 'wide')),
]
TTS = [os.path.join(HERE, 'tts2', f'l{i:02d}.mp3') for i in range(1, 10)] + [os.path.join(HERE, 'tts3', f'l{i:02d}.mp3') for i in range(1, 4)] + [os.path.join(HERE, 'tts2', 'l10.mp3')]
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


def quote_card(lines, i):
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); d = ImageDraw.Draw(bg); fl.W = W
    f = ImageFont.truetype(fl.FM, 64); lh = 92; h = lh * len(lines) + 90
    y0 = (890 - h) // 2 + 30
    d.rounded_rectangle((60, y0, W - 60, y0 + h), 26, fill=(250, 250, 250))
    d.text((W / 2, y0 - 24), '펨코 댓글 원문', font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
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
        vf = f'{crop},scale={W}:{VH}:flags=lanczos,fps=30,{PUNCH.format(W=W, VH=VH)}'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sc[1]), '-t', f'{d:.3f}', '-i', f'{SRC}/v1.mp4', '-vf', vf, *ENC, out], check=True)
    else:
        img = (f'{SRC}/{sc[1]}' if sc[0] == 'img' else quote_card(sc[1], i) if sc[0] == 'quote'
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
sr.overlay(["세무사 수석 부정행위 방법", "[펨코에 이미 있었다] ㄷㄷ"], f'{T}/top.png', size=72)
fb = ImageFont.truetype(fl.F, 62); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 1330, W, 1612), fill=(6, 6, 8, 255))
    if sc[0] == 'vid':
        d.text((W - 40, 500), "영상: 유튜브 '이돈호 변호사'", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
               anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    y = 1471 - 80 * (len(rows) - 1) / 2 + 22
    for k, r in enumerate(rows):
        fl.line(d, r, y + 80 * k, fb)
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
w5 = int((starts[4] - 0.3) * 1000); b9 = int((starts[8] - 0.05) * 1000)
fc += f';[{n0 + N}:a]volume=1.3[x1];[{n0 + N + 1}:a]adelay={w5}|{w5},volume=1.1[x2];[{n0 + N + 2}:a]adelay={b9}|{b9},volume=1.2[x3]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + f'[x1][x2][x3]amix=inputs={N + 3}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
