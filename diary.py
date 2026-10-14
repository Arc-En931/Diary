"""My Diary. Run:  python diary.py   (or rename to diary.pyw and double-click)
Saves automatically to diary_data.json in the same folder as this file."""
import tkinter as tk, json, os, random, math, uuid
from tkinter import font as tkfont, messagebox
from datetime import datetime

import sys
# When packed as an .exe, keep the diary data NEXT TO the .exe (not in a temporary folder).
HERE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "diary_data.json")
DEFAULTS = ["Art", "Programming", "Civil", "Language", "Novel", "Exercise"]
STONES = ["#c2b093", "#b3a083", "#cbbba0", "#a99878", "#bba98b", "#b8a587"]
SCRIB = ["#d8c4a0", "#b89b72", "#8a6f4d", "#5c4a3a", "#2e2a24", "#a89f91", "#cdbfa3"]
DESK, PAPER, LINE, MARG, RULE = "#e9dfcb", "#fffaf0", "#d9cdb4", "#b08968", "#d9c9ad"
INK, SOFT, ACC, CARD = "#4a4038", "#6b625a", "#7a5230", "#fff4dc"
HAND = BODY = "TkDefaultFont"
K = 1.0  # UI scale, set from the screen size in main()


def fp(px, bold=False, hand=False):
    """Font sized in PIXELS (same on every screen), scaled by K."""
    return (HAND if hand else BODY, -max(1, round(px * K)), "bold" if bold else "normal")


def mkcat(n):
    return {"id": uuid.uuid4().hex[:8], "name": n, "text": ""}


def load():
    try:
        with open(FILE, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {"entries": []}
    d.setdefault("entries", [])
    d.setdefault("catalog", list(DEFAULTS))
    return d


def save(d):
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, FILE)


def fmt(iso):
    d = datetime.fromisoformat(iso)
    return f"{d:%A}, {d:%B} {d.day}, {d.year} · {d.strftime('%I:%M %p').lstrip('0')}"


# ---------- background: coffee stains + ant sketch ----------
def wob(c, pts, rng, w=1.6, j=1.4, closed=False):
    if closed:
        pts = list(pts) + list(pts[:2])
    for _ in range(2):
        p = [(x + rng.uniform(-j, j), y + rng.uniform(-j, j)) for x, y in pts]
        c.create_line(*[v for xy in p for v in xy], fill=INK, width=w, smooth=True, capstyle="round", tags="bg")


def stain(c, i, x, y):
    rng = random.Random(i * 13 + 5)
    r = rng.randint(34, 66)
    kind = i % 3

    def wobbly(rr, n=14):
        out = []
        for k in range(n):
            a = k / n * 6.283
            q = rr * (1 + rng.uniform(-.07, .07))
            out += [x + q * math.cos(a), y + q * math.sin(a)]
        return out
    if kind == 1:  # filled blob
        c.create_polygon(*wobbly(r), smooth=True, fill="#ead8b8", outline="#d6bc92", stipple="gray50", tags="bg")
        return
    c.create_polygon(*wobbly(r - 4), smooth=True, fill="#efdfc2", outline="", stipple="gray25", tags="bg")
    c.create_polygon(*wobbly(r), smooth=True, fill="", outline="#dcc39d", width=6, tags="bg")
    c.create_polygon(*wobbly(r + 1), smooth=True, fill="", outline="#c9a676", width=2, tags="bg")
    if kind == 2:  # drips / splatter
        for _ in range(5):
            a, d, s = rng.uniform(0, 6.283), r * rng.uniform(1.15, 1.7), rng.randint(2, 5)
            c.create_oval(x + d * math.cos(a) - s, y + d * math.sin(a) - s, x + d * math.cos(a) + s,
                          y + d * math.sin(a) + s, fill="#d9bf98", outline="", tags="bg")


_SP = {}


