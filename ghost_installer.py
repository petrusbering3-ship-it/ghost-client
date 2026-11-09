"""Ghost client installer: finds your Minecraft folder, installs Fabric if needed, and puts the mod in mods/."""
import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import filedialog

MOD_NAME = "ghost-26.2.jar"
MC_VERSION = "26.2"
TEXT, DIM, ACCENT, ACCENT2, GOOD, BAD, WARN = "#FFFFFF", "#DCE8FF", "#7FB2FF", "#B9D6FF", "#5BE38A", "#FF6B6B", "#FFD24A"
GLASS, FRAME, EDGE = "#2F64DB", "#B9D6FF", "#1C45B8"
FONT = "Consolas" if sys.platform.startswith("win") else "DejaVu Sans Mono"
UA = {"User-Agent": "ghost-installer"}
# Where the newest jar lives. For a GitHub repo use: https://github.com/USER/REPO/releases/latest/download/ghost-26.2.jar
# You can also put the URL alone in a file called update_url.txt next to the exe (no rebuild needed).
UPDATE_URL = ""


def update_url():
    for d in (os.path.dirname(os.path.abspath(sys.argv[0])), os.getcwd()):
        try:
            with open(os.path.join(d, "update_url.txt")) as f:
                u = f.read().strip()
                if u:
                    return u
        except OSError:
            pass
    return UPDATE_URL


def get_latest_jar(say):
    """Downloads the newest jar if an update URL is set. Returns a file path, or None to use the built-in jar."""
    url = update_url()
    if not url:
        return None
    try:
        say("Checking for a newer version online...")
        import tempfile
        tmp = os.path.join(tempfile.mkdtemp(), MOD_NAME)
        with fetch(url, 60) as r, open(tmp, "wb") as out:
            shutil.copyfileobj(r, out)
        if os.path.getsize(tmp) < 50000:
            raise RuntimeError("download too small")
        say("Downloaded the latest version.")
        return tmp
    except Exception as e:
        say("Could not check online (%s). Using the built-in version." % e)
        return None


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base, name)
    return p if os.path.exists(p) else os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def default_mc():
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), ".minecraft")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/minecraft")
    return os.path.expanduser("~/.minecraft")


def has(folder, prefix):
    try:
        return any(f.lower().startswith(prefix) and f.endswith(".jar") for f in os.listdir(folder))
    except OSError:
        return False


def has_fabric(mc):
    try:
        return any(d.startswith("fabric-loader-") and d.endswith(MC_VERSION) for d in os.listdir(os.path.join(mc, "versions")))
    except OSError:
        return False


def fetch(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def install_mod(mc, with_api, say, progress):
    mods = os.path.join(mc, "mods")
    os.makedirs(mods, exist_ok=True)
    say("Removing old Ghost versions...")
    for f in os.listdir(mods):
        if f.lower().startswith("ghost") and f.endswith(".jar"):
            os.remove(os.path.join(mods, f))
    progress(15)
    say("Copying Ghost client...")
    src = get_latest_jar(say) or resource(MOD_NAME)
    if not os.path.exists(src):
        raise RuntimeError("the mod jar is missing from this installer")
    shutil.copyfile(src, os.path.join(mods, MOD_NAME))
    progress(55)
    if with_api and not has(mods, "fabric-api"):
        say("Downloading Fabric API...")
        url = ("https://api.modrinth.com/v2/project/fabric-api/version?game_versions=%5B%22" + MC_VERSION + "%22%5D&loaders=%5B%22fabric%22%5D")
        versions = json.load(fetch(url))
        if not versions:
            raise RuntimeError("no Fabric API build for " + MC_VERSION + " yet")
        files = versions[0]["files"]
        f = next((x for x in files if x.get("primary")), files[0])
        with fetch(f["url"], 120) as r, open(os.path.join(mods, f["filename"]), "wb") as out:
            shutil.copyfileobj(r, out)
    progress(100)
    say("Done. Start Minecraft with the Fabric profile.")


def launch_game(say):
    """Starts the Minecraft launcher. Pick the Fabric profile and press Play."""
    if sys.platform.startswith("win"):
        pf, pf86 = os.environ.get("ProgramFiles", r"C:\\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")
        for p in (pf86 + r"\\Minecraft Launcher\\MinecraftLauncher.exe", pf + r"\\Minecraft Launcher\\MinecraftLauncher.exe",
                  os.path.expandvars(r"%LOCALAPPDATA%\\Packages\\Microsoft.4297127D64EC6_8wekyb3d8bbwe\\LocalCache\\Local\\runtime")):
            if os.path.isfile(p):
                subprocess.Popen([p]); say("Launcher started. Choose the Fabric profile and press Play."); return
        try:
            subprocess.Popen(["explorer.exe", "shell:AppsFolder\\Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft"])
            say("Launcher started. Choose the Fabric profile and press Play."); return
        except OSError:
            pass
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "Minecraft"]); say("Launcher started."); return
    else:
        for c in ("minecraft-launcher", "prismlauncher"):
            if shutil.which(c):
                subprocess.Popen([c]); say("Launcher started."); return
    say("Could not find the launcher. Open it yourself.")


