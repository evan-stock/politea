"""더피드 숏츠형 릴스 — 충주맨 김선태 '9급 고졸 수준' 발언 반박 (TTS 없음, 원본 소리 그대로)
원본: 유튜브 '김선태 라이브' 2026-11-25 「9급 공무원 고졸 수준에 대한 입장발표」(UBuJ-J1plH8)
      구간 3개를 맥북 도우미로 받음: gk1 3:27~3:52 / gk2 5:02~5:16 / gk3 9:14~9:31
화면: 라이브 화면 오른쪽 아래 웹캠(본인 얼굴)만 잘라 폭 1080으로. 흐림·모자이크 없음, 남는 곳은 검정.
순서: 센 대사 먼저(고졸이 죄졌어요?) → 긁혔다 → 월급 200·누가 뽑으래. 말 없는 틈은 잘라 22초 안팎.
"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../scripts/feed_reel'))
import feedlib as fl
import shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
V = os.path.join(HERE, 'video')
TITLE = ["9급은 고졸 수준?", "[충주맨 결국 폭발] ㄷㄷ"]
CAM = (1436, 722, 484, 358)       # 웹캠 영역 (x, y, w, h)
VW, VH = 1080, 798                # 화면에 놓을 크기
VY = 520
SRC_LABEL = "영상: 유튜브 김선태 라이브"

# (파일, 시작, 끝, 자막)
SEG = [
    ('gk2', 7.35, 8.75, "고졸이 뭔데?"),
    ('gk2', 11.05, 12.75, "[고졸이 죄졌어요?]"),
    ('gk1', 9.40, 12.00, "[저 긁힌 거 맞습니다]"),
    ('gk1', 12.00, 17.50, "긁혀서 지금\n이거 켠 거예요"),
    ('gk1', 17.50, 21.10, "왜냐? 제가\n[9급이자 고졸]이에요"),
    ('gk3', 2.50, 6.50, "그럼 왜 그렇게\n[저급한 인재]를 뽑아요?"),
    ('gk3', 6.90, 8.30, "[월급 200] 주면서"),
    ('gk3', 10.00, 11.40, "대학원졸로 뽑아요"),
    ('gk3', 13.90, 15.10, "[누가 뽑으래?]"),
]


def sub_png(text, path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(fl.F, 80); fl.W = W
    ls = text.split('\n')
    ys = [1471] if len(ls) == 1 else [1421, 1521]
    for t, y in zip(ls, ys):
        fl.line(d, t, y, f, stroke=9)
    yc = sum(ys) / len(ys) - 28
    lay = lay.transform((W, H), Image.AFFINE, (1, sr.SHEAR, -sr.SHEAR * yc, 0, 1, 0), Image.BICUBIC)
    lay.save(path)


def src_png(path):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(fl.FM, 26)
    tw = d.textlength(SRC_LABEL, font=f)
    d.text((W - 28 - tw, sr.BAND + 22), SRC_LABEL, font=f, fill=(255, 255, 255, 200), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    lay.save(path)


def build():
    tmp = tempfile.mkdtemp()
    # 1) 구간 자르기 + 이어 붙이기 (웹캠만 잘라서)
    x, y, w, h = CAM
    parts = []
    for i, (k, s, e, _) in enumerate(SEG):
        p = os.path.join(tmp, f'p{i:02d}.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s}', '-t', f'{e - s:.2f}', '-i', os.path.join(V, f'{k}.mp4'),
                        '-vf', f'crop={w}:{h}:{x}:{y},scale={VW}:{VH}:flags=lanczos,fps=30,setsar=1',
                        '-af', 'aresample=48000', '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast',
                        '-c:a', 'aac', '-b:a', '192k', p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, 'l.txt'); open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    cat = os.path.join(tmp, 'cat.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', cat], check=True)
    # 2) 틀 + 자막
    ov = os.path.join(tmp, 'ov.png'); sr.overlay(TITLE, ov); src_png(os.path.join(tmp, 'src.png'))
    t, times = 0.0, []
    for i, (_, s, e, txt) in enumerate(SEG):
        sub_png(txt, os.path.join(tmp, f's{i:02d}.png')); times.append((t, t + e - s)); t += e - s
    ins = ['-i', ov, '-i', os.path.join(tmp, 'src.png')] + sum([['-i', os.path.join(tmp, f's{i:02d}.png')] for i in range(len(SEG))], [])
    fc = (f'color=c=0x08080a:s={W}x{H}:r=30[bg];[bg][0:v]overlay=0:{VY}:shortest=1[a1];'
          f'[a1][1:v]overlay=0:0[a2];[a2][2:v]overlay=0:0[b0]')
    last = 'b0'
    for i, (s, e) in enumerate(times):
        fc += f";[{last}][{i + 3}:v]overlay=0:0:enable='gte(t,{s:.2f})*lt(t,{e:.2f})'[c{i}]"
        last = f'c{i}'
    fc += f';[{last}]format=yuv420p[o];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[au]'
    out = os.path.join(HERE, 'reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', cat, *ins, '-filter_complex', fc, '-map', '[o]', '-map', '[au]',
                    '-c:a', 'aac', '-b:a', '160k', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast',
                    '-movflags', '+faststart', out], check=True)
    # 커버: '고졸이 죄졌어요?' 장면
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{times[1][0] + 0.6:.2f}', '-i', out, '-frames:v', '1', '-q:v', '2',
                    os.path.join(HERE, 'reel_cover.jpg')], check=True)
    return out, t


if __name__ == '__main__':
    print(build())