def shape_spots(W, H):
    """Random spots; a shape may overlap at most ONE other shape. Stable as the page grows."""
    if len(_SP) > 6:
        _SP.clear()
    st = _SP.setdefault(int(W), {"spots": [], "done": 0})
    spots, need = st["spots"], int(H // 300) + 1
    for b in range(st["done"], need):
        r = random.Random(b * 31 + 7)
        near = [q for q in spots if q[1] > b * 300 - 400]
        for _ in range(18):
            for _t in range(30):
                R, x, y = r.uniform(22, 80), r.uniform(0, W), b * 300 + r.uniform(0, 300)
                hits = [q for q in near if math.hypot(q[0] - x, q[1] - y) < q[2] + R]
                if len(hits) <= 1 and all(q[3] == 0 for q in hits):
                    for q in hits:
                        q[3] += 1
                    p = [x, y, R, len(hits), r.getrandbits(32)]
                    spots.append(p); near.append(p)
                    break
    st["done"] = max(st["done"], need)
    return spots


def draw_shape(c, x, y, R, r):
    col, th = r.choice(SCRIB), r.uniform(-.6, .6)
    fill, w = (col if r.random() < .5 else ""), r.choice((2, 3))
    kw = dict(outline=col, width=w, tags="bg", fill=fill, **({"stipple": "gray25"} if fill else {}))
    plain = dict(outline=col, width=w, tags="bg", fill="")

    def rot(pts):
        return [v for u, q in pts for v in (x + u * math.cos(th) - q * math.sin(th), y + u * math.sin(th) + q * math.cos(th))]

    def extrude(poly, d):  # cube / prism: back face, edges, front face
        front = [(u - d / 2, q + d / 2) for u, q in poly]
        back = [(u + d, q - d) for u, q in front]
        c.create_polygon(*rot(back), **plain)
        for a, b in zip(front, back):
            c.create_line(*rot([a, b]), fill=col, width=w, tags="bg")
        c.create_polygon(*rot(front), **kw)
    k = r.choice(("triangle", "circle", "square", "cube", "prism", "cone"))
    if k == "triangle":
        c.create_polygon(*rot([(-R * .9, R * .7), (R * .9, R * .7), (0, -R)]), **kw)
    elif k == "circle":
        c.create_oval(x - R, y - R, x + R, y + R, **kw)
    elif k == "square":
        s_ = R * .7
        c.create_polygon(*rot([(-s_, -s_), (s_, -s_), (s_, s_), (-s_, s_)]), **kw)
    elif k == "cube":
        s_ = R * .5
        extrude([(-s_, -s_), (s_, -s_), (s_, s_), (-s_, s_)], R * .45)
    elif k == "prism":
        n, a = r.choice((3, 5, 6)), R * .5
        extrude([(a * math.cos(j * 6.283 / n - 1.571), a * math.sin(j * 6.283 / n - 1.571)) for j in range(n)], R * .5)
    else:  # cone
        by, rx, ry = R * .55, R * .6, R * .2
        c.create_polygon(*rot([(-rx, by), (0, -R), (rx, by)]), **{**kw, "outline": ""})
        for sx in (-rx, rx):
            c.create_line(*rot([(sx, by), (0, -R)]), fill=col, width=w, tags="bg")
        c.create_polygon(*rot([(rx * math.cos(t * .314), by + ry * math.sin(t * .314)) for t in range(20)]), **kw)


def shapes(c, W, H):  # triangles, circles, squares, cubes, prisms, cones
    for x, y, R, _, seed in shape_spots(W, H):
        if y < H + 100:
            draw_shape(c, x, y, R, random.Random(seed))


class App:
    def __init__(s, root):
        s.root, s.d, s.view, s.stack, s.wide, s.W, s.H = root, load(), None, [], [], 600, 600
        s.X, s.sx, s.SW, s.texts = 84, 0, 800, []
        root.minsize(720, 520)
        s.drag, s.slots = None, []
        root.title("My Diary")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = int(sw * .92), int(sh * .88)
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{int(sh * .04)}")
        root.configure(bg=DESK)
        sb = tk.Scrollbar(root)
        sb.pack(side="right", fill="y", pady=12)
        s.pg = tk.Canvas(root, bg=PAPER, highlightthickness=0, yscrollcommand=sb.set)
        sb.configure(command=s.pg.yview)
        s.pg.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=12)
        s.pg.bind("<Configure>", s.sync)
        s.pg.configure(yscrollincrement=int(24 * K))  # pixels per scroll step
        root.bind_all("<MouseWheel>", s.wheel)
        for ev, fn in (("<ButtonPress-1>", s.bpress), ("<B1-Motion>", s.bmove), ("<ButtonRelease-1>", s.brelease)):
            s.pg.tag_bind("block", ev, fn)
        s.pg.tag_bind("block", "<Enter>", lambda e: s.pg.configure(cursor="hand2"))
        s.pg.tag_bind("block", "<Leave>", lambda e: s.pg.configure(cursor=""))
        for key, n, what in (("<Up>", -3, "units"), ("<Down>", 3, "units"), ("<Prior>", -1, "pages"), ("<Next>", 1, "pages")):
            root.bind_all(key, lambda e, n=n, what=what: s.key_scroll(n, what))
        root.update_idletasks()
        s.render()

    # ----- layout engine: items are stacked top to bottom on the paper -----
    def txt(s, text, size, fg=INK, hand=True, bold=True, gap=8):
        i = s.pg.create_text(s.X, 0, text=text, anchor="nw", fill=fg, width=s.W, font=fp(size, bold, hand))
        s.stack.append((i, gap))
        s.texts.append(i)

    def put(s, widget, gap=8, wide=False):
        i = s.pg.create_window(s.X, 0, window=widget, anchor="nw", **({"width": s.W} if wide else {}))
        s.stack.append((i, gap))
        if wide:
            s.wide.append(i)

    def key_scroll(s, n, what="units"):  # Up/Down arrows and PageUp/PageDown scroll the page
        try:
            w = s.root.focus_get()
        except KeyError:
            w = None
        if w is not None and (w.winfo_toplevel() is not s.root or isinstance(w, tk.Text)):
            return  # pop-up windows keep their own keys; the writing box handles its own edges
        s.pg.yview_scroll(n, what)

    def wheel(s, e):  # mouse wheel and touchpad: small steps = smooth
        n = int(-e.delta / 120 * 3) or (-1 if e.delta > 0 else 1)
        s.pg.yview_scroll(n, "units")

    def layout(s):
        s.pg.update_idletasks()
        y = 24 * K
        for item, gap in s.stack:
            y += gap * K
            s.pg.coords(item, s.X, y)
            b = s.pg.bbox(item)
            y += b[3] - b[1]
        s.H = max(y + 50, s.pg.winfo_height())
        s.pg.configure(scrollregion=(0, 0, max(s.pg.winfo_width(), 1), s.H))
        s.paint()

    def cw(s):
        w = s.pg.winfo_width()
        return w if w > 200 else 900  # 900 only before the window is first drawn

    def geom(s):  # home = full page; day entry = centred sheet (about 3/5 of the width)
        cw = s.cw()
        m, r = int(84 * K), int(44 * K)
        if s.view is None:
            s.sx, s.SW, s.X = 0, cw, m
            s.W = max(int(320 * K), min(int(cw * .46), cw - m - int(300 * K)))
        else:
            s.SW = min(max(int(cw * .62), int(700 * K)), cw - 20)
            s.sx = max((cw - s.SW) // 2, 0)
            s.X, s.W = s.sx + m, s.SW - m - r

    def paint(s):
        c, cw = s.pg, s.cw()
        c.delete("bg")
        shapes(c, cw, s.H)
        if s.view is not None:
            c.create_rectangle(s.sx + 6, 6, s.sx + s.SW + 6, s.H, fill="#cbbd9f", outline="", tags="bg")
            c.create_rectangle(s.sx, 0, s.sx + s.SW, s.H - 6, fill=PAPER, outline=LINE, width=2, tags="bg")
        for i in range(int(s.H // 520) + 1):
            r = random.Random(i * 13 + 5)
            stain(c, i, s.sx + s.SW * r.uniform(.2, .78), i * 520 + r.uniform(60, 440))
        c.create_line(s.sx + int(60 * K), 0, s.sx + int(60 * K), s.H, fill=MARG, width=2, tags="bg")
        c.tag_lower("bg")
        s.draw_blocks()

    def sync(s, _=None):
        s.geom()
        for i in s.wide + s.texts:
            s.pg.itemconfigure(i, width=s.W)
        s.layout()

    # ----- stone blocks: one per category, stacked like a pyramid; drag one onto another to swap -----
    def draw_blocks(s):
        c = s.pg
        if s.drag:
            return
        c.delete("block"); c.delete("hint"); c.delete("block_note")
        s.slots = []
        cat = s.d["catalog"]
        if s.view is not None or not cat:
            return
        rows = 1
        while rows * (rows + 1) // 2 < len(cat):
            rows += 1
        cw, ch = s.cw(), max(c.winfo_height(), 400)
        left = s.X + s.W + int(30 * K)
        aw = max(cw - left - int(20 * K), int(240 * K))
        gap = max(int(4 * K), 3)
        bw = min(int(170 * K), (aw - (rows - 1) * gap) // rows)
        bh = max(int(bw * .46), int(48 * K))
        total = rows * bh + (rows - 1) * gap
        mid, top, i = left + aw / 2, max((ch - total) // 2, int(40 * K)), 0
        for r in range(rows):
            k = min(r + 1, len(cat) - i)
            x, y = mid - (k * bw + (k - 1) * gap) / 2, top + r * (bh + gap)
            for _ in range(k):
                s.slots.append((x, y, x + bw, y + bh))
                s.block(i, cat[i], x, y, bw, bh)
                x += bw + gap
                i += 1
        c.create_text(mid, top + total + int(22 * K), text="Drag a block onto another to swap places", width=aw,
                      fill=SOFT, font=fp(15), tags="block_note")

    def block(s, i, name, x, y, w, h):
        c, r, tg = s.pg, random.Random(sum(map(ord, name)) * 7 + i), ("block", f"b{i}")
        c.create_rectangle(x, y, x + w, y + h, fill=r.choice(STONES), outline="#6f5f4b", width=2, tags=tg)
        c.create_line(x + 3, y + h - 3, x + 3, y + 3, x + w - 3, y + 3, fill="#e2d6bd", width=2, tags=tg)  # lit edges
        c.create_line(x + w - 3, y + 4, x + w - 3, y + h - 3, x + 3, y + h - 3, fill="#85735c", width=2, tags=tg)  # shaded edges
        for _ in range(2):  # little cracks
            px, py = x + r.uniform(.1, .9) * w, y + r.uniform(.2, .8) * h
            c.create_line(px, py, px + r.uniform(-14, 14) * K, py + r.uniform(-9, 9) * K,
                          px + r.uniform(-20, 20) * K, py + r.uniform(-12, 12) * K, fill="#8f7f68", tags=tg)
        c.create_text(x + w / 2, y + h / 2, text=name, width=w - int(14 * K), justify="center", fill="#2b241c",
                      font=fp(max(12, min(19, int(w / 8.5 / K))), True, True), tags=tg)

    def slot_at(s, x, y, skip=None):
        for j, (x0, y0, x1, y1) in enumerate(s.slots):
            if j != skip and x0 <= x <= x1 and y0 <= y <= y1:
                return j

    def bpress(s, e):
        for t in s.pg.gettags("current"):
            if t[0] == "b" and t[1:].isdigit():
                s.drag = {"i": int(t[1:]), "x": s.pg.canvasx(e.x), "y": s.pg.canvasy(e.y)}
                s.pg.tag_raise(t)
                return

    def bmove(s, e):
        d, c = s.drag, s.pg
        if not d:
            return
        x, y = c.canvasx(e.x), c.canvasy(e.y)
        c.move(f"b{d['i']}", x - d["x"], y - d["y"])
        d["x"], d["y"] = x, y
        c.delete("hint")
        j = s.slot_at(x, y, d["i"])
        if j is not None:
            x0, y0, x1, y1 = s.slots[j]
            c.create_rectangle(x0 - 3, y0 - 3, x1 + 3, y1 + 3, outline=ACC, width=3, dash=(6, 4), tags="hint")

    def brelease(s, e):
        d, s.drag = s.drag, None
        if not d:
            return
        j = s.slot_at(s.pg.canvasx(e.x), s.pg.canvasy(e.y), d["i"])
        if j is not None:
            cat = s.d["catalog"]
            cat[d["i"]], cat[j] = cat[j], cat[d["i"]]
            save(s.d)
        s.draw_blocks()

    # ----- widget helpers -----
    def label(s, p, text, size=12, fg=INK, hand=False, bold=False, bg=PAPER, **k):
        return tk.Label(p, text=text, fg=fg, bg=bg, anchor="w", justify="left",
                        font=fp(size, bold, hand), **k)

    def watch(s, fr, *labels):
        """Let labels wrap to the card's real width, and re-flow the page when the card's height changes."""
        fr._h = fr._cw = None  # (never use the name _w: tkinter keeps the widget's path name in it)

        def on(ev):
            if ev.width != fr._cw:  # ignore plain moves caused by scrolling
                fr._cw = ev.width
                for lb in labels:
                    lb.configure(wraplength=max(ev.width - int(48 * K), 120))
            if fr.winfo_reqheight() != fr._h:
                fr._h = fr.winfo_reqheight()
                s.root.after_idle(s.layout)
        fr.bind("<Configure>", on)

    def button(s, text, cmd, solid=False, p=None):
        return tk.Button(p or s.pg, text=text, command=cmd, relief="flat", cursor="hand2", padx=int(20 * K), pady=int(9 * K),
                         bg=ACC if solid else CARD, fg="white" if solid else ACC,
                         activebackground=ACC, activeforeground="white", font=fp(17))

    def entry_box(s, init, on_change):
        e = tk.Entry(s.pg, font=fp(17), bd=int(8 * K), bg=CARD, fg=INK, relief="flat", highlightthickness=1,
                     highlightbackground=LINE, highlightcolor=ACC, insertbackground=INK)
        e.insert(0, init)
        for ev in ("<KeyRelease>", "<FocusOut>"):
            e.bind(ev, lambda _e: on_change(e.get()))
        return e

    def lined(s, init, on_change, minl=12):
        """Text box that looks like notebook paper: ruled lines, grows as you write."""
        fnt = tkfont.Font(family=BODY, size=-round(17 * K))
        t = tk.Text(s.pg, height=minl, wrap="word", font=fnt, bg="#fffdf6", fg=INK, relief="flat",
                    highlightthickness=1, highlightbackground=LINE, highlightcolor=ACC, padx=12, pady=4,
                    insertbackground=INK, undo=True)
        t.insert("1.0", init)
        t._rules = []

        def refit():
            r = t.count("1.0", "end", "displaylines")
            n = (r[0] if isinstance(r, (tuple, list)) else r) or 1
            if int(t.cget("height")) != max(minl, n + 1):
                t.configure(height=max(minl, n + 1))
                s.root.after_idle(s.layout)

        def draw():
            try:
                for f in t._rules:
                    f.destroy()
                t._rules = []
                b = t.bbox("1.0")
                if not b:
                    return
                ls, y = fnt.metrics("linespace"), b[1] + fnt.metrics("linespace") - 1
                while y < t.winfo_height() - 2:
                    f = tk.Frame(t, bg=RULE, height=1)
                    f.place(x=1, y=y, relwidth=1.0, width=-2)
                    t._rules.append(f)
                    y += ls
            except tk.TclError:
                pass

        def key(_=None):
            on_change(t.get("1.0", "end-1c"))
            refit()
        t.bind("<KeyRelease>", key)

        def edge(n, what="units"):  # inside the writing box: arrows move the cursor, and scroll the page at the top/bottom
            def h(e):
                if (what == "pages" or (n < 0 and t.compare("insert display linestart", "==", "1.0"))
                        or (n > 0 and t.compare("insert display lineend", ">=", "end-1c"))):
                    s.pg.yview_scroll(n, what)
                    return "break"
            return h
        for k, n, what in (("<Up>", -3, "units"), ("<Down>", 3, "units"), ("<Prior>", -1, "pages"), ("<Next>", 1, "pages")):
            t.bind(k, edge(n, what))
        last = [None]

        def resized(e):
            if last[0] != (e.width, e.height):  # ignore plain moves caused by scrolling
                last[0] = (e.width, e.height)
                refit(); s.root.after_idle(draw)
        t.bind("<Configure>", resized)
        s.root.after(60, lambda: (refit(), draw()) if t.winfo_exists() else None)
        return t

    def set_(s, obj, key, val):
        obj[key] = val
        save(s.d)

    def cur(s):
        return next(e for e in s.d["entries"] if e["id"] == s.view)

    # ----- screens -----
    def render(s):
        for w in s.pg.winfo_children():
            w.destroy()
        s.pg.delete("all")
        s.stack, s.wide, s.texts = [], [], []
        s.pg.configure(bg=PAPER if s.view is None else DESK)
        s.geom()
        s.home() if s.view is None else s.entry()
        s.layout()
        s.pg.yview_moveto(0)

    def home(s):
        es = s.d["entries"]
        s.txt("My Diary", 38, gap=0)
        s.txt("Every day, one page.", 17, SOFT, hand=False, bold=False, gap=4)
        n = max([e["day"] for e in es], default=0) + 1
        s.put(s.button(f"+ New entry (Day {n})", s.new_dialog, True), gap=16)
        if not es:
            s.txt("No entries yet. Start your first day!", 17, SOFT, hand=False, bold=False, gap=20)
        for e in sorted(es, key=lambda e: -e["day"]):
            row = tk.Frame(s.pg, bg=CARD, highlightbackground=LINE, highlightthickness=1, cursor="hand2")
            a = s.label(row, f"Day {e['day']}", 32, ACC, hand=True, bold=True, bg=CARD)
            b = s.label(row, fmt(e["created"]), 17, SOFT, bg=CARD, wraplength=max(s.W - int(48 * K), 200))
            names = " · ".join(c["name"] for c in e["cats"]) or "no categories"
            t = s.label(row, names, 16, SOFT, bg=CARD, wraplength=max(s.W - int(48 * K), 200))
            pad, v = int(24 * K), int(20 * K)
            a.pack(anchor="w", padx=pad, pady=(v, 0)); b.pack(anchor="w", padx=pad, pady=(int(8 * K), 0))
            t.pack(anchor="w", padx=pad, pady=(int(10 * K), v)); s.watch(row, b, t)
            for w in (row, a, b, t):
                w.bind("<Button-1>", lambda ev, i=e["id"]: s.open(i))
            s.put(row, gap=16, wide=True)

    def entry(s):
        e = s.cur()
        s.put(s.button("← All days", s.back), gap=0)
        s.txt(f"Day {e['day']}", 34, gap=6)
        s.txt(fmt(e["created"]), 17, SOFT, hand=False, bold=False, gap=4)
        s.put(s.lined(e["summary"], lambda v: s.set_(e, "summary", v)), gap=14, wide=True)
        g = tk.Frame(s.pg, bg=PAPER)
        cols = max(2, min(5, s.W // int(260 * K)))
        for i in range(cols):
            g.columnconfigure(i, weight=1, uniform="c")
        for i in range(len(e["cats"]) // cols + 1):
            g.rowconfigure(i, minsize=int(130 * K))
        for i, c in enumerate(e["cats"] + [None]):
            card = tk.Frame(g, bg=CARD, highlightbackground=LINE, highlightthickness=1, cursor="hand2")
            card.grid(row=i // cols, column=i % cols, sticky="nsew", padx=5, pady=5)
            if c:
                prev = (c["text"][:140] + "…") if len(c["text"]) > 140 else (c["text"] or "Click to write…")
                a = s.label(card, c["name"], 24, ACC, hand=True, bold=True, bg=CARD)
                b = s.label(card, prev, 16, SOFT, bg=CARD, wraplength=int(200 * K))
                cmd = lambda ev, i=c["id"]: s.popup(i)
            else:
                a, b, cmd = s.label(card, "+ Add category", 22, ACC, hand=True, bg=CARD), None, s.add_cat
            p_, v_ = int(20 * K), int(18 * K)
            a.pack(anchor="w", padx=p_, pady=(v_, 0))
            if b:
                b.pack(anchor="w", padx=p_, pady=(8, v_)); s.watch(card, b)
            for w in (card, a, b):
                if w:
                    w.bind("<Button-1>", cmd)
        s.put(g, gap=16, wide=True); s.watch(g)
        s.txt("Conclusion", 28, ACC, gap=18)
        s.put(s.entry_box(e["conclusion"], lambda v: s.set_(e, "conclusion", v)), gap=4, wide=True)
        s.put(s.button("Delete this day", s.delete), gap=26)

    # ----- actions -----
    def new_dialog(s):
        d, es = s.d, s.d["entries"]
        cat = d["catalog"]
        last = max(es, key=lambda e: e["day"])["cats"] if es else []
        vs = {k: tk.BooleanVar(value=any(c["name"] == k for c in last)) for k in cat}
        n = max([e["day"] for e in es], default=0) + 1
        w = tk.Toplevel(s.root); w.title(f"New entry - Day {n}"); w.configure(bg=PAPER, padx=18, pady=14)
        w.transient(s.root); w.grab_set()
        s.label(w, f"Day {n}: choose categories", 28, ACC, hand=True, bold=True).pack(anchor="w")
        s.label(w, "Tick the ones you want. ✕ removes a choice from the list.", 16, SOFT).pack(anchor="w", pady=(0, 8))
        box = tk.Frame(w, bg=PAPER); box.pack(fill="x")

        def build():
            for ch in box.winfo_children():
                ch.destroy()
            for name in cat:
                row = tk.Frame(box, bg=PAPER); row.pack(fill="x", pady=1)
                tk.Checkbutton(row, text=name, variable=vs[name], bg=PAPER, activebackground=PAPER, fg=INK,
                               font=fp(17), anchor="w").pack(side="left", fill="x", expand=True)
                tk.Button(row, text="✕", font=fp(16), relief="flat", bg=PAPER, fg=SOFT, cursor="hand2",
                          command=lambda q=name: drop(q)).pack(side="right")

        def drop(q):
            cat.remove(q); vs.pop(q, None); save(d); build()

        def add(_=None):
            q = ne.get().strip()
            if q and q not in cat:
                cat.append(q); vs[q] = tk.BooleanVar(value=True); save(d)
            elif q in vs:
                vs[q].set(True)
            ne.delete(0, "end"); build()

        def create():
            names = [q for q in cat if vs[q].get()]
            w.destroy(); s.create_entry(names)
        add_row = tk.Frame(w, bg=PAPER); add_row.pack(fill="x", pady=(10, 4))
        ne = tk.Entry(add_row, font=fp(17), bd=int(6 * K), bg=CARD, fg=INK, relief="flat", highlightthickness=1,
                      highlightbackground=LINE, highlightcolor=ACC, insertbackground=INK)
        ne.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
        ne.bind("<Return>", add)
        s.button("+ New category", add, p=add_row).pack(side="right")
        bar = tk.Frame(w, bg=PAPER); bar.pack(fill="x", pady=(12, 0))
        s.button("Cancel", w.destroy, p=bar).pack(side="left")
        s.button("Create day", create, True, p=bar).pack(side="right")
        build(); ne.focus_set()

    def create_entry(s, names):
        es = s.d["entries"]
        e = {"id": uuid.uuid4().hex[:8], "day": max([x["day"] for x in es], default=0) + 1,
             "created": datetime.now().isoformat(timespec="seconds"), "summary": "", "conclusion": "",
             "cats": [mkcat(q) for q in names]}
        es.append(e); save(s.d); s.view = e["id"]; s.render()

    def open(s, i):
        s.view = i; s.render()

    def back(s):
        s.view = None; s.render()

    def delete(s):
        if messagebox.askyesno("Delete", "Delete this day permanently?"):
            s.d["entries"] = [x for x in s.d["entries"] if x["id"] != s.view]
            save(s.d); s.back()

    def add_cat(s, _=None):
        c = mkcat("New category")
        s.cur()["cats"].append(c); save(s.d); s.popup(c["id"], True)

    def popup(s, cid, rename=False):
        e = s.cur(); c = next(x for x in e["cats"] if x["id"] == cid)
        w = tk.Toplevel(s.root); w.title(c["name"]); w.configure(bg=PAPER, padx=14, pady=12)
        w.geometry(f"{int(620 * K)}x{int(540 * K)}"); w.transient(s.root); w.grab_set()
        ent = tk.Entry(w, font=fp(26, True, True), bd=int(6 * K), bg=CARD, fg=ACC, relief="flat", highlightthickness=1,
                       highlightbackground=LINE)
        ent.insert(0, c["name"]); ent.pack(fill="x", ipady=4)
        ent.bind("<KeyRelease>", lambda ev: s.set_(c, "name", ent.get()))
        t = tk.Text(w, height=12, wrap="word", font=fp(17), bg=CARD, fg=INK, relief="flat",
                    highlightthickness=1, highlightbackground=LINE, highlightcolor=ACC, padx=8, pady=6,
                    insertbackground=INK)
        t.insert("1.0", c["text"]); t.pack(fill="both", expand=True, pady=10)
        t.bind("<KeyRelease>", lambda ev: s.set_(c, "text", t.get("1.0", "end-1c")))

        def done():
            w.destroy(); s.render()

        def remove():
            if messagebox.askyesno("Remove", f"Remove '{c['name']}'?", parent=w):
                e["cats"] = [x for x in e["cats"] if x["id"] != cid]; save(s.d); done()
        bar = tk.Frame(w, bg=PAPER); bar.pack(fill="x")
        s.button("Remove category", remove, p=bar).pack(side="left")
        s.button("Done", done, True, p=bar).pack(side="right")
        w.protocol("WM_DELETE_WINDOW", done)
        (ent if rename else t).focus_set()
        if rename:
            ent.select_range(0, "end")


def main():
    global HAND, BODY, K
    try:  # ask Windows not to blur-scale the window; K below then sizes everything properly
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    K = max(1.0, min(2.5, root.winfo_fpixels("1i") / 96), min(2.0, root.winfo_screenheight() / 1080))
    fams = set(tkfont.families())
    HAND = next((f for f in ("Segoe Print", "Bradley Hand", "Comic Sans MS", "Chalkboard SE") if f in fams), "Georgia")
    BODY = next((f for f in ("Georgia", "Palatino Linotype", "Cambria", "Times New Roman") if f in fams), "TkDefaultFont")
    def report(exc, val, tb):
        import traceback
        msg = "".join(traceback.format_exception(exc, val, tb))
        try:
            with open(os.path.join(HERE, "diary_error.log"), "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except OSError:
            pass
        messagebox.showerror("Diary error", "Something went wrong (saved to diary_error.log):\n\n" + msg[-600:])
    root.report_callback_exception = report
    try:
        App(root)
    except Exception:
        import sys
        report(*sys.exc_info())
        return
    root.mainloop()


if __name__ == "__main__":
    main()