def update_and_play(mc, with_api, say, progress):
    if not has_fabric(mc):
        install_fabric(mc, say, lambda v: progress(v // 2))
    install_mod(mc, with_api, say, lambda v: progress(50 + v // 2))
    launch_game(say)


def install_fabric(mc, say, progress):
    say("Looking up the latest Fabric installer...")
    inst = json.load(fetch("https://meta.fabricmc.net/v2/versions/installer"))
    iv = next(i for i in inst if i.get("stable"))["version"]
    loaders = json.load(fetch("https://meta.fabricmc.net/v2/versions/loader/" + MC_VERSION))
    lv = next(l for l in loaders if l["loader"].get("stable", True))["loader"]["version"]
    jar = os.path.join(os.environ.get("TEMP", "/tmp"), "fabric-installer.jar")
    say("Downloading Fabric installer " + iv + "...")
    with fetch("https://maven.fabricmc.net/net/fabricmc/fabric-installer/%s/fabric-installer-%s.jar" % (iv, iv), 120) as r, open(jar, "wb") as out:
        shutil.copyfileobj(r, out)
    progress(50)
    java = shutil.which("java") or shutil.which("javaw")
    if not java:
        raise RuntimeError("Java 25 is not installed or not on PATH (https://adoptium.net/temurin/releases/?version=25)")
    say("Installing Fabric Loader " + lv + "...")
    out = subprocess.run([java, "-jar", jar, "client", "-dir", mc, "-mcversion", MC_VERSION, "-loader", lv], capture_output=True, text=True, timeout=300)
    if out.returncode != 0:
        raise RuntimeError("Fabric installer failed: " + (out.stderr or out.stdout)[-200:])
    progress(100)
    say("Fabric Loader installed. Now press Install to add the mod.")


def uninstall_mod(mc, say):
    mods = os.path.join(mc, "mods")
    n = 0
    if os.path.isdir(mods):
        for f in os.listdir(mods):
            if f.lower().startswith("ghost") and f.endswith(".jar"):
                os.remove(os.path.join(mods, f))
                n += 1
    say("Ghost client removed." if n else "Ghost client was not installed.")


import random
import time


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(ca[k] + (cb[k] - ca[k]) * t) for k in range(3))


TILE = 12


class App:
    W = 540

    def __init__(self):
        self.root = r = tk.Tk()
        r.title("Ghost Installer")
        r.overrideredirect(True)
        W = self.W
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        r.geometry("%dx%d+%d+%d" % (W, W, (sw - W) // 2, (sh - W) // 2))
        r.configure(bg="#10131c")
        self.cv = cv = tk.Canvas(r, width=W, height=W, bg="#10131c", highlightthickness=0)
        cv.pack()
        self.t0 = time.time()
        self.hover = None
        self.buttons = []
        self.make_backdrop()

        self.drag = (0, 0)
        cv.bind("<Button-1>", lambda e: setattr(self, "drag", (e.x_root - r.winfo_x(), e.y_root - r.winfo_y())))
        cv.bind("<B1-Motion>", lambda e: r.geometry("+%d+%d" % (e.x_root - self.drag[0], e.y_root - self.drag[1])))

        # big window pane
        self.pane(10, 10, W - 20, W - 20, 0.42)

        # title
        cv.create_text(46, 62, text="GHOST", anchor="w", fill="#10286e", font=(FONT, 34, "bold"))
        cv.create_text(44, 60, text="GHOST", anchor="w", fill=TEXT, font=(FONT, 34, "bold"))
        cv.create_text(46, 100, text="Client installer  -  Minecraft %s  -  Fabric" % MC_VERSION, anchor="w", fill=DIM, font=(FONT, 10))
        cv.create_rectangle(46, 118, 130, 120, fill=FRAME, outline="")
        x = cv.create_text(W - 38, 34, text="X", fill=DIM, font=(FONT, 13, "bold"))
        cv.tag_bind(x, "<Button-1>", lambda e: self.close())
        cv.tag_bind(x, "<Enter>", lambda e: cv.itemconfig(x, fill=TEXT))
        cv.tag_bind(x, "<Leave>", lambda e: cv.itemconfig(x, fill=DIM))

        # path
        cv.create_text(46, 144, text="MINECRAFT FOLDER", anchor="w", fill=DIM, font=(FONT, 8, "bold"))
        self.pane(44, 156, 340, 34, 0.7)
        self.path = tk.StringVar(value=default_mc())
        e = tk.Entry(cv, textvariable=self.path, bg="#27479a", fg=TEXT, insertbackground=TEXT, relief="flat", font=(FONT, 10), highlightthickness=0)
        cv.create_window(52, 163, window=e, anchor="nw", width=324, height=20)
        e.bind("<Return>", lambda ev: self.refresh())
        self.button(392, 156, 62, 34, "Browse", self.browse)
        self.button(460, 156, 56, 34, "Detect", self.detect)

        # status pane
        self.pane(44, 206, W - 88, 138, 0.5)
        self.rows = []
        for i in range(4):
            y = 230 + i * 30
            self.cv.create_rectangle(58, y - 6, 70, y + 6, fill=DIM, outline=EDGE)
            dot = self.cv.create_rectangle(58, y - 6, 70, y + 6, fill=DIM, outline=FRAME)
            cv.create_line(60, y - 4, 64, y - 4, fill="#FFFFFF")
            txt = cv.create_text(84, y, text="", anchor="w", fill=TEXT, font=(FONT, 10))
            self.rows.append((dot, txt))

        # option switch
        self.api = tk.BooleanVar(value=True)
        self.sw_x, self.sw_y = 46, 360
        self.sw_track = cv.create_rectangle(self.sw_x, self.sw_y, self.sw_x + 38, self.sw_y + 18, fill="#3d7bff", outline=FRAME)
        self.sw_knob = cv.create_rectangle(self.sw_x + 22, self.sw_y + 2, self.sw_x + 36, self.sw_y + 16, fill="#FFFFFF", outline=EDGE)
        lab = cv.create_text(94, self.sw_y + 9, text="Download Fabric API if it is missing", anchor="w", fill=TEXT, font=(FONT, 10))
        for it in (self.sw_track, self.sw_knob, lab):
            cv.tag_bind(it, "<Button-1>", lambda ev: self.toggle_api())

        # progress
        self.pane(44, 400, W - 88, 14, 0.75)
        self.bar = cv.create_rectangle(47, 403, 47, 411, fill=ACCENT2, outline="")
        self.bar_shine = cv.create_rectangle(47, 403, 47, 406, fill="#FFFFFF", outline="")
        self.log = cv.create_text(46, 432, text="Ready.", anchor="w", fill=DIM, font=(FONT, 9))
        link = cv.create_text(W - 46, self.sw_y + 9, text="Get Java 25", anchor="e", fill=ACCENT2, font=(FONT, 9, "bold"))
        cv.tag_bind(link, "<Button-1>", lambda e: webbrowser.open("https://adoptium.net/temurin/releases/?version=25"))
        cv.tag_bind(link, "<Enter>", lambda e: cv.config(cursor="hand2"))
        cv.tag_bind(link, "<Leave>", lambda e: cv.config(cursor=""))

        # buttons
        self.install_btn = self.button(44, 452, 166, 52, "INSTALL + PLAY", self.do_install, primary=True)
        self.fabric_btn = self.button(216, 452, 92, 52, "Fabric", self.do_fabric)
        self.button(314, 452, 92, 52, "Remove", self.do_uninstall)
        self.button(412, 452, 104, 52, "Folder", self.open_folder)

        self.refresh()
        try:
            r.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        self.animate()

    # ---- blue stained glass drawing ----
    def make_backdrop(self):
        """A deepslate-and-ore pixel wall: the glass panes blend with it, so they look see-through."""
        rnd = random.Random(26)
        n = self.W // TILE + 1
        self.tiles = {}
        for ty in range(n):
            for tx in range(n):
                v = rnd.random()
                base = mix("#1b1f2a", "#3a4254", rnd.random() * 0.8)
                if v > 0.965:
                    base = rnd.choice(["#35e0e8", "#e8c53a", "#d94a4a", "#5aa0ff"])
                elif v > 0.9:
                    base = mix(base, "#0a0c12", 0.5)
                self.tiles[(tx, ty)] = base
                self.cv.create_rectangle(tx * TILE, ty * TILE, tx * TILE + TILE, ty * TILE + TILE, fill=base, outline=mix(base, "#000000", 0.3))

    def pane(self, x, y, w, h, tint):
        """Stained glass: every backdrop tile under the pane is tinted blue, then a light frame, a dark inner edge and shine."""
        cv = self.cv
        for ty in range(y // TILE, (y + h - 1) // TILE + 1):
            for tx in range(x // TILE, (x + w - 1) // TILE + 1):
                x1, y1 = max(x, tx * TILE), max(y, ty * TILE)
                x2, y2 = min(x + w, tx * TILE + TILE), min(y + h, ty * TILE + TILE)
                if x2 > x1 and y2 > y1:
                    base = self.tiles.get((tx, ty), "#20242f")
                    cv.create_rectangle(x1, y1, x2, y2, fill=mix(base, GLASS, tint), outline="")
        cv.create_rectangle(x, y, x + w, y + h, outline=FRAME, width=1)
        cv.create_rectangle(x + 1, y + 1, x + w - 1, y + h - 1, outline=mix(GLASS, EDGE, 0.8), width=1)
        if h > 16:
            for k in range(min(5, max(2, h // 6))):
                cv.create_line(x + 2, y + 2 + k, x + w - 2, y + 2 + k, fill=mix(GLASS, "#FFFFFF", max(0.0, 0.14 - k * 0.03)))
        if w > 30 and h > 16:
            for k in range(5):
                cv.create_rectangle(x + 4 + k, y + 9 - k, x + 5 + k, y + 10 - k, fill="#FFFFFF", outline="")
            for k in range(3):
                cv.create_rectangle(x + 12 + k, y + 7 - k, x + 13 + k, y + 8 - k, fill="#DCE8FF", outline="")

    def button(self, x, y, w, h, text, cmd, primary=False):
        cv = self.cv
        base = mix(GLASS, "#FFFFFF", 0.18) if primary else mix("#20242f", GLASS, 0.62)
        b = {"cmd": cmd, "primary": primary, "enabled": True, "base": base, "items": []}
        b["body"] = cv.create_rectangle(x, y, x + w, y + h, fill=base, outline=FRAME)
        b["inner"] = cv.create_rectangle(x + 1, y + 1, x + w - 1, y + h - 1, outline=mix(base, EDGE, 0.8))
        for k in range(h // 4):
            b["items"].append(cv.create_line(x + 2, y + 2 + k, x + w - 2, y + 2 + k, fill=mix(base, "#FFFFFF", max(0.0, (0.28 if primary else 0.16) - k * 0.03))))
        for k in range(4):
            b["items"].append(cv.create_rectangle(x + 4 + k, y + 8 - k, x + 5 + k, y + 9 - k, fill="#FFFFFF", outline=""))
        b["label"] = cv.create_text(x + w / 2, y + h / 2, text=text, fill=TEXT, font=(FONT, 13 if primary else 10, "bold"))
        for it in [b["body"], b["inner"], b["label"]] + b["items"]:
            cv.tag_bind(it, "<Button-1>", lambda e, bb=b: bb["enabled"] and bb["cmd"]())
            cv.tag_bind(it, "<Enter>", lambda e, bb=b: self.set_hover(bb))
            cv.tag_bind(it, "<Leave>", lambda e: self.set_hover(None))
        self.buttons.append(b)
        return b

    def set_hover(self, b):
        self.hover = b
        self.cv.config(cursor="hand2" if b else "")
        for bb in self.buttons:
            self.cv.itemconfig(bb["body"], fill=mix(bb["base"], "#FFFFFF", 0.14) if bb is b else bb["base"])

    def toggle_api(self):
        self.api.set(not self.api.get())
        on = self.api.get()
        self.cv.itemconfig(self.sw_track, fill="#3d7bff" if on else "#26345f")
        x, y = self.sw_x, self.sw_y
        self.cv.coords(self.sw_knob, x + (22 if on else 2), y + 2, x + (36 if on else 16), y + 16)

    def animate(self):
        t = time.time() - self.t0
        try:
            self.root.attributes("-alpha", min(0.96, t / 0.5))
        except tk.TclError:
            pass
        if t < 1.0:
            self.root.after(33, self.animate)

    def close(self):
        self.root.destroy()

    # ---- state ----
    def mc(self):
        return self.path.get().strip()

    def say(self, s):
        self.root.after(0, lambda: self.cv.itemconfig(self.log, text=s))

    def prog(self, v):
        def draw():
            w = int((self.W - 94) * v / 100)
            self.cv.coords(self.bar, 47, 403, 47 + w, 411)
            self.cv.coords(self.bar_shine, 47, 403, 47 + w, 406)

        self.root.after(0, draw)

    def set_row(self, i, color, text):
        dot, txt = self.rows[i]
        self.cv.itemconfig(dot, fill=color)
        self.cv.itemconfig(txt, text=text)

    def refresh(self):
        mc = self.mc()
        ok = os.path.isdir(mc)
        self.set_row(0, GOOD if ok else BAD, "Minecraft folder found" if ok else "Minecraft folder not found")
        fab = ok and has_fabric(mc)
        self.set_row(1, GOOD if fab else WARN, "Fabric Loader for %s installed" % MC_VERSION if fab else "Fabric Loader for %s missing (press Fabric)" % MC_VERSION)
        api = ok and has(os.path.join(mc, "mods"), "fabric-api")
        self.set_row(2, GOOD if api else WARN, "Fabric API installed" if api else "Fabric API will be downloaded")
        gh = ok and has(os.path.join(mc, "mods"), "ghost")
        self.set_row(3, GOOD if gh else DIM, "Ghost client installed (Install updates it)" if gh else "Ghost client not installed yet")
        self.cv.itemconfig(self.install_btn["label"], text="UPDATE + PLAY" if gh else "INSTALL + PLAY")

    def browse(self):
        d = filedialog.askdirectory(initialdir=self.mc() or None)
        if d:
            self.path.set(d)
            self.refresh()

    def detect(self):
        self.path.set(default_mc())
        self.refresh()

    def run(self, fn):
        self.install_btn["enabled"] = False

        def job():
            try:
                fn()
            except Exception as e:
                self.say("Error: %s" % e)
            self.root.after(0, lambda: (self.install_btn.__setitem__("enabled", True), self.refresh()))

        t = threading.Thread(target=job, daemon=True)
        t.start()
        return t

    def do_install(self):
        return self.run(lambda: update_and_play(self.mc(), self.api.get(), self.say, self.prog))

    def do_fabric(self):
        return self.run(lambda: install_fabric(self.mc(), self.say, self.prog))

    def do_uninstall(self):
        return self.run(lambda: uninstall_mod(self.mc(), self.say))

    def open_folder(self):
        mods = os.path.join(self.mc(), "mods")
        os.makedirs(mods, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(mods)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", mods])
        else:
            subprocess.Popen(["xdg-open", mods])


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--install":
        install_mod(sys.argv[2], "--api" in sys.argv, print, lambda v: None)
    else:
        App().root.mainloop()
