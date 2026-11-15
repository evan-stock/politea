"""더피드 숏츠형 릴스: '구라라던 펨코 부정행위 댓글, 진짜였다' (개드립 734860151 내용 + 이돈호 변호사 유튜브 자수 영상 + edge-tts 내레이션).
소스: /tmp/taxsrc/fm_comment.png(커뮤니티 댓글 캡처, 가격·장치 연결 부분은 흐림), /tmp/taxsrc/v1.mp4(오늘의쓸모 media/20261115-brk/video/v1.mp4)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'feed_reel'))
import feedlib as fl, shorts_reel as sr
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, BAND = 1080, 1920, 440; VH = H - BAND; GAP = 0.18
T = '/tmp/cheat'; os.makedirs(T, exist_ok=True)
LINES = ["얼마 전 한 커뮤니티에 이런 댓글이 올라왔습니다.",
         "절대 안 걸리는 부정행위 방법이라며, 초소형 카메라로 문제를 찍으면 AI가 풀고, 귀에 숨긴 이어폰으로 답이 들어온다는 내용이었죠.",
         "3분 뒤 지운다던 이 글, 다들 구라라고 넘겼습니다.",
         "그런데 세무사 시험 수석 합격자가 경찰에 자수하며 밝힌 방법이, 바로 이거였습니다.",
         "초소형 카메라로 시험 문제를 찍어 생성형 AI에 보내고, 답은 스마트폰으로 받았다는 겁니다.",
         "시험장 감독관 4명 중 누구도 눈치채지 못했습니다.",
         "예전엔 대신 풀어 줄 사람을 구하는 게 제일 어려웠다면, 이제 그 자리를 AI가 채운 셈입니다.",
         "시험장 전자기기 검사, 이대로 괜찮을까요?"]
# 화면 자막(짧게 끊음, [대괄호] 빨강)
CAPS = [["얼마 전 한 커뮤니티 댓글"],
        ["\"절대 안 걸리는 방법\"", "[초소형 카메라]로 문제 찍으면", "[AI]가 풀고 이어폰으로 정답"],
        ["3분 뒤 삭제한다던 글", "다들 [구라]라고 넘겼다"],
        ["그런데 세무사 수석이", "[경찰 자수]하며 밝힌 방법"],
        ["초소형 카메라로 찍어 [생성형 AI]로", "답은 [스마트폰]으로"],
        ["감독관 4명 [아무도 몰랐다]"],
        ["대신 풀어 줄 사람 구하는 게", "제일 어려웠는데", "이젠 [AI]가 그 자리를"],
        ["시험장 전자기기 검사", "[이대로 괜찮을까?]"]]
TTS = [os.path.join(HERE, 'tts', f'l{i:02d}.mp3') for i in range(1, 9)]
dur = [float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                            capture_output=True, text=True).stdout) for f in TTS]
starts = []; t = 0.3
for d in dur:
    starts.append(t); t += d + GAP
TOTAL = t + 0.6
CUT = starts[3]  # 4번째 문장부터 자수 영상

# 1) 댓글 캡처 장면(1080x1480): 어두운 바탕 + 흰 카드, 가격·장치 연결 줄은 흐리게, 천천히 확대
c = Image.open('/tmp/taxsrc/fm_comment.png').convert('RGB').crop((18, 18, 630, 478))
blur = c.crop((0, 118, c.width, 285)).filter(ImageFilter.GaussianBlur(9)); c.paste(blur, (0, 118))
s = 1000 / c.width; c = c.resize((1000, int(c.height * s)), Image.LANCZOS)
bg = Image.new('RGB', (W, VH), (24, 24, 28)); bg.paste(c, ((W - c.width) // 2, 110))
dd = ImageDraw.Draw(bg); fl.W = W
dd.text((W / 2, 88), '커뮤니티 댓글 캡처 (일부 흐림 처리)', font=ImageFont.truetype(fl.FM, 30), fill=(170, 170, 178), anchor='ms')
bg.save(f'{T}/comment.png')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', f'{T}/comment.png', '-t', f'{CUT:.3f}', '-filter_complex',
                f"[0:v]scale=2160:-1,zoompan=z='1+0.00012*on':x='iw/2-(iw/zoom/2)':y='ih*0.3-(ih/zoom*0.3)':d=1:s={W}x{VH}:fps=30,format=yuv420p",
                '-r', '30', f'{T}/a.mp4'], check=True)
# 2) 자수 영상(원본 세로 영상 안쪽 화면만, 원본 자막은 아래 우리 자막 띠로 가림)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '26', '-t', f'{TOTAL - CUT:.3f}', '-i', '/tmp/taxsrc/v1.mp4', '-an', '-vf',
                f'crop=563:770:78:375,scale={W}:{VH}:flags=lanczos,fps=30,format=yuv420p', f'{T}/b.mp4'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{T}/a.mp4', '-i', f'{T}/b.mp4', '-filter_complex',
                '[0:v][1:v]concat=n=2:v=1:a=0[v]', '-map', '[v]', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', f'{T}/body.mp4'], check=True)

# 3) 겹칠 그림: 위 제목 띠(기울임)+로고 / 문장별 자막 띠
sr.overlay(["구라라던 펨코 댓글", "[진짜였다] ㄷㄷ"], f'{T}/top.png')
fb = ImageFont.truetype(fl.F, 60)
cap_files = []
for i, rows in enumerate(CAPS):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 1330, W, 1612), fill=(6, 6, 8, 255))  # 원본 자막·알약을 가리는 자막 띠
    if i >= 3:
        d.text((W - 40, 500), "영상: 유튜브 '이돈호 변호사'", font=ImageFont.truetype(fl.FM, 28), fill=(235, 235, 235, 255),
               anchor='rs', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    y = 1471 - 78 * (len(rows) - 1) / 2 + 22
    for k, r in enumerate(rows):
        fl.line(d, r, y + 78 * k, fb, fg=(255, 255, 255))
    p = f'{T}/cap{i}.png'; im.save(p); cap_files.append(p)

# 4) 합치기
inputs = ['-i', f'{T}/body.mp4', '-i', f'{T}/top.png'] + sum((['-i', p] for p in cap_files), [])
fc = f'color=c=0x08080a:s={W}x{H}:r=30:d={TOTAL:.3f}[bg];[bg][0:v]overlay=0:{BAND}:shortest=1[s0];[s0][1:v]overlay=0:0[s1]'
last = 's1'
for i in range(len(CAPS)):
    a = starts[i] - 0.05; b = starts[i + 1] - 0.05 if i + 1 < len(starts) else TOTAL
    fc += f";[{last}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{i}]"; last = f'c{i}'
# 소리: 문장 mp3를 시작 시각에 놓기
ains = sum((['-i', f] for f in TTS), [])
n0 = 2 + len(CAPS)
fc += ';' + ';'.join(f'[{n0 + i}:a]adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[a{i}]' for i in range(8))
fc += ';' + ''.join(f'[a{i}]' for i in range(8)) + f'amix=inputs=8:normalize=0,apad,atrim=0:{TOTAL:.3f},volume=1.1[aout]'
fc += f';[{last}]format=yuv420p[vout]'
out = os.path.join(HERE, 'reel.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *ains, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]',
                '-t', f'{TOTAL:.3f}', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', out], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '2', os.path.join(HERE, 'reel_cover.jpg')], check=True)
print('ok', round(TOTAL, 2), [round(x, 2) for x in starts])
