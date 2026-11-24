"""더피드 영상 릴스(TTS 없음, 원본 소리): 젠슨 황 11일 만에 엔비디아 복귀 — 본사 직원 환호, "두 번째 기회 고맙다, 더 나은 CEO 되겠다"(X @SawyerMerritt, 2026-11-23).
틀: media/20261121-feed-aimirror/build.py. 세로 영상이라 위 띠 아래 1080x1480으로 가운데 자름(확대 최소).
대사: v1은 cardnews 받아쓰기(media/20261124-jensenhq/video/v1.srt), v2는 게시글 원문 인용.
실행: python3 media/20261124-feed-jensenback/build.py [cardnews 저장소 경로]"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

CN = sys.argv[1] if len(sys.argv) > 1 else '/home/user/cardnews'
W, H, BAND = 1080, 1920, 440; VH = H - BAND
T = '/tmp/feedjensenback'; os.makedirs(T, exist_ok=True); SFX = os.path.join(ROOT, 'assets', 'sfx')
V1 = f'{CN}/media/20261124-jensenback/video/v1.mp4'   # 1080x1920, 직원 환호
V2 = f'{CN}/media/20261124-jensenback/video/v2.mp4'   # 720x1280, 발언
C1 = 'crop=1080:1480:0:200'
C2 = 'scale=1080:1920:flags=lanczos,crop=1080:1480:0:200'
SRCN = {V1: '영상: X @SawyerMerritt', V2: '영상: X @SawyerMerritt'}
SC = [  # (자막, (원본, 시작, 길이, 화면))
    (["직원들:", "\"[사랑해요, 젠슨!]\""], (V1, 0.0, 4.6, C1)),
    (["\"[돌아온 걸 환영해요!]\""], (V1, 4.6, 3.4, C1)),
    (["\"자, [일하러 갑시다!]\""], (V1, 16.2, 3.0, C1)),
    (["본사 3개 층이", "[꽉 찼다]"], (V1, 29.3, 3.5, C1)),
    (["\"두 번째 기회", "[모두 고마워요]\""], (V2, 0.0, 3.2, C2)),
    (["\"두 번째엔", "[더 나은 CEO]가 될게요\""], (V2, 3.2, 3.3, C2)),
    (["그리고 직원들 사이로", "[다시 출근]"], (V2, 6.5, 4.7, C2)),
]
TITLE = ["11일 만에 돌아온 젠슨 황", "[직원들 반응] 미쳤다 ㄷㄷ"]
SFXS = []  # 효과음 없음(원본 환호 소리)  # (효과음, 장면 번호, dB)
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
        src, ss, d, crop = sc
        vf = (f"{crop},setsar=1,fps=30,{PUNCH.format(W=W, VH=VH)}")  # 세로 영상은 바로 1080x1480
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
fc += ';[0:a]apad=pad_dur=4,loudnorm=I=-16:TP=-1.5[orig]'  # 2026-11-17: loudnorm이 끝 몇 초를 삼켜 apad로 여유
for k, (n, sci, db) in enumerate(SFXS):
    ms = int(max(0, starts[sci] - 0.05) * 1000); fc += f';[{n0 + k}:a]adelay={ms}|{ms},volume={db}dB[x{k}]'
fc += (';[orig]' + ''.join(f'[x{k}]' for k in range(len(SFXS))) + f'amix=inputs={1 + len(SFXS)}:normalize=0,alimiter=limit=0.95,apad,atrim=0:{TOTAL:.3f}[aout]') if SFXS else f';[orig]alimiter=limit=0.95,atrim=0:{TOTAL:.3f}[aout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
