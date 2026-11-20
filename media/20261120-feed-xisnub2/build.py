"""더피드 릴스: 같은 APEC, 트럼프 손은 잡고 다카이치에겐 '입꾹닫'. 기준 media/20261115-feed-cheat/build2.py 틀 그대로(SC·TTS·제목·효과음만 바꿈).
소스 src/: v1(엑스 @ThayzzySmith 백악관 공개 에스컬레이터 영상), v2(Viory 에스컬레이터), v3(Viory 트럼프·시진핑 악수),
press01~03(연합뉴스 시진핑·다카이치 악수). 사실: 뉴스핌·아주경제·서울신문·경향신문 2026.11.19~20. 내레이션 tts/ (Gemini Fenrir)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.1; INTRO = 0.2
T = '/tmp/xisnub2'; os.makedirs(T, exist_ok=True); SRC = os.path.join(HERE, 'src'); SFX = os.path.join(ROOT, 'assets', 'sfx')
VSRC = {'v1.mp4': "영상: 백악관 공개(X @ThayzzySmith)", 'v2.mp4': '영상: Viory', 'v3.mp4': '영상: Viory'}
AIR_SS = 0.0
AIR = os.path.exists(os.path.join(HERE, 'src', 'air.mp4'))  # 다카이치 공항 도착(SBS D리포트), 없으면 그래픽
VSRC['air.mp4'] = '영상: SBS D리포트'
SC = [  # (화면 자막, 장면)
    (["같은 날, 같은 시진핑", "[대접이 달랐다]"], ('vid', 'v3.mp4', 4.5, 0.5)),
    (["트럼프가 손 내밀자", "[바로 잡았다]"], ('vid', 'v2.mp4', 3.9, 0.42)),
    (["공항에서도", "[시진핑이 직접] 마중"], ('vid', 'air.mp4', 25.3, 0.5) if AIR else ('greet', 0)),
    (["그런데 [일본 총리]는"], ('vid', 'air.mp4', 2.5, 0.5) if AIR else ('img', 'press01.jpg', 0.5)),
    (["의장대 [10명 남짓]", "꽃도 음악도 [없었다]"], ('vid', 'air.mp4', 10.6, 0.55) if AIR else ('quote', ["의장대 [10명 남짓]", "꽃다발 [X]", "환영 음악 [X]"], 'NHK·TBS 보도')),
    (["영접은", "[외교부 의전 대사]"], ('greet', 2)),
    (["만찬에선 다카이치가", "[먼저 말 건넸지만]"], ('img', 'press02.jpg', 0.5)),
    (["시진핑은 [미소만]", "(중화권 매체 보도)"], ('img', 'press03.jpg', 0.68)),
    (["정상회담은", "끝내 [무산]"], ('tl', 3)),
    (["이유는", "[1년 전 대만 발언]"], ('tl', 0)),
    (["\"대만 유사시", "[일본도 나설 수 있다]\""], ('quote', ["대만 유사시", "[존립위기사태]가", "될 수 있다"], '2025.11 다카이치 국회 답변(취지)')),
    (["중국 \"모두에게", "[적절한 환대]\""], ('quote', ["국제관례에 따라", "모든 참석자에게", "[적절한 안내와 환대]"], '중국 외교부 대변인 (11.19)')),
    (["손잡은 미국, 외면당한 일본", "한국은 [어디에]?"], ('vid', 'v3.mp4', 11.0, 0.5)),
]
TTS = [os.path.join(HERE, 'tts', f'l{i:02d}.wav') for i in range(1, 14)]  # Gemini Fenrir(한 번에 생성 후 문장별로 자름, 1.2배속)
def trim(f, k):
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
ends = starts[1:] + [TOTAL]; seg = [ends[i] - (starts[i] if i else 0) for i in range(len(SC))]

PUNCH = "scale=w='2*trunc(540*max(1,1+0.07*exp(-t*14)))':h=-2:eval=frame,crop={W}:{VH},setsar=1"
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', '-an']


def quote_card(lines, label, i):
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); d = ImageDraw.Draw(bg); fl.W = W
    f = ImageFont.truetype(fl.FM, 64); lh = 92; h = lh * len(lines) + 90
    y0 = (890 - h) // 2 + 30
    d.rounded_rectangle((60, y0, W - 60, y0 + h), 26, fill=(250, 250, 250))
    d.text((W / 2, y0 - 24), label, font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    for k, t in enumerate(lines):
        if t: fl.line(d, t, y0 + 95 + lh * k, f, fg=(20, 20, 22))
    bg.save(f'{T}/q{i}.png'); return f'{T}/q{i}.png'


def greet_card(hl, i):  # 공항 영접 비교 그래픽: hl = 강조할 줄 번호
    rows = [("트럼프", "[시진핑 주석] 직접"), ("푸틴", "차이치 상무위원(서열 5위)"), ("다카이치", "[외교부 의전 대사]")]
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); d = ImageDraw.Draw(bg); fl.W = W
    fn, fv = ImageFont.truetype(fl.F, 58), ImageFont.truetype(fl.FM, 50)
    d.text((W / 2, 150), '공항에 누가 마중 나왔나', font=ImageFont.truetype(fl.F, 54), fill=(255, 255, 255), anchor='ms')
    d.text((W / 2, 200), '선전 APEC 도착 영접 (보도 종합)', font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
    for k, (a, b) in enumerate(rows):
        y = 260 + k * 200; on = k == hl
        d.rounded_rectangle((60, y, W - 60, y + 160), 26, fill=(250, 250, 250) if on else (44, 44, 50),
                            outline=fl.RED if on else None, width=8 if on else 0)
        fg = (20, 20, 22) if on else (150, 150, 158)
        d.text((110, y + 100), a, font=fn, fill=fg, anchor='ls')
        d.text((370, y + 98), '→', font=fv, fill=fg, anchor='ls')
        fl.line(d, b if on else b.replace('[', '').replace(']', ''), y + 98, fv, fg=fg, x0=440)
    bg.save(f'{T}/g{i}.png'); return f'{T}/g{i}.png'


def tl_card(hl, i):  # 1년 연표 그래픽
    rows = [("2025.11", "다카이치 '대만 유사시' 답변"), ("이후 1년", "중국, 발언 [철회·수정] 요구"),
            ("2026.11.18", "APEC 공항 의전 [간소]"), ("2026.11.18", "만찬 악수만, 정상회담 [무산]")]
    bg = Image.new('RGB', (W, VH), (24, 24, 28)); d = ImageDraw.Draw(bg); fl.W = W
    d.text((W / 2, 120), '중일 갈등 1년', font=ImageFont.truetype(fl.F, 64), fill=(255, 255, 255), anchor='ms')
    x = 110; d.line((x, 230, x, 230 + 3 * 165), fill=(70, 70, 78), width=6)
    for k, (a, b) in enumerate(rows):
        y = 230 + k * 165; on = k == hl
        d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=fl.RED if on else (110, 110, 118))
        d.text((x + 55, y + 14), a, font=ImageFont.truetype(fl.FM, 42), fill=fl.RED if on else (150, 150, 158), anchor='ls')
        fl.line(d, b, y + 92, ImageFont.truetype(fl.FM, 50), fg=(255, 255, 255) if on else (140, 140, 148), x0=x + 55)
    bg.save(f'{T}/l{i}.png'); return f'{T}/l{i}.png'


clips = []
for i, (_, sc) in enumerate(SC):
    out = f'{T}/s{i:02d}.mp4'; d = seg[i] + 0.05
    if sc[0] == 'vid':
        _, fn, ss, xc = sc
        vf = (f"scale={W}*max(iw/ih/({W}/{VH})\\,1):{VH}*max(({W}/{VH})/(iw/ih)\\,1):flags=lanczos,"
              f"crop={W}:{VH}:'max(0\\,min(iw-{W}\\,iw*{xc}-{W}/2))':'(ih-{VH})/2',fps=30,"
              + ("split[m][b];[b]crop=W:240:0:1170,boxblur=24:2[bl];[m][bl]overlay=0:1170,".replace('W', str(W)) if fn == 'air.mp4' else '')
              + PUNCH.format(W=W, VH=VH))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-t', f'{d:.3f}', '-i', f'{SRC}/{fn}', '-filter_complex', vf, *ENC, out], check=True)
    else:
        if sc[0] == 'img':
            im = Image.open(f'{SRC}/{sc[1]}').convert('RGB'); r = max(W / im.width, VH / im.height)
            im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
            x = int(max(0, min(im.width - W, im.width * sc[2] - W / 2)))
            im.crop((x, 0, x + W, VH)).save(f'{T}/i{i}.png'); img = f'{T}/i{i}.png'
        elif sc[0] == 'greet':
            img = greet_card(sc[1], i)
        elif sc[0] == 'tl':
            img = tl_card(sc[1], i)
        else:
            img = quote_card(sc[1], sc[2], i)
        vf = (f"scale=2160:-1,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{VH}:fps=30,"
              f"{PUNCH.format(W=W, VH=VH)}")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', f'{d:.3f}', '-i', img, '-vf', vf, *ENC, out], check=True)
    clips.append(out)
lst = f'{T}/list.txt'; open(lst, 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-t', f'{TOTAL:.3f}', *ENC, f'{T}/body.mp4'], check=True)

sr.overlay(["트럼프는 직접 마중하더니", "[일본 총리엔 입꾹닫] ㄷㄷ"], f'{T}/top.png', size=72)
fb = ImageFont.truetype(fl.F, 80); caps = []
for i, (rows, sc) in enumerate(SC):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    src = VSRC.get(sc[1]) if sc[0] == 'vid' else ('사진: 연합뉴스' if sc[0] == 'img' else None)
    if src:
        d.text((W - 40, 500), src, font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
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
for i in range(len(SC)):
    a = 0 if i == 0 else starts[i] - 0.02; b = ends[i] - 0.02
    fc += f";[{last}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{i}]"; last = f'c{i}'
fc += f";[{last}]scale=w='2*trunc(540*max(1,1+0.18*exp(-t*8)*cos(t*20)))':h=-2:eval=frame,crop={W}:{H},setsar=1,format=yuv420p[vout]"
n0 = 2 + len(SC); N = len(SC)
# 효과음: (파일, 장면, 볼륨) — 장면 바뀔 때 하나씩
FX = [('boom.mp3', 0, 1.1), ('dudung.mp3', 1, 0.5), ('swoosh_short.mp3', 3, 0.5), ('huh.mp3', 4, 0.5),
      ('buzz_wrong.mp3', 5, 0.4), ('chills.mp3', 7, 0.5), ('swoosh_short.mp3', 9, 0.5), ('keyboard.mp3', 10, 0.4), ('dudung.mp3', 12, 0.5)]
ains = sum((['-i', f] for f in TTS), []) + sum((['-i', f'{SFX}/{f}'] for f, _, _ in FX), [])
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(N))
for k, (_, s, v) in enumerate(FX):
    ms = int(max(0, (starts[s] if s else 0) - 0.05) * 1000)
    fc += f';[{n0 + N + k}:a]adelay={ms}|{ms},volume={v}[x{k}]'
fc += ';' + ''.join(f'[a{i}]' for i in range(N)) + ''.join(f'[x{k}]' for k in range(len(FX))) + \
      f'amix=inputs={N + len(FX)}:normalize=0,apad,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '6.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
