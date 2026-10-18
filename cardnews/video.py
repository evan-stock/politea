"""영상 장 만들기: 원본 영상을 4:5(1080x1350)로 자르고 카드 글자(투명 PNG)를 얹은 mp4."""
import subprocess


def video_slide(src, overlay_png, out, start=0.0, dur=10.0, crop_x=0.5, crop_y=0.5):
    """crop_x/crop_y: 4:5로 자를 때 기준 위치(0=왼쪽/위, 0.5=가운데, 1=오른쪽/아래)."""
    base = (f"[0:v]scale='if(gt(a,0.8),-2,1080)':'if(gt(a,0.8),1350,-2)',"
            f"crop=1080:1350:(in_w-1080)*{crop_x}:(in_h-1350)*{crop_y},"
            f"unsharp=5:5:0.6,fps=30,format=yuv420p")
    if overlay_png:  # 글자 얹기
        inputs = ["-i", overlay_png]
        vf, audio = base + "[v];[v][1:v]overlay=0:0[o]", "2:a"
    else:            # 글자 없이 영상만
        inputs = []
        vf, audio = base + "[o]", "1:a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(dur), "-i", src,
                    *inputs, "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", vf, "-map", "[o]", "-map", audio, "-shortest",
                    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    return out


def reel_916(src, overlay_png, out, start=0.0, dur=20.0, crop_x=0.5, crop_y=0.5, keep_audio=True):
    """원본 영상을 9:16(1080x1920)으로 꽉 채우고 글자 오버레이(투명 PNG)를 얹는다. 원본 소리 유지."""
    vf = (f"[0:v]scale='if(gt(a,0.5625),-2,1080)':'if(gt(a,0.5625),1920,-2)':flags=lanczos,"
          f"crop=1080:1920:(in_w-1080)*{crop_x}:(in_h-1920)*{crop_y},unsharp=5:5:0.6,fps=30,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(dur), "-i", src]
    if overlay_png:
        cmd += ["-i", overlay_png]
        vf += "[v];[v][1:v]overlay=0:0,format=yuv420p[o]"
    else:
        vf += "[o]"
    has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    if keep_audio and has_audio:
        amap = ["-map", "0:a"]
    else:
        cmd += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo"]
        amap = ["-map", f"{2 if overlay_png else 1}:a"]
    cmd += ["-filter_complex", vf, "-map", "[o]", *amap, "-shortest", "-c:v", "libx264", "-profile:v", "high",
            "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out
