"""더피드 TTS형 릴스: 세무사 수석 AI 커닝 장비 3D 재현(경향신문 11.18 단독 보도 내용). feed-reward/build.py(=build2.py 복사본) 복사, SC·TTS·제목·효과음만 교체.
3D 장면: cardnews scripts/story_shorts/anim3d_cheat.py(Blender 로우폴리) → gfx3d_post → src/g3d.mp4. 움직임 효과 없음(컷만).
사진: 경찰 출석(연합뉴스, 경향신문 기사 사진, 얼굴 가림 원본). 캡처: 경향신문 기사 제목(X @deoksu_kr 첨부)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/feedcheat3d'; os.makedirs(T, exist_ok=True); SRC = os.path.join(HERE, 'src'); SFX = os.path.join(ROOT, 'assets', 'sfx')
SC = [  # (화면 자막, 장면)  g3d = (3D 영상 시작 초, 재생 속도)
    (["세무사 수석의 [AI 커닝 수법]", "드러났다"], ('cmt', 'khan_head.jpg', (0, 0, 4096, 1500), '경향신문 단독 (11.18)')),
    (["시작은 [수정테이프] 속", "초소형 카메라"], ('g3d', 0.0, 0.45)),
    (["시험 문제를", "[몰래 촬영]"], ('g3d', 0.7, 0.45)),
    (["계산기는", "[무선 키보드]로 개조"], ('g3d', 1.6, 0.45)),
    (["버튼 하나하나가", "[전송 명령어]"], ('g3d', 1.9, 0.3)),
    (["휴대전화 거쳐", "[집 노트북]으로"], ('g3d', 2.6, 0.75)),
    (["노트북 속 [AI가]", "문제 풀이"], ('g3d', 4.4, 0.6)),
    (["답은 [초소형 모니터]로", "돌아왔다"], ('g3d', 6.2, 0.5)),
    (["[파이썬]으로", "프로그램까지 직접"], ('quote', ["'파이썬'으로 별도 프로그램", "지난해 12월부터 준비", "두 달여 만에 [코딩까지 완료]"], '경향신문 보도 (11.18)')),
    (["첫 실전은", "[3월 회계사 시험]"], ('quote', ["1교시 경영학·경제원론 [만점]", "2교시 기업법·세법 [1문제] 틀림", "3교시 회계학 중 [기기 이상]"], '경향신문 보도 (11.18)')),
    (["기기 고장 나자", "[위경련] 호소하며 귀가"], ('quote', ["기기 오류에도", "적발되지 않자", "[같은 수법]을 세무사 시험에"], '경향신문 보도 (11.18)')),
    (["한 달 뒤", "[세무사 시험 수석]"], ('img', 'photo.jpg')),
    (["내일 수능", "[막을 수 있을까?]"], ('g3d', 4.6, 0.0)),
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
    if sc[0] == 'g3d':   # 3D 시뮬레이션(1080x780)을 위쪽 카드 자리에, 남는 곳은 어두운 바탕. 속도 0이면 그 장면 정지
        sp = sc[2]
        tim = f"setpts=PTS/{sp}," if sp else "trim=end_frame=1,loop=loop=-1:size=1,setpts=N/30/TB,"
        vf = (f"{tim}fps=30,tpad=stop_mode=clone:stop_duration=20,pad={W}:{VH}:0:55:0x18181c,{PUNCH}")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sc[1]), '-i', f'{SRC}/g3d.mp4', '-t', f'{d:.3f}', '-filter_complex', vf, *ENC, out], check=True)
    elif sc[0] == 'vid':
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
sr.overlay(["세무사 수석 AI 커닝 장비", "[3D로 재현해봤다] ㄷㄷ"], f'{T}/top.png', size=80)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sc[0] in ('img', 'g3d'):
        d.text((W - 40, 500), "사진: 연합뉴스(경향신문)" if sc[0] == 'img' else "3D 재현: 더피드(경향신문 보도 내용)", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
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
ains = sum((['-i', f] for f in TTS), []) + ['-i', f'{SFX}/dudung.mp3', '-i', f'{SFX}/keyboard.mp3', '-i', f'{SFX}/chills.mp3']
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
w5 = int(starts[3] * 1000); b9 = int(starts[11] * 1000)  # dudung=첫 장면, keyboard=계산기, chills=세무사 수석
fc += f';[{n0 + N}:a]volume=-7dB[x1];[{n0 + N + 1}:a]adelay={w5}|{w5},volume=-8dB[x2];[{n0 + N + 2}:a]adelay={b9}|{b9},volume=-8dB[x3]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + f'[x1][x2][x3]amix=inputs={N + 3}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
