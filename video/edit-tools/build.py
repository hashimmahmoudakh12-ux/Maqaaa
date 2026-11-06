import json, subprocess, sys

W, H, FPS = 1080, 1920, 30
PRE, POST = 0.08, 0.14          # breathing room kept around speech
DROP = [(18.5, 20.0)]           # false start: "and I'm hoping to —"

# ---------- 1. keep-segments from speech map ----------
speech = json.load(open('speech.json'))
speech = [s for s in speech if not any(a <= s[0] and s[1] <= b for a, b in DROP)]
segs = []
for a, b in speech:
    a, b = max(0, a - PRE), min(35.26, b + POST)
    a, b = round(a * FPS) / FPS, round(b * FPS) / FPS     # frame aligned
    if segs and a <= segs[-1][1] + 0.30:
        segs[-1][1] = max(segs[-1][1], b)
    else:
        segs.append([a, b])

def remap(t):
    """original time -> edited time (times inside a cut snap to next kept frame)"""
    acc = 0.0
    for a, b in segs:
        if t < a:
            return acc
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc
TOTAL = sum(b - a for a, b in segs)

# ---------- 2. words (orig times) grouped into caption cards ----------
# (word, start); keywords render gold italic
KEY = {'Umrah', 'Allah', 'deen', 'Makkah', 'Madinah', 'present', 'inspire'}
cards = [
    [('What', 3.06), ("I'm", 3.44), ('hoping', 3.60), ('to', 3.80), ('gain', 4.06)],
    [('from', 4.24), ('this', 4.46), ('Umrah', 4.66)],
    [('is', 5.53), ('really', 5.62), ('just', 5.98)],
    [('a', 6.96), ('deeper', 7.14), ('connection', 7.60)],
    [('with', 8.52), ('Allah', 8.96), ('and', 9.20), ('my', 9.40), ('deen', 9.52)],
    [('and', 10.51), ('just', 10.88), ('to', 11.70), ('be', 11.90), ('present', 12.08)],
    [('and', 12.88), ('just', 13.28), ('to', 14.29), ('take', 14.50), ('this', 16.00)],
    [('as', 16.30), ('a', 16.78), ('learning', 16.86), ('experience.', 17.02)],
    [('What', 20.42), ("I'm", 20.50), ('hoping', 20.62), ('to', 20.78), ('bring', 20.96), ('back', 21.12)],
    [('here', 22.20), ('is', 22.40), ('just', 23.55), ('to', 23.70), ('inspire', 23.92)],
    [('more', 25.08), ('youth', 25.30), ('like', 25.70), ('me', 26.00)],
    [('to', 26.57), ('go', 26.62), ('and', 27.66), ('make', 28.27), ('Umrah', 28.50)],
    [('and', 29.32), ('see', 29.55), ('Makkah', 30.24)],
    [('and', 31.18), ('Madinah', 31.30), ('for', 31.86), ('themselves.', 31.98)],
]

def ts(t):
    t = max(0, t); cs = int(round(t * 100))
    return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"

CREAM, GOLD, SH = '&HD8EDF5&', '&H4CA8C9&', '&H101A09&'   # BGR
hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Cormorant Garamond SemiBold,92,{CREAM},{CREAM},{SH},&H64000000&,0,0,0,0,100,100,1,0,1,3,0,5,90,90,0,1
Style: Arabic,Amiri,104,{GOLD},{GOLD},{SH},&H64000000&,1,0,0,0,100,100,0,0,1,3,0,5,60,60,0,1
Style: Translit,Cormorant Garamond Medium,62,{CREAM},{CREAM},{SH},&H64000000&,0,1,0,0,100,100,3,0,1,3,0,5,60,60,0,1
Style: Rule,Cormorant Garamond Medium,10,{GOLD},{GOLD},{GOLD},&H00000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
CY = 1430           # caption centre (lower third, clear of reel UI)
SOFT = r'{\blur7\bord3\3a&H50&}'   # soft halo shadow instead of hard outline

