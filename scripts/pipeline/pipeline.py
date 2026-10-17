#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline.py - video -> transcript pipeline (P4). Code-only build; no external video fetched yet.
Chain: yt-dlp audio -> faster-whisper sentence timestamps -> SRT + JSON -> optional merge with official transcript.
Deps (install when network stable): pip install -U yt-dlp faster-whisper
Usage:
  python scripts/pipeline/pipeline.py download URL OUTDIR          # audio only, --no-video
  python scripts/pipeline/pipeline.py transcribe AUDIO MODEL       # e.g. base.en / small.en
  python scripts/pipeline/pipeline.py merge ASR.json OFFICIAL.txt  # difflib alignment report
Self-test: python scripts/pipeline/pipeline.py selftest             # ffmpeg tone -> transcribe tiny model
"""
import sys, os, json, subprocess, difflib

def sh(cmd):
    print("+ " + " ".join(cmd)); return subprocess.run(cmd, check=True)

def download(url, outdir):
    os.makedirs(outdir, exist_ok=True)
    sh(["yt-dlp", "-x", "--audio-format", "m4a", "--no-playlist", "-o", os.path.join(outdir, "%(id)s.m4a"), url])

def transcribe(audio, model="base.en"):
    from faster_whisper import WhisperModel          # lazy import
    m = WhisperModel(model, device="auto", compute_type="int8")
    segs, info = m.transcribe(audio, word_timestamps=False)
    out = {"audio": audio, "model": model, "lang": info.language, "segments": []}
    for s in segs:
        out["segments"].append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    j = audio + ".asr.json"; k = audio + ".srt"
    with open(j, "w", encoding="utf-8") as fh: json.dump(out, fh, ensure_ascii=False, indent=1)
    with open(k, "w", encoding="utf-8") as fh:
        for i, s in enumerate(out["segments"], 1):
            ts = lambda t: "{:02d}:{:02d},{:03d}".format(int(t//3600), int(t%3600//60), int(t%60*1000)%1000)
            fh.write("{}\n{} --> {}\n{}\n\n".format(i, ts(s["start"]), ts(s["end"]), s["text"]))
    print("WROTE", j, k, "segments=", len(out["segments"]))

def merge(asr_json, official_txt):
    asr = json.load(open(asr_json, encoding="utf-8"))
    off = open(official_txt, encoding="utf-8").read()
    a = [s["text"] for s in asr["segments"]]; r = difflib.SequenceMatcher(None, "\n".join(a), off)
    print("similarity=", round(r.ratio(), 3))
    for tag, i1, i2, j1, j2 in r.get_opcodes():
        if tag != "equal": print(tag, "ASR[{0}:{1}] vs OFFICIAL[{2}:{3}]".format(i1, i2, j1, j2))

def selftest():
    wav = os.path.join(os.environ.get("TEMP", "."), "tone.wav")
    sh(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=3", wav])
    transcribe(wav, "tiny.en")

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(0)
    {"download": lambda: download(sys.argv[2], sys.argv[3]),
     "transcribe": lambda: transcribe(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "base.en"),
     "merge": lambda: merge(sys.argv[2], sys.argv[3]),
     "selftest": selftest}[sys.argv[1]]()