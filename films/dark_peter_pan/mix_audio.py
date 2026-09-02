#!/usr/bin/env python3
"""Build the film's soundtrack (narration + Mixkit SFX) with ffmpeg.

Usage: python3 mix_audio.py [out.wav]
Timeline follows SCRIPT.md (62 s). Each cue: (file, start_s, gain_dB, [fade_in, fade_out, trim_to_s]).
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "audio")
S = os.path.join(A, "sfx")
TOTAL = 62.0

# name, start, gain_db, fade_in, fade_out, max_len
CUES = [
    # --- S1 nursery 0-9
    (f"{S}/1172.mp3", 0.0, -14, 1.5, 1.0, 9.5),      # cold interior wind
    (f"{S}/337.mp3", 2.2, -12, 0, 0, None),           # floorboard creak
    (f"{S}/1163.mp3", 6.0, -10, 0, 0.5, None),        # window creak
    (f"{A}/narr_1.mp3", 1.5, 0, 0, 0, None),
    # --- S2 forest 9-20
    (f"{S}/2483.mp3", 8.5, -13, 1.5, 1.5, 12.5),      # scary woods
    (f"{S}/2623.mp3", 17.0, -9, 0, 0, None),          # ghostly whoosh
    (f"{A}/narr_2.mp3", 10.0, 0, 0, 0, None),
    # --- S3 graveyard 20-31
    (f"{S}/2500.mp3", 19.5, -14, 1.5, 1.5, 12.5),     # tomb ambience
    (f"{S}/1157.mp3", 21.0, -16, 1.0, 1.5, 10.0),     # graveyard wind
    (f"{A}/narr_3.mp3", 20.5, 0, 0, 0, None),
    # --- S4 chase 31-44
    (f"{S}/2483.mp3", 30.5, -15, 1.0, 1.0, 13.0),     # woods bed
    (f"{S}/1236.mp3", 31.0, -8, 0.3, 0.8, 6.3),       # running
    (f"{S}/1214.mp3", 37.0, -9, 0.5, 0.8, 6.0),       # careful walk
    (f"{S}/494.mp3", 31.0, -12, 1.0, 0.5, 12.5),      # slow heartbeat
    (f"{S}/773.mp3", 43.4, -6, 0, 0, None),           # horror impact on cut to black
    (f"{A}/narr_4.mp3", 32.0, 0, 0, 0, None),
    # --- S5 adult Wendy 44-54
    (f"{S}/1172.mp3", 44.0, -15, 1.5, 1.0, 10.5),
    (f"{S}/634.mp3", 44.0, -19, 3.0, 2.0, 18.0),      # haunted orchestra, faint
    (f"{A}/narr_5.mp3", 44.5, 0, 0, 0, None),
    # --- S6 new child 54-62
    (f"{S}/1163.mp3", 56.0, -9, 0, 0.5, None),        # window opens itself
    (f"{S}/2630.mp3", 58.0, -8, 0, 1.0, None),        # terror sweep into title
    (f"{A}/narr_6.mp3", 54.5, 0, 0, 0, None),
]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(A, "mix.wav")
    inputs, filters, labels = [], [], []
    for i, (f, start, gain, fi, fo, ml) in enumerate(CUES):
        inputs += ["-i", f]
        chain = [f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo"]
        if ml:
            chain.append(f"atrim=0:{ml}")
        if fi:
            chain.append(f"afade=t=in:st=0:d={fi}")
        if fo and ml:
            chain.append(f"afade=t=out:st={ml - fo}:d={fo}")
        chain.append(f"volume={gain}dB")
        chain.append(f"adelay={int(start * 1000)}|{int(start * 1000)}")
        filters.append(",".join(chain) + f"[a{i}]")
        labels.append(f"[a{i}]")
    n = len(CUES)
    filters.append("".join(labels) + f"amix=inputs={n}:normalize=0:duration=longest,"
                   f"atrim=0:{TOTAL},afade=t=out:st={TOTAL - 1.5}:d=1.5,alimiter=limit=0.95[out]")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-ar", "48000", out]
    subprocess.run(cmd, check=True, capture_output=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                         capture_output=True, text=True).stdout.strip()
    print(json.dumps({"out": out, "duration_s": float(dur), "cues": n}))


if __name__ == "__main__":
    main()