# ---------- opening title: greeting ----------
g0, g1 = remap(0.41), remap(2.57) + 0.35
ev.append(f"Dialogue: 2,{ts(g0)},{ts(g1)},Arabic,,0,0,0,,"
          r"{\an5\pos(540,1330)\fad(350,300)\blur14\t(0,600,0.6,\blur1)\3a&H40&\bord4}"
          + __import__("arabic_reshaper").reshape("السلام عليكم ورحمة الله وبركاته"))
ev.append(f"Dialogue: 2,{ts(g0+0.25)},{ts(g1)},Translit,,0,0,0,,"
          r"{\an5\move(540,1475,540,1460,0,900)\fad(400,300)\blur12\t(0,700,0.6,\blur1)\3a&H40&\bord3}"
          "Assalamu alaikum warahmatullahi wabarakatuh")
ev.append(f"Dialogue: 1,{ts(g0+0.15)},{ts(g1)},Rule,,0,0,0,,"
          r"{\an5\pos(540,1400)\fad(0,300)\fscx0\t(0,900,0.5,\fscx100)\bord0\shad0\p1}m -150 0 l 150 0 l 150 2 l -150 2{\p0}")

# ---------- word-reveal cards ----------
RISE = 380      # ms for each word to resolve from blur
for i, card in enumerate(cards):
    st = remap(card[0][1]) - 0.06
    nxt = remap(cards[i + 1][0][1]) - 0.06 if i + 1 < len(cards) else TOTAL
    last = remap(card[-1][1])
    en = min(nxt - 0.02, last + 1.6)
    parts = []
    for w, t in card:
        o = int((remap(t) - st) * 1000)
        key = w.strip('.') in KEY
        base = (r'\c' + GOLD + r'\i1\fnCormorant Garamond SemiBold\fs104') if key else ''
        parts.append('{' + base + rf'\alpha&HFF&\blur10\t({o},{o+RISE},0.5,\alpha&H00&\blur0.6)' + '}' + w)
    dur = int((en - st) * 1000)
    head = (rf'{{\an5\move(540,{CY+26},540,{CY},0,{min(dur,1100)})'
            rf'\fad(0,260)\t({max(dur-260,0)},{dur},\blur8)\blur7\bord3\3a&H50&}}')
    ev.append(f"Dialogue: 2,{ts(st)},{ts(en)},Cap,,0,0,0,,{head}" + ' '.join(parts))
    # thin gold rule drawing in under each card
    ev.append(f"Dialogue: 1,{ts(st)},{ts(en)},Rule,,0,0,0,,"
              rf"{{\an5\pos(540,{CY+82})\fad(0,260)\alpha&H40&\fscx0\t(0,700,0.45,\fscx100)\bord0\shad0\p1}}"
              "m -60 0 l 60 0 l 60 2 l -60 2{\\p0}")

open('captions.ass', 'w').write(hdr + '\n'.join(ev) + '\n')

# ---------- 3. ffmpeg filtergraph: cuts + alternating punch-in + audio fades ----------
fg = []
for i, (a, b) in enumerate(segs):
    z = 1.0 if i % 2 == 0 else 1.07          # hide jump cuts with a subtle punch-in
    zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
    fg.append(f"[0:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS,scale={zw}:{zh}:flags=lanczos,"
              f"crop={W}:{H}:{(zw-W)//2}:{int((zh-H)*0.3)},setsar=1[v{i}]")
    d = b - a
    fg.append(f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.012,afade=t=out:st={max(d-0.02,0):.4f}:d=0.02[a{i}]")
fg.append(''.join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[vc][ac]")
fg.append("[vc]vignette=angle=PI/8:mode=forward,"
          "ass=captions.ass:fontsdir=../fonts:shaping=complex,format=yuv420p[vout]")
fg.append("[ac]highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
open('graph.txt', 'w').write(';\n'.join(fg))

print(f"segments: {len(segs)}  {35.27:.2f}s -> {TOTAL:.2f}s")
for a, b in segs: print(f"  keep {a:6.2f}-{b:6.2f}")
