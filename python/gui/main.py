"""
PlanetHack GUI - Cyberpunk HUD
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import threading
import random
import time
from typing import Optional, List, Dict, Any

from utils.helpers import is_ip_address, validate_url
from core.recon_plan import build_recon_plan
from core.tool_runner import resolve_tool_command, run_tool, run_tools_sequential
from core.session import SessionLog
from modules import MODULE_REGISTRY

# ── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "bg":           "#0a0a0a",
    "bg_panel":     "#0d1117",
    "bg_input":     "#111820",
    "fg":           "#00ff41",
    "fg_dim":       "#00aa28",
    "fg_bright":    "#33ff66",
    "cyan":         "#00ffff",
    "cyan_dim":     "#00aaaa",
    "magenta":      "#ff00ff",
    "magenta_dim":  "#aa00aa",
    "yellow":       "#ffff00",
    "red":          "#ff0040",
    "orange":       "#ff8800",
    "white":        "#e0e0e0",
    "border":       "#00ff41",
    "border_dim":   "#004d14",
    "glow":         "#003311",
}

MOVIE_QUOTES = [
    ("Hack the Planet!", "Hackers"),
    ("Mess with the best, die like the rest.", "Hackers"),
    ("There is no right and wrong. There's only fun and boring.", "Hackers"),
    ("Type 'cookie', you idiot.", "Hackers"),
    ("God gave men brains larger than dogs' so they wouldn't hump women's legs at cocktail parties.", "Hackers"),
    ("The password is... swordfish.", "Swordfish"),
    ("Nothing is impossible.", "Swordfish"),
    ("Anybody wanna shut down the DOD?", "Swordfish"),
    ("Follow the white rabbit.", "The Matrix"),
    ("There is no spoon.", "The Matrix"),
    ("I know kung fu.", "The Matrix"),
    ("Welcome to the real world.", "The Matrix"),
    ("Free your mind.", "The Matrix"),
    ("The Matrix has you...", "The Matrix"),
    ("Unfortunately, no one can be told what the Matrix is.", "The Matrix"),
    ("Guns. Lots of guns.", "The Matrix"),
    ("Not like this... not like this.", "The Matrix"),
    ("Do not try and bend the spoon. That's impossible.", "The Matrix"),
]

ASCII_BANNER = r"""
  ██████╗ ██╗      █████╗ ███╗   ██╗███████╗████████╗
  ██╔══██╗██║     ██╔══██╗████╗  ██║██╔════╝╚══██╔══╝
  ██████╔╝██║     ███████║██╔██╗ ██║█████╗     ██║
  ██╔═══╝ ██║     ██╔══██║██║╚██╗██║██╔══╝     ██║
  ██║     ███████╗██║  ██║██║ ╚████║███████╗   ██║
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝

  ██╗  ██╗ █████╗  ██████╗██╗  ██╗
  ██║  ██║██╔══██╗██╔════╝██║ ██╔╝
  ███████║███████║██║     █████╔╝
  ██╔══██║██╔══██║██║     ██╔═██╗
  ██║  ██║██║  ██║╚██████╗██║  ██╗
  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

MATRIX_CHARS = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "@#$%&*<>{}[]|/\\~^"
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
)


# ── Matrix Rain ──────────────────────────────────────────────────────────────

class MatrixRain:
    """Canvas-based falling-code rain effect."""

    def __init__(self, canvas: tk.Canvas, density: int = 28, speed: int = 55):
        self.canvas = canvas
        self.density = density
        self.speed = speed
        self._running = False
        self._columns: List[dict] = []
        self._job_id: Optional[str] = None
        self.canvas.bind("<Configure>", self._on_resize)

    def _init_columns(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return
        col_w = max(14, w // self.density)
        self._columns = []
        for x in range(0, w, col_w):
            self._columns.append({
                "x": x,
                "y": random.randint(-h, 0),
                "speed": random.randint(8, 22),
                "chars": [random.choice(MATRIX_CHARS) for _ in range(random.randint(6, 22))],
                "length": random.randint(6, 22),
            })

    def _on_resize(self, _event=None):
        if self._running:
            self._init_columns()

    def start(self):
        if self._running:
            return
        self._running = True
        self._init_columns()
        self._tick()

    def stop(self):
        self._running = False
        if self._job_id:
            self.canvas.after_cancel(self._job_id)
            self._job_id = None

    def _tick(self):
        if not self._running:
            return
        c = self.canvas
        c.delete("rain")
        h = c.winfo_height()
        for col in self._columns:
            x = col["x"]
            y = col["y"]
            chars = col["chars"]
            for i, ch in enumerate(chars):
                cy = y + i * 16
                if cy < -20 or cy > h + 20:
                    continue
                if random.random() < 0.08:
                    chars[i] = random.choice(MATRIX_CHARS)
                    ch = chars[i]
                if i == len(chars) - 1:
                    color = "#ffffff"
                elif i >= len(chars) - 3:
                    color = COLORS["fg_bright"]
                elif i >= len(chars) // 2:
                    color = COLORS["fg"]
                else:
                    color = COLORS["fg_dim"]
                c.create_text(
                    x, cy, text=ch, fill=color,
                    font=("Courier", 11), anchor="nw", tags="rain",
                )
            col["y"] += col["speed"]
            if col["y"] > h + 40:
                col["y"] = random.randint(-h // 2, -20)
                col["speed"] = random.randint(8, 22)
                col["chars"] = [random.choice(MATRIX_CHARS) for _ in range(random.randint(6, 22))]
        self._job_id = c.after(self.speed, self._tick)


# ── Neon Button ──────────────────────────────────────────────────────────────

class NeonButton(tk.Canvas):
    """Hand-drawn neon-bordered button with hover glow."""

    def __init__(
        self, parent, text="", command=None, width=180, height=38,
        fg=COLORS["cyan"], border=COLORS["cyan"], bg=COLORS["bg_panel"],
        hover_fg="#ffffff", hover_border=COLORS["magenta"],
        font=("Courier New", 10, "bold"), **kw,
    ):
        super().__init__(
            parent, width=width, height=height,
            bg=bg, highlightthickness=0, cursor="hand2", **kw,
        )
        self._text = text
        self._command = command
        self._fg = fg
        self._border = border
        self._bg = bg
        self._hover_fg = hover_fg
        self._hover_border = hover_border
        self._font = font
        self._pressed = False
        self._draw(fg, border)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, fg, border):
        self.delete("all")
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.create_rectangle(2, 2, w - 2, h - 2, outline=border, width=2, tags="border")
        self.create_rectangle(4, 4, w - 4, h - 4, outline=border, width=1, dash=(2, 4), tags="inner")
        self.create_text(w // 2, h // 2, text=self._text, fill=fg, font=self._font, tags="label")

    def _on_enter(self, _e):
        self._draw(self._hover_fg, self._hover_border)

    def _on_leave(self, _e):
        self._draw(self._fg, self._border)
        self._pressed = False

    def _on_press(self, _e):
        self._pressed = True
        self._draw(self._bg, self._hover_border)

    def _on_release(self, _e):
        if self._pressed and self._command:
            self._command()
        self._pressed = False
        self._draw(self._fg, self._border)

    def configure_text(self, text):
        self._text = text
        self._draw(self._fg, self._border)


# ── CRT Scanline Overlay ────────────────────────────────────────────────────

def apply_scanlines(canvas: tk.Canvas, spacing: int = 4, alpha_hex: str = "#000000"):
    """Draw faint horizontal scanlines for a CRT monitor look."""
    canvas.delete("scanline")
    h = canvas.winfo_height()
    w = canvas.winfo_width()
    for y in range(0, h, spacing):
        canvas.create_line(0, y, w, y, fill=alpha_hex, stipple="gray12", tags="scanline")


# ── Main GUI ─────────────────────────────────────────────────────────────────

class PlanetHackGUI:
    """Main GUI application."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.root = tk.Tk()
        self.recon_phases: List[Dict[str, Any]] = []
        self._rain: Optional[MatrixRain] = None
        self._quote_job: Optional[str] = None
        self._header_job: Optional[str] = None
        self._header_idx = 0
        self._terminal_sessions: Dict[str, Dict] = {}
        self._active_session: Optional[str] = None
        self._session_counter = 0
        self.session_log = SessionLog()
        self.setup_window()
        self.create_widgets()
        self._start_header_cycle()

    # ── Window Setup ─────────────────────────────────────────────────────

    def setup_window(self):
        self.root.title("PLANETHACK // HACK THE PLANET")
        self.root.geometry("1280x850")
        self.root.minsize(960, 600)
        self.root.configure(bg=COLORS["bg"])

        try:
            self.root.attributes("-alpha", 0.97)
        except tk.TclError:
            pass

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Cyber.TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["bg_panel"])

        style.configure(
            "Cyber.TLabel", background=COLORS["bg"],
            foreground=COLORS["fg"], font=("Courier New", 10),
        )
        style.configure(
            "CyberBright.TLabel", background=COLORS["bg"],
            foreground=COLORS["cyan"], font=("Courier New", 10, "bold"),
        )
        style.configure(
            "CyberDim.TLabel", background=COLORS["bg"],
            foreground=COLORS["fg_dim"], font=("Courier New", 9),
        )
        style.configure(
            "Header.TLabel", background=COLORS["bg"],
            foreground=COLORS["cyan"], font=("Courier New", 14, "bold"),
        )
        style.configure(
            "Cyber.TButton", background=COLORS["bg_panel"],
            foreground=COLORS["cyan"], font=("Courier New", 10, "bold"),
            borderwidth=1,
        )
        style.map(
            "Cyber.TButton",
            background=[("active", COLORS["glow"])],
            foreground=[("active", COLORS["magenta"])],
        )
        style.configure(
            "Green.TButton", background=COLORS["bg_panel"],
            foreground=COLORS["fg"], font=("Courier New", 10, "bold"),
            borderwidth=1,
        )
        style.map(
            "Green.TButton",
            background=[("active", COLORS["glow"])],
            foreground=[("active", COLORS["fg_bright"])],
        )

        style.configure(
            "Cyber.TNotebook", background=COLORS["bg"], borderwidth=0,
        )
        style.configure(
            "Cyber.TNotebook.Tab",
            background=COLORS["bg_panel"], foreground=COLORS["cyan"],
            font=("Courier New", 10, "bold"), padding=[14, 6],
        )
        style.map(
            "Cyber.TNotebook.Tab",
            background=[("selected", COLORS["bg"]), ("active", COLORS["glow"])],
            foreground=[("selected", COLORS["fg"]), ("active", COLORS["magenta"])],
        )

        style.configure(
            "Cyber.TEntry",
            fieldbackground=COLORS["bg_input"], foreground=COLORS["fg"],
            insertcolor=COLORS["fg"], font=("Courier New", 11),
            borderwidth=1,
        )
        style.configure(
            "Cyber.TRadiobutton",
            background=COLORS["bg"], foreground=COLORS["cyan"],
            font=("Courier New", 10),
        )
        style.map(
            "Cyber.TRadiobutton",
            foreground=[("active", COLORS["magenta"])],
            background=[("active", COLORS["bg"])],
        )
        style.configure(
            "Cyber.TLabelframe", background=COLORS["bg_panel"],
            foreground=COLORS["cyan"], font=("Courier New", 10, "bold"),
        )
        style.configure(
            "Cyber.TLabelframe.Label",
            background=COLORS["bg_panel"], foreground=COLORS["cyan"],
            font=("Courier New", 10, "bold"),
        )

    # ── Widget Creation ──────────────────────────────────────────────────

    def create_widgets(self):
        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        border_top = tk.Frame(outer, bg=COLORS["border_dim"], height=2)
        border_top.pack(fill=tk.X)

        header_frame = tk.Frame(outer, bg=COLORS["bg"])
        header_frame.pack(fill=tk.X, padx=12, pady=(8, 2))

        self.header_label = tk.Label(
            header_frame, text="[ PLANETHACK ]",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 16, "bold"),
        )
        self.header_label.pack(side=tk.LEFT)

        self.quote_label = tk.Label(
            header_frame, text="",
            bg=COLORS["bg"], fg=COLORS["fg_dim"],
            font=("Courier New", 9, "italic"),
        )
        self.quote_label.pack(side=tk.RIGHT, padx=10)
        self._cycle_quote()

        border_mid = tk.Frame(outer, bg=COLORS["border_dim"], height=1)
        border_mid.pack(fill=tk.X, padx=12, pady=(4, 0))

        self.notebook = ttk.Notebook(outer, style="Cyber.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 0))

        self.home_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.home_frame, text="  HOME  ")
        self.create_welcome_screen()

        self.recon_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.recon_frame, text="  RECON  ")

        self.modules_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.modules_frame, text="  MODULES  ")
        self.create_modules_tab()

        self.last_report_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.last_report_frame, text="  REPORT HISTORY  ")

        self.terminal_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.terminal_frame, text="  TERMINAL  ")
        self.create_terminal_tab()

        self.settings_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.settings_frame, text="  ABOUT  ")
        self.create_settings_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        border_bot = tk.Frame(outer, bg=COLORS["border_dim"], height=1)
        border_bot.pack(fill=tk.X, padx=12, pady=(0, 2))

        status_frame = tk.Frame(outer, bg=COLORS["bg"])
        status_frame.pack(fill=tk.X, padx=12, pady=(0, 6))

        tk.Label(
            status_frame, text="STATUS >",
            bg=COLORS["bg"], fg=COLORS["cyan_dim"],
            font=("Courier New", 9, "bold"),
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="SYSTEM ONLINE -- READY")
        self.status_label = tk.Label(
            status_frame, textvariable=self.status_var,
            bg=COLORS["bg"], fg=COLORS["fg"],
            font=("Courier New", 9),
            anchor="w",
        )
        self.status_label.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)

        border_bottom = tk.Frame(outer, bg=COLORS["border_dim"], height=2)
        border_bottom.pack(fill=tk.X)

    # ── Header Animation ─────────────────────────────────────────────────

    _HEADER_FRAMES = [
        ("[ PLANETHACK ]", COLORS["cyan"]),
        ("[ PLANETHACK ]", COLORS["fg"]),
        ("// HACK THE PLANET //", COLORS["magenta"]),
        ("// HACK THE PLANET //", COLORS["cyan"]),
        ("< PLANETHACK MODE >", COLORS["orange"]),
        ("< PLANETHACK MODE >", COLORS["yellow"]),
        ("// HACK THE PLANET //", COLORS["fg"]),
        ("// HACK THE PLANET //", COLORS["fg_bright"]),
        ("[ PLANETHACK ]", COLORS["cyan"]),
        ("[ PLANETHACK ]", COLORS["cyan"]),
    ]

    def _start_header_cycle(self):
        self._header_idx = 0
        self._tick_header()

    def _tick_header(self):
        text, color = self._HEADER_FRAMES[self._header_idx % len(self._HEADER_FRAMES)]
        self.header_label.configure(text=text, fg=color)
        self._header_idx += 1
        self._header_job = self.root.after(2400, self._tick_header)

    # ── Quote Rotation ───────────────────────────────────────────────────

    def _cycle_quote(self):
        q, movie = random.choice(MOVIE_QUOTES)
        self.quote_label.configure(text=f'"{q}"  -- {movie}')
        self._quote_job = self.root.after(8000, self._cycle_quote)

    # ── Tab Changed ──────────────────────────────────────────────────────

    def _on_tab_changed(self, _event=None):
        selected = self.notebook.index(self.notebook.select())
        if selected == 0:
            if self._rain:
                self._rain.start()
        else:
            if self._rain:
                self._rain.stop()
        if selected == 1 and not self.recon_frame.winfo_children():
            self.create_recon_input_screen()
        if selected == 2:
            self.create_last_report_screen()

    # ── HOME TAB ─────────────────────────────────────────────────────────

    def create_welcome_screen(self):
        for w in self.home_frame.winfo_children():
            w.destroy()

        rain_canvas = tk.Canvas(
            self.home_frame, bg=COLORS["bg"], highlightthickness=0,
        )
        rain_canvas.pack(fill=tk.BOTH, expand=True)

        self._rain = MatrixRain(rain_canvas, density=30, speed=60)

        overlay = tk.Frame(rain_canvas, bg=COLORS["bg"])
        rain_canvas.create_window(0, 0, window=overlay, anchor="nw", tags="overlay")

        def _reposition_overlay(_e=None):
            cw = rain_canvas.winfo_width()
            ch = rain_canvas.winfo_height()
            rain_canvas.coords(
                rain_canvas.find_withtag("overlay")[0],
                cw // 2, ch // 2,
            )
            rain_canvas.itemconfigure("overlay", anchor="center")

        rain_canvas.bind("<Configure>", lambda e: (_reposition_overlay(e), self._rain._on_resize(e)))

        banner_label = tk.Label(
            overlay, text=ASCII_BANNER, bg=COLORS["bg"], fg=COLORS["fg"],
            font=("Courier New", 9), justify="left",
        )
        banner_label.pack(pady=(10, 4))

        tagline = tk.Label(
            overlay,
            text="//  CTF & BUG BOUNTY TOOLKIT  //",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 10, "bold"),
        )
        tagline.pack(pady=(0, 12))

        divider = tk.Label(
            overlay,
            text="━" * 58,
            bg=COLORS["bg"], fg=COLORS["border_dim"],
            font=("Courier New", 10),
        )
        divider.pack(pady=(0, 8))

        prompt = tk.Label(
            overlay,
            text="WHAT DO YOU WANT TO DO?",
            bg=COLORS["bg"], fg=COLORS["magenta"],
            font=("Courier New", 13, "bold"),
        )
        prompt.pack(pady=(0, 14))

        btn_frame = tk.Frame(overlay, bg=COLORS["bg"])
        btn_frame.pack(pady=4)

        recon_btn = NeonButton(
            btn_frame, text="RECON",
            width=280, height=44,
            fg=COLORS["fg"], border=COLORS["fg"],
            command=self.on_recon_click,
            font=("Courier New", 11, "bold"),
        )
        recon_btn.grid(row=0, column=0, padx=12, pady=10)

        browse_btn = NeonButton(
            btn_frame, text=">> BROWSE OTHER MODULES <<",
            width=280, height=44,
            fg=COLORS["yellow"], border=COLORS["yellow"],
            command=self.on_browse_modules,
            font=("Courier New", 11, "bold"),
        )
        browse_btn.grid(row=0, column=1, padx=12, pady=10)

        last_report_btn = NeonButton(
            btn_frame, text="REPORT HISTORY",
            width=280, height=44,
            fg=COLORS["cyan"], border=COLORS["cyan"],
            command=self.on_last_report_click,
            font=("Courier New", 11, "bold"),
        )
        last_report_btn.grid(row=0, column=2, padx=12, pady=10)

        self.root.after(200, self._rain.start)

    # ── REPORT HISTORY TAB (Bug Bounty) ───────────────────────────────────

    def create_last_report_screen(self):
        for w in self.last_report_frame.winfo_children():
            w.destroy()

        container = tk.Frame(self.last_report_frame, bg=COLORS["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        top = tk.Frame(container, bg=COLORS["bg"])
        top.pack(fill=tk.X, pady=(0, 10))

        NeonButton(
            top, text="< BACK TO HOME", width=160, height=32,
            fg=COLORS["fg_dim"], border=COLORS["fg_dim"],
            command=self.on_back_to_home,
            font=("Courier New", 9, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            container,
            text="[ LAST REPORT — BUG BOUNTY ]",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 14, "bold"),
        ).pack(pady=(0, 4))

        tk.Label(
            container,
            text="History of your recon sessions. Use this to draft bug bounty reports.",
            bg=COLORS["bg"], fg=COLORS["fg_dim"],
            font=("Courier New", 10),
        ).pack(pady=(0, 12))

        report = getattr(self, "_last_report", None)
        summary = self.session_log.get_findings_summary()
        has_data = report or summary.get("tools_run")

        if not has_data:
            tk.Label(
                container,
                text="No recon data yet. Run a reconnaissance first.",
                bg=COLORS["bg"], fg=COLORS["yellow"],
                font=("Courier New", 12),
            ).pack(pady=20)
            NeonButton(
                container, text="GO TO RECON", width=200, height=36,
                fg=COLORS["fg"], border=COLORS["fg"],
                command=self.on_recon_click,
                font=("Courier New", 10, "bold"),
            ).pack(pady=10)
            return

        if not report:
            report = self.session_log.build_cumulative_report()
            self._last_report = report

        summary = report.get_findings_summary()
        next_steps = report.get_next_steps()
        target = report.target

        btn_row = tk.Frame(container, bg=COLORS["bg"])
        btn_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(btn_row, text="EXPORT:", bg=COLORS["bg"], fg=COLORS["cyan"],
                 font=("Courier New", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        NeonButton(btn_row, text="COPY FOR BOUNTY", width=180, height=30,
                  fg=COLORS["fg"], border=COLORS["fg"],
                  command=lambda: self._copy_bounty_report(report),
                  font=("Courier New", 9, "bold")).pack(side=tk.LEFT, padx=4)
        NeonButton(btn_row, text="SAVE .MD", width=100, height=30,
                  fg=COLORS["cyan_dim"], border=COLORS["cyan_dim"],
                  command=lambda: self._save_report("md"), font=("Courier New", 9, "bold")).pack(side=tk.LEFT, padx=4)
        NeonButton(btn_row, text="SAVE .HTML", width=100, height=30,
                  fg=COLORS["cyan_dim"], border=COLORS["cyan_dim"],
                  command=lambda: self._save_report("html"), font=("Courier New", 9, "bold")).pack(side=tk.LEFT, padx=4)

        scroller = scrolledtext.ScrolledText(
            container, wrap=tk.WORD, bg=COLORS["bg_input"], fg=COLORS["fg"],
            insertbackground=COLORS["fg"], font=("Courier New", 10),
            relief=tk.FLAT, padx=10, pady=10,
        )
        scroller.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        lines = [
            "=" * 60,
            "RECON REPORT — BUG BOUNTY DRAFT",
            "=" * 60,
            "",
            "TARGET: " + target,
            "SESSION LOG: " + self.session_log.get_log_path(),
            "",
            "--- SUMMARY ---",
            "",
        ]
        ports = summary.get("ports", [])
        if ports:
            lines.append("OPEN PORTS:")
            for p in ports[:15]:
                lines.append(f"  - {p['port']}/{p['proto']} {p.get('service', '')}")
            lines.append("")
        techs = summary.get("technologies", [])
        if techs:
            lines.append("TECHNOLOGIES: " + ", ".join(techs[:12]))
            lines.append("")
        vulns = summary.get("vulnerabilities", [])
        if vulns:
            lines.append(f"VULNERABILITIES / FINDINGS: {len(vulns)} item(s)")
            for v in vulns[:10]:
                lines.append(f"  - {v[:120]}")
            lines.append("")
        dirs = summary.get("directories", [])
        if dirs:
            lines.append(f"DIRECTORIES: {len(dirs)} path(s)")
            for d in dirs[:15]:
                lines.append(f"  - {d}")
            lines.append("")
        nuclei = summary.get("nuclei", [])
        if nuclei:
            crit = [f for f in nuclei if f.get("severity") in ("critical", "high")]
            lines.append(f"NUCLEI: {len(nuclei)} finding(s), {len(crit)} critical/high")
            for f in nuclei[:8]:
                lines.append(f"  [{f.get('severity', '?').upper()}] {f.get('name', f.get('template', '?'))}")
            lines.append("")
        lines.append("--- RECOMMENDED NEXT STEPS ---")
        lines.append("")
        for step in next_steps:
            lines.append(f"* {step['reason']}")
            lines.append(f"  $ {step['command']}")
            lines.append("")
        lines.append("=" * 60)

        body = "\n".join(lines)
        scroller.insert(tk.END, body)
        scroller.config(state=tk.DISABLED)

    def _copy_bounty_report(self, report):
        summary = report.get_findings_summary()
        next_steps = report.get_next_steps()
        target = report.target
        lines = [
            "# Recon Report — Bug Bounty",
            "",
            "## Target",
            target,
            "",
            "## Summary",
            "",
        ]
        ports = summary.get("ports", [])
        if ports:
            lines.append("**Open ports:** " + ", ".join(f"{p['port']}/{p['proto']}" for p in ports[:15]))
        techs = summary.get("technologies", [])
        if techs:
            lines.append("**Technologies:** " + ", ".join(techs[:12]))
        vulns = summary.get("vulnerabilities", [])
        if vulns:
            lines.append(f"**Findings:** {len(vulns)} items from scan.")
        lines.extend(["", "## Recommended next steps", ""])
        for step in next_steps:
            lines.append(f"- {step['reason']}")
            lines.append(f"  ```\n  {step['command']}\n  ```")
        text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("CLIPBOARD > Bug bounty report copied")

    # ── RECON TAB ────────────────────────────────────────────────────────

    def create_recon_input_screen(self):
        for w in self.recon_frame.winfo_children():
            w.destroy()

        container = tk.Frame(self.recon_frame, bg=COLORS["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        top = tk.Frame(container, bg=COLORS["bg"])
        top.pack(fill=tk.X, pady=(0, 10))

        back_btn = NeonButton(
            top, text="< BACK", width=100, height=32,
            fg=COLORS["fg_dim"], border=COLORS["fg_dim"],
            command=self.on_back_to_home,
            font=("Courier New", 9, "bold"),
        )
        back_btn.pack(side=tk.LEFT)

        tk.Label(
            container,
            text="[ RECONNAISSANCE MODULE ]",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 14, "bold"),
        ).pack(pady=(0, 6))

        tk.Label(
            container,
            text="━" * 50,
            bg=COLORS["bg"], fg=COLORS["border_dim"],
            font=("Courier New", 10),
        ).pack(pady=(0, 10))

        input_panel = tk.Frame(container, bg=COLORS["bg_panel"], bd=1, relief="solid",
                               highlightbackground=COLORS["border_dim"], highlightthickness=1)
        input_panel.pack(fill=tk.X, pady=6, ipady=8)

        tk.Label(
            input_panel, text="TARGET >",
            bg=COLORS["bg_panel"], fg=COLORS["cyan"],
            font=("Courier New", 11, "bold"),
        ).pack(side=tk.LEFT, padx=(12, 6))

        self.recon_target_entry = tk.Entry(
            input_panel, width=50,
            bg=COLORS["bg_input"], fg=COLORS["fg"],
            insertbackground=COLORS["fg"],
            font=("Courier New", 12),
            bd=0, highlightthickness=1,
            highlightcolor=COLORS["cyan"],
            highlightbackground=COLORS["border_dim"],
        )
        self.recon_target_entry.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        preset_panel = tk.Frame(container, bg=COLORS["bg"])
        preset_panel.pack(fill=tk.X, pady=8)

        tk.Label(
            preset_panel, text="PRESET:",
            bg=COLORS["bg"], fg=COLORS["fg_dim"],
            font=("Courier New", 10, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.recon_preset_var = tk.StringVar(value="full")
        presets = [
            ("FULL RECON", "full"),
            ("HTB / CTF", "htb"),
            ("WEB FOCUS", "web"),
        ]
        for label, val in presets:
            rb = ttk.Radiobutton(
                preset_panel, text=label,
                variable=self.recon_preset_var, value=val,
                style="Cyber.TRadiobutton",
            )
            rb.pack(side=tk.LEFT, padx=12)

        build_btn = NeonButton(
            container, text=">>> BUILD RECON PLAN <<<",
            width=300, height=42,
            fg=COLORS["fg"], border=COLORS["fg"],
            hover_fg="#ffffff", hover_border=COLORS["cyan"],
            command=self.on_build_recon_plan,
        )
        build_btn.pack(pady=14)

        self.recon_plan_container = tk.Frame(container, bg=COLORS["bg"])
        self.recon_plan_container.pack(fill=tk.BOTH, expand=True, pady=6)

    def create_recon_plan_display(self, phases: List[Dict[str, Any]]):
        for w in self.recon_plan_container.winfo_children():
            w.destroy()

        canvas = tk.Canvas(
            self.recon_plan_container, bg=COLORS["bg"], highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            self.recon_plan_container, orient="vertical",
            command=canvas.yview, bg=COLORS["bg_panel"],
            troughcolor=COLORS["bg"], activebackground=COLORS["cyan"],
        )
        scrollable = tk.Frame(canvas, bg=COLORS["bg"])

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        tk.Label(
            scrollable,
            text="[ RECON PLAN -- EXECUTE OR COPY ]",
            bg=COLORS["bg"], fg=COLORS["magenta"],
            font=("Courier New", 11, "bold"),
        ).pack(anchor="w", pady=(4, 8))

        self._phase_cmd_entries = {}

        for phase in phases:
            phase_frame = tk.Frame(
                scrollable, bg=COLORS["bg_panel"], bd=0,
                highlightbackground=COLORS["border_dim"], highlightthickness=1,
            )
            phase_frame.pack(fill=tk.X, padx=4, pady=6, ipady=6)

            phase_header = tk.Label(
                phase_frame,
                text=f"  PHASE {phase['phase']}  |  {phase['purpose'].upper()}  |  {phase['tool'].upper()}  ",
                bg=COLORS["bg_panel"], fg=COLORS["cyan"],
                font=("Courier New", 10, "bold"),
                anchor="w",
            )
            phase_header.pack(anchor="w", padx=8, pady=(4, 2))

            cmd = resolve_tool_command(phase)
            if not cmd:
                cmd = phase.get("command", "(tool not found)")
                avail = False
                cmd_color = COLORS["red"]
            else:
                avail = True
                cmd_color = COLORS["fg"]

            cmd_row = tk.Frame(phase_frame, bg=COLORS["bg_panel"])
            cmd_row.pack(fill=tk.X, padx=16, pady=2)

            tk.Label(
                cmd_row, text="$",
                bg=COLORS["bg_panel"], fg=COLORS["yellow"],
                font=("Courier New", 10, "bold"),
            ).pack(side=tk.LEFT, padx=(0, 4))

            cmd_entry = tk.Entry(
                cmd_row, bg=COLORS["bg_input"], fg=cmd_color,
                insertbackground=COLORS["fg"],
                font=("Courier New", 10),
                bd=0, highlightthickness=1,
                highlightcolor=COLORS["cyan"],
                highlightbackground=COLORS["border_dim"],
                state=tk.NORMAL if avail else tk.DISABLED,
            )
            cmd_entry.insert(0, cmd)
            cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

            phase_idx = phase["phase"]
            self._phase_cmd_entries[phase_idx] = (cmd_entry, phase)

            btn_row = tk.Frame(phase_frame, bg=COLORS["bg_panel"])
            btn_row.pack(anchor="w", padx=12, pady=(4, 4))

            if avail:
                NeonButton(
                    btn_row, text="EXECUTE", width=110, height=30,
                    fg=COLORS["fg"], border=COLORS["fg"],
                    command=lambda p=phase, e=cmd_entry: self.on_execute_phase_edited(p, e),
                    font=("Courier New", 9, "bold"),
                ).pack(side=tk.LEFT, padx=4)

            NeonButton(
                btn_row, text="COPY CMD", width=110, height=30,
                fg=COLORS["cyan_dim"], border=COLORS["cyan_dim"],
                command=lambda e=cmd_entry: self.copy_to_clipboard(e.get()),
                font=("Courier New", 9, "bold"),
            ).pack(side=tk.LEFT, padx=4)

        run_all = NeonButton(
            scrollable, text=">>> RUN ALL PHASES (SEQUENTIAL) <<<",
            width=400, height=42,
            fg=COLORS["magenta"], border=COLORS["magenta"],
            command=self.on_run_all_phases,
        )
        run_all.pack(pady=14)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ── MODULES TAB ──────────────────────────────────────────────────────

    def create_modules_tab(self):
        container = tk.Frame(self.modules_frame, bg=COLORS["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        tk.Label(
            container,
            text="[ ARSENAL -- SELECT MODULE ]",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 13, "bold"),
        ).pack(pady=(6, 4))

        tk.Label(
            container,
            text="━" * 50,
            bg=COLORS["bg"], fg=COLORS["border_dim"],
            font=("Courier New", 10),
        ).pack(pady=(0, 8))

        target_panel = tk.Frame(container, bg=COLORS["bg_panel"], bd=0,
                                highlightbackground=COLORS["border_dim"], highlightthickness=1)
        target_panel.pack(fill=tk.X, pady=(0, 12), ipady=6)

        tk.Label(
            target_panel, text="TARGET >",
            bg=COLORS["bg_panel"], fg=COLORS["cyan"],
            font=("Courier New", 11, "bold"),
        ).pack(side=tk.LEFT, padx=(12, 6))

        self.target_entry = tk.Entry(
            target_panel, width=50,
            bg=COLORS["bg_input"], fg=COLORS["fg"],
            insertbackground=COLORS["fg"],
            font=("Courier New", 12),
            bd=0, highlightthickness=1,
            highlightcolor=COLORS["cyan"],
            highlightbackground=COLORS["border_dim"],
        )
        self.target_entry.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        grid_frame = tk.Frame(container, bg=COLORS["bg"])
        grid_frame.pack(fill=tk.BOTH, expand=True)

        modules = [
            ("RECON", "recon", COLORS["fg"]),
            ("SQL INJECTION", "sql", COLORS["cyan"]),
            ("XSS", "xss", COLORS["cyan"]),
            ("OPEN REDIRECT", "open_redirect", COLORS["yellow"]),
            ("CLICKJACKING", "clickjacking", COLORS["yellow"]),
            ("CSRF", "csrf", COLORS["yellow"]),
            ("ACCESS CTRL", "access_control", COLORS["magenta"]),
            ("AUTH", "auth", COLORS["magenta"]),
            ("FILE UPLOAD", "file_upload", COLORS["magenta"]),
            ("BIZ LOGIC", "business_logic", COLORS["orange"]),
            ("SSRF", "ssrf", COLORS["orange"]),
            ("DESEIRAL", "deserialization", COLORS["orange"]),
            ("XXE", "xxe", COLORS["red"]),
            ("SSTI", "template_injection", COLORS["red"]),
            ("RCE", "rce", COLORS["red"]),
            ("API SEC", "api", COLORS["cyan"]),
            ("INFO DISC", "information_disclosure", COLORS["cyan"]),
            ("SESSION", "session", COLORS["fg"]),
            ("SMUGGLING", "request_smuggling", COLORS["fg"]),
            ("WEB CACHE", "cache", COLORS["fg"]),
            ("FUZZING", "fuzzing", COLORS["yellow"]),
            ("BRUTE FORCE", "brute_force", COLORS["red"]),
        ]

        row, col = 0, 0
        for name, mid, color in modules:
            btn = NeonButton(
                grid_frame, text=name, width=190, height=36,
                fg=color, border=color,
                command=lambda m=mid: self.run_module(m),
                font=("Courier New", 9, "bold"),
            )
            btn.grid(row=row, column=col, padx=6, pady=5)
            col += 1
            if col >= 4:
                col = 0
                row += 1

    # ── TERMINAL TAB ─────────────────────────────────────────────────────

    def create_terminal_tab(self):
        container = tk.Frame(self.terminal_frame, bg=COLORS["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        term_header = tk.Frame(container, bg=COLORS["bg_panel"],
                               highlightbackground=COLORS["border_dim"], highlightthickness=1)
        term_header.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            term_header, text="  TERMINAL SESSIONS  //  LIVE FEED  ",
            bg=COLORS["bg_panel"], fg=COLORS["cyan"],
            font=("Courier New", 10, "bold"),
        ).pack(side=tk.LEFT, padx=6, pady=4)

        NeonButton(
            term_header, text="CLOSE TAB", width=100, height=28,
            fg=COLORS["red"], border=COLORS["red"],
            command=self._close_current_session,
            font=("Courier New", 9, "bold"),
        ).pack(side=tk.RIGHT, padx=6, pady=4)

        NeonButton(
            term_header, text="CLEAR", width=80, height=28,
            fg=COLORS["orange"], border=COLORS["orange"],
            command=self.clear_terminal,
            font=("Courier New", 9, "bold"),
        ).pack(side=tk.RIGHT, padx=2, pady=4)

        self.term_notebook = ttk.Notebook(container, style="Cyber.TNotebook")
        self.term_notebook.pack(fill=tk.BOTH, expand=True)

        self._create_terminal_session("Main")

        style = ttk.Style()
        style.configure(
            "Neon.Horizontal.TProgressbar",
            troughcolor=COLORS["bg"],
            background=COLORS["fg"],
            thickness=14,
        )

    def _create_terminal_session(self, label: str = "Session") -> str:
        """Create a new terminal session tab. Returns the session ID."""
        self._session_counter += 1
        sid = f"sess_{self._session_counter}"

        frame = tk.Frame(self.term_notebook, bg=COLORS["bg"])

        term_widget = scrolledtext.ScrolledText(
            frame,
            bg="#050505", fg=COLORS["fg"],
            font=("Courier New", 11),
            insertbackground=COLORS["fg"],
            selectbackground=COLORS["glow"],
            selectforeground=COLORS["fg_bright"],
            bd=0, highlightthickness=1,
            highlightbackground=COLORS["border_dim"],
            highlightcolor=COLORS["cyan"],
            wrap=tk.WORD,
        )
        term_widget.pack(fill=tk.BOTH, expand=True)

        term_widget.tag_configure("phase", foreground=COLORS["cyan"], font=("Courier New", 11, "bold"))
        term_widget.tag_configure("cmd", foreground=COLORS["yellow"])
        term_widget.tag_configure("error", foreground=COLORS["red"])
        term_widget.tag_configure("success", foreground=COLORS["fg_bright"])

        progress_frame = tk.Frame(frame, bg=COLORS["bg_panel"],
                                  highlightbackground=COLORS["border_dim"], highlightthickness=1)
        progress_frame.pack(fill=tk.X, pady=(4, 0))

        progress_label = tk.Label(
            progress_frame, text="IDLE",
            bg=COLORS["bg_panel"], fg=COLORS["cyan"],
            font=("Courier New", 10, "bold"),
        )
        progress_label.pack(side=tk.LEFT, padx=8, pady=4)

        progress_var = tk.DoubleVar(value=0.0)
        progress_bar = ttk.Progressbar(
            progress_frame, variable=progress_var,
            maximum=100, length=300,
            style="Neon.Horizontal.TProgressbar",
        )
        progress_bar.pack(side=tk.RIGHT, padx=8, pady=4, fill=tk.X, expand=True)

        report_frame = tk.Frame(frame, bg=COLORS["bg"])
        report_frame.pack(fill=tk.X, pady=(4, 0))
        report_frame.pack_forget()

        short_label = label[:20]
        self.term_notebook.add(frame, text=f"  {short_label}  ")
        self.term_notebook.select(frame)

        self._terminal_sessions[sid] = {
            "frame": frame,
            "terminal": term_widget,
            "progress_label": progress_label,
            "progress_var": progress_var,
            "progress_bar": progress_bar,
            "report_frame": report_frame,
            "label": label,
        }
        self._active_session = sid

        # Keep backward compatibility: point self.terminal etc to the new session
        self.terminal = term_widget
        self.progress_label = progress_label
        self.progress_var = progress_var
        self.progress_bar = progress_bar
        self.report_frame = report_frame

        return sid

    def _get_session(self, sid: str) -> Optional[Dict]:
        return self._terminal_sessions.get(sid)

    def _activate_session(self, sid: str):
        """Switch backward-compat attributes to a specific session."""
        sess = self._get_session(sid)
        if not sess:
            return
        self._active_session = sid
        self.terminal = sess["terminal"]
        self.progress_label = sess["progress_label"]
        self.progress_var = sess["progress_var"]
        self.progress_bar = sess["progress_bar"]
        self.report_frame = sess["report_frame"]
        self.term_notebook.select(sess["frame"])

    def _close_current_session(self):
        """Close the currently visible terminal session tab."""
        if len(self._terminal_sessions) <= 1:
            self.clear_terminal()
            return
        try:
            current = self.term_notebook.select()
        except Exception:
            return
        sid_to_remove = None
        for sid, sess in self._terminal_sessions.items():
            if str(sess["frame"]) == str(current):
                sid_to_remove = sid
                break
        if sid_to_remove:
            self.term_notebook.forget(self._terminal_sessions[sid_to_remove]["frame"])
            del self._terminal_sessions[sid_to_remove]
            remaining = list(self._terminal_sessions.keys())
            if remaining:
                self._activate_session(remaining[-1])

    def _open_new_terminal(self, label: str) -> str:
        """Open a new terminal session and switch to it. Returns session ID."""
        self.notebook.select(self.terminal_frame)
        sid = self._create_terminal_session(label)
        return sid

    # ── ABOUT TAB ────────────────────────────────────────────────────────

    def create_settings_tab(self):
        container = tk.Frame(self.settings_frame, bg=COLORS["bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            container,
            text="[ ABOUT ]",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 13, "bold"),
        ).pack(pady=(10, 4))

        tk.Label(
            container,
            text="━" * 44,
            bg=COLORS["bg"], fg=COLORS["border_dim"],
            font=("Courier New", 10),
        ).pack(pady=(0, 16))

        info_items = [
            ("VERSION", "1.0.0"),
            ("AUTHOR", "HCKNKnuckle"),
            ("AUTHOR", "HCKNKnuckle"),
            ("THEME", "Hackers x Swordfish x Matrix"),
            ("ENGINE", "Python / Tkinter / Go"),
            ("DESIGNED FOR", "Kali Linux / WSL / Docker"),
        ]
        for label, value in info_items:
            row = tk.Frame(container, bg=COLORS["bg"])
            row.pack(fill=tk.X, pady=4)
            tk.Label(
                row, text=f"  {label}:", width=18, anchor="e",
                bg=COLORS["bg"], fg=COLORS["cyan_dim"],
                font=("Courier New", 10, "bold"),
            ).pack(side=tk.LEFT)
            tk.Label(
                row, text=f"  {value}", anchor="w",
                bg=COLORS["bg"], fg=COLORS["fg"],
                font=("Courier New", 10),
            ).pack(side=tk.LEFT, padx=(6, 0))

        tk.Label(
            container,
            text="\n\"We are samurai, the keyboard cowboys...\"\n  -- The Plague, Hackers (1995)",
            bg=COLORS["bg"], fg=COLORS["fg_dim"],
            font=("Courier New", 10, "italic"),
            justify="center",
        ).pack(pady=30)

    # ── Event Handlers ───────────────────────────────────────────────────

    def on_recon_click(self, _module_id=None):
        self.notebook.select(self.recon_frame)
        self.create_recon_input_screen()
        self.status_var.set("RECON > Enter target for reconnaissance")

    def on_module_click(self, module_id: str):
        self.notebook.select(self.modules_frame)
        self.target_entry.delete(0, tk.END)
        self.status_var.set(f"MODULE > Enter target, then run {module_id.upper()}")

    def on_browse_modules(self):
        self.notebook.select(self.modules_frame)
        self.status_var.set("ARSENAL > Select a module")

    def on_last_report_click(self):
        self.notebook.select(self.last_report_frame)
        self.create_last_report_screen()
        self.status_var.set("REPORT HISTORY > Bug bounty report from your last recon")

    def on_back_to_home(self):
        self.notebook.select(self.home_frame)
        self.create_welcome_screen()
        self.status_var.set("SYSTEM ONLINE -- READY")

    def validate_target(self, target: str) -> bool:
        target = target.strip()
        if not target:
            return False
        if target.startswith(("http://", "https://")):
            return validate_url(target)
        if is_ip_address(target):
            return True
        if "." in target:
            return True
        return False

    def on_build_recon_plan(self):
        target = self.recon_target_entry.get().strip()
        if not target:
            messagebox.showwarning("NO TARGET", "Enter an IP address or domain/URL")
            return
        if not self.validate_target(target):
            messagebox.showwarning("INVALID TARGET", "Enter a valid IP or URL")
            return

        preset = self.recon_preset_var.get()
        self.status_var.set("RECON > Running pre-flight checks...")

        from core.host_check import run_preflight_check, add_to_hosts_file

        preflight = run_preflight_check(target, preset)

        if preflight["needs_hosts_update"]:
            redirect_host = preflight.get("redirect_hostname", "")
            warning_text = "\n\n".join(preflight["warnings"]) if preflight["warnings"] else preflight["message"]

            if redirect_host:
                answer = messagebox.askyesnocancel(
                    "HOSTS FILE UPDATE REQUIRED",
                    f"{warning_text}\n\n"
                    f"Add \"{target}  {redirect_host}\" to /etc/hosts now?\n\n"
                    f"YES = Add and continue (requires sudo)\n"
                    f"NO = Skip and build plan anyway\n"
                    f"CANCEL = Abort"
                )
                if answer is None:
                    self.status_var.set("RECON > Aborted")
                    return
                if answer:
                    ok, msg = add_to_hosts_file(target, [redirect_host])
                    if ok:
                        self.status_var.set(f"RECON > {msg}")
                        self.log_terminal(f"[+] {msg}\n", "success")
                        target = redirect_host
                        self.recon_target_entry.delete(0, tk.END)
                        self.recon_target_entry.insert(0, target)
                    else:
                        messagebox.showwarning("HOSTS UPDATE FAILED", msg)
                        self.log_terminal(f"[!] {msg}\n", "error")
            else:
                messagebox.showwarning("HOST CHECK WARNING", warning_text)

        elif preflight["redirect_hostname"]:
            redir = preflight["redirect_hostname"]
            self.log_terminal(f"[*] Redirect detected: {target} -> {redir} (already in /etc/hosts)\n", "phase")

        if preflight.get("warnings"):
            for w in preflight["warnings"]:
                self.log_terminal(f"[!] {w}\n", "error")

        self.status_var.set("RECON > Building plan...")

        try:
            phases = build_recon_plan(target, self.config, preset=preset)
            self.recon_phases = phases
            self._last_recon_target = target
            self.session_log.set_target(target)
            self.create_recon_plan_display(phases)
            self.status_var.set(f"RECON > Plan built: {len(phases)} phases for {target}  |  Log: {self.session_log.get_log_path()}")
        except Exception as e:
            self.logger.error(f"Error building plan: {e}")
            messagebox.showerror("ERROR", str(e))
            self.status_var.set("RECON > Error building plan")

    def on_execute_phase(self, phase: dict):
        cmd = resolve_tool_command(phase)
        if not cmd:
            messagebox.showwarning("TOOL NOT FOUND", f"{phase['tool']} is not on PATH")
            return

        sid = self._open_new_terminal(f"P{phase['phase']} {phase['tool']}")
        sess = self._get_session(sid)
        term = sess["terminal"]
        tool_name = phase.get("tool", "unknown")
        output_buf: list = []

        self._log_to(term, f"\n[*] === Phase {phase['phase']}: {phase['purpose']} ===\n", "phase")
        self._log_to(term, f"[*] $ {cmd}\n\n", "cmd")
        self.status_var.set(f"EXEC > Running {tool_name}...")
        self.session_log.set_target(getattr(self, "_last_recon_target", ""))

        def on_out(msg, _buf=output_buf):
            _buf.append(msg)
            self.root.after(0, lambda: self._log_to(term, msg))

        def on_done(code, _buf=output_buf):
            self.session_log.record_output(tool_name, cmd, "".join(_buf), code, source="phase")
            self.root.after(0, lambda: (
                self.status_var.set(f"EXEC > Phase {phase['phase']} completed (exit {code})"),
                self._refresh_session_panel(),
            ))

        run_tool(cmd, on_out, on_complete=on_done)

    def on_execute_phase_edited(self, phase: dict, cmd_entry):
        """Execute a phase using the user-edited command from the entry widget."""
        cmd = cmd_entry.get().strip()
        if not cmd:
            messagebox.showwarning("EMPTY COMMAND", "Enter a command to execute")
            return

        phase["command"] = cmd
        tool_name = phase.get("tool", "unknown")

        sid = self._open_new_terminal(f"P{phase['phase']} {tool_name}")
        sess = self._get_session(sid)
        term = sess["terminal"]
        output_buf: list = []

        self._log_to(term, f"\n[*] === Phase {phase['phase']}: {phase['purpose']} ===\n", "phase")
        self._log_to(term, f"[*] $ {cmd}\n\n", "cmd")
        self.status_var.set(f"EXEC > Running {tool_name}...")
        self.session_log.set_target(getattr(self, "_last_recon_target", ""))

        def on_out(msg, _buf=output_buf):
            _buf.append(msg)
            self.root.after(0, lambda: self._log_to(term, msg))

        def on_done(code, _buf=output_buf):
            self.session_log.record_output(tool_name, cmd, "".join(_buf), code, source="phase")
            self.root.after(0, lambda: (
                self.status_var.set(f"EXEC > Phase {phase['phase']} completed (exit {code})"),
                self._refresh_session_panel(),
            ))

        run_tool(cmd, on_out, on_complete=on_done)

    def on_run_all_phases(self):
        if not self.recon_phases:
            messagebox.showwarning("NO PLAN", "Build a recon plan first.")
            return

        if hasattr(self, "_phase_cmd_entries"):
            for phase_num, (entry, phase) in self._phase_cmd_entries.items():
                edited = entry.get().strip()
                if edited:
                    phase["command"] = edited

        target = getattr(self, "_last_recon_target", self.recon_target_entry.get().strip())
        sid = self._open_new_terminal(f"Recon {target[:15]}")
        sess = self._get_session(sid)
        term = sess["terminal"]
        p_label = sess["progress_label"]
        p_var = sess["progress_var"]
        r_frame = sess["report_frame"]

        self._log_to(term, "\n[*] === RUNNING ALL PHASES (SEQUENTIAL -- CONFIRM AFTER EACH) ===\n\n", "phase")
        self.status_var.set("EXEC > Running all phases...")
        p_var.set(0)
        p_label.config(text="STARTING...")
        r_frame.pack_forget()
        self.session_log.set_target(target)

        from core.report import ReconReport
        report = ReconReport(target)

        def on_out(msg):
            self.root.after(0, lambda: self._log_to(term, msg))

        def on_phase_done(phase, code):
            self.root.after(
                0,
                lambda: self.status_var.set(
                    f"EXEC > Phase {phase['phase']} done. Waiting for confirmation..."
                ),
            )

        def on_progress(current, total, phase):
            pct = (current / total) * 100 if total else 0
            lbl = f"PHASE {current}/{total}: {phase.get('tool', '?')} -- {phase.get('purpose', '')}"
            self.root.after(0, lambda: (
                p_var.set(pct),
                p_label.config(text=lbl),
            ))

        def on_phase_confirm(phase, exit_code, output, collected_so_far):
            """Blocks the runner thread until user confirms in the GUI."""
            tool_name = phase.get("tool", "unknown")
            summary_lines = SessionLog.parse_phase_summary(tool_name, output)

            confirm_event = threading.Event()
            user_choice = [True]  # True = continue, False = stop

            def _show_confirm():
                self._log_to(term, "\n" + "=" * 60 + "\n", "phase")
                self._log_to(term, f"  PHASE {phase['phase']} COMPLETE -- {tool_name.upper()} FINDINGS:\n", "phase")
                self._log_to(term, "=" * 60 + "\n", "phase")
                for line in summary_lines:
                    self._log_to(term, f"  {line}\n", "success")
                self._log_to(term, "=" * 60 + "\n\n", "phase")
                self.status_var.set(f"WAITING > Review Phase {phase['phase']} findings, then confirm.")

                confirm_frame = tk.Frame(term.master, bg=COLORS["bg_panel"],
                                         highlightbackground=COLORS["yellow"],
                                         highlightthickness=2)
                confirm_frame.pack(fill=tk.X, pady=4, padx=4)

                tk.Label(
                    confirm_frame,
                    text=f"PHASE {phase['phase']}: {tool_name.upper()} -- {phase.get('purpose', '')}",
                    bg=COLORS["bg_panel"], fg=COLORS["yellow"],
                    font=("Courier New", 11, "bold"),
                ).pack(anchor="w", padx=8, pady=(6, 2))

                for line in summary_lines:
                    tk.Label(
                        confirm_frame, text=f"  {line}",
                        bg=COLORS["bg_panel"], fg=COLORS["fg"],
                        font=("Courier New", 9), anchor="w",
                    ).pack(anchor="w", padx=12)

                btn_row = tk.Frame(confirm_frame, bg=COLORS["bg_panel"])
                btn_row.pack(fill=tk.X, padx=8, pady=(8, 6))

                def _continue():
                    user_choice[0] = True
                    confirm_frame.destroy()
                    confirm_event.set()

                def _stop():
                    user_choice[0] = False
                    confirm_frame.destroy()
                    confirm_event.set()

                NeonButton(
                    btn_row, text="CONTINUE TO NEXT PHASE >>>", width=260, height=32,
                    fg=COLORS["fg"], border=COLORS["fg"],
                    command=_continue,
                    font=("Courier New", 10, "bold"),
                ).pack(side=tk.LEFT, padx=(0, 8))

                NeonButton(
                    btn_row, text="STOP HERE", width=120, height=32,
                    fg=COLORS["red"], border=COLORS["red"],
                    command=_stop,
                    font=("Courier New", 10, "bold"),
                ).pack(side=tk.LEFT)

                term.master.update_idletasks()
                term.see(tk.END)

            self.root.after(0, _show_confirm)
            confirm_event.wait()
            return user_choice[0]

        def on_all_done(collected):
            for tool, output in collected.items():
                report.add_phase_output(tool, output)
                self.session_log.record_output(tool, "", output, 0, source="recon")
            self._last_report = report

            from core.host_check import extract_hostnames_from_output, hostname_in_hosts, read_hosts_file
            all_output = "\n".join(collected.values())
            new_hosts = extract_hostnames_from_output(all_output)
            hosts_map = read_hosts_file()
            unmapped = [h for h in new_hosts if not hostname_in_hosts(h, hosts_map)]
            if unmapped:
                self.root.after(0, lambda: self._prompt_new_hostnames(target, unmapped))

            self._activate_session(sid)
            self.root.after(0, lambda: self._show_post_recon_panel(report))
            self.root.after(0, lambda: (
                p_var.set(100),
                p_label.config(text="ALL PHASES COMPLETE"),
                self.status_var.set("EXEC > Complete. Review findings and next steps below."),
                self._log_to(term, "\n[+] === ALL PHASES COMPLETE ===\n", "success"),
            ))

        run_tools_sequential(
            self.recon_phases,
            on_out,
            on_phase_complete=on_phase_done,
            on_progress=on_progress,
            on_all_complete=on_all_done,
            on_phase_confirm=on_phase_confirm,
        )

    def _show_post_recon_panel(self, report):
        """Show findings summary, report buttons, and executable next-step commands."""
        for w in self.report_frame.winfo_children():
            w.destroy()
        self.report_frame.pack(fill=tk.X, pady=(4, 0))

        summary = report.get_findings_summary()
        next_steps = report.get_next_steps()

        session_summary = self.session_log.get_findings_summary()
        tools_run = session_summary.get("tools_run", [])
        total_runs = session_summary.get("total_entries", 0)

        if tools_run:
            session_bar = tk.Frame(self.report_frame, bg=COLORS["bg_panel"],
                                   highlightbackground=COLORS["border_dim"], highlightthickness=1)
            session_bar.pack(fill=tk.X, pady=(0, 4))
            tk.Label(
                session_bar,
                text=f"[ SESSION: {total_runs} run(s) | Tools: {', '.join(tools_run)} | Log: {self.session_log.get_log_path()} ]",
                bg=COLORS["bg_panel"], fg=COLORS["cyan_dim"],
                font=("Courier New", 9), anchor="w",
            ).pack(anchor="w", padx=8, pady=3)

        # -- Findings summary --
        summary_lines = []
        ports = summary.get("ports", [])
        if ports:
            summary_lines.append(f"OPEN PORTS: {', '.join(str(p['port']) + '/' + p['proto'] + ' ' + p['service'] for p in ports[:10])}")
        techs = summary.get("technologies", [])
        if techs:
            summary_lines.append(f"TECH STACK: {', '.join(techs[:8])}")
        vulns = summary.get("vulnerabilities", [])
        if vulns:
            summary_lines.append(f"VULNS FOUND: {len(vulns)} item(s)")
        dirs = summary.get("directories", [])
        if dirs:
            summary_lines.append(f"DIRECTORIES: {len(dirs)} path(s) discovered")
        nuclei = summary.get("nuclei", [])
        if nuclei:
            crit = [f for f in nuclei if f.get("severity") in ("critical", "high")]
            summary_lines.append(f"NUCLEI: {len(nuclei)} finding(s), {len(crit)} critical/high")

        if summary_lines:
            findings_frame = tk.Frame(self.report_frame, bg=COLORS["bg_panel"],
                                      highlightbackground=COLORS["border_dim"], highlightthickness=1)
            findings_frame.pack(fill=tk.X, pady=(0, 4))
            tk.Label(
                findings_frame, text="[ FINDINGS SUMMARY ]",
                bg=COLORS["bg_panel"], fg=COLORS["magenta"],
                font=("Courier New", 10, "bold"),
            ).pack(anchor="w", padx=8, pady=(4, 2))
            for line in summary_lines:
                tk.Label(
                    findings_frame, text=f"  {line}",
                    bg=COLORS["bg_panel"], fg=COLORS["fg"],
                    font=("Courier New", 9), anchor="w",
                ).pack(anchor="w", padx=12)

        # -- Report buttons --
        report_row = tk.Frame(self.report_frame, bg=COLORS["bg"])
        report_row.pack(fill=tk.X, pady=4)

        tk.Label(
            report_row, text="SAVE REPORT:",
            bg=COLORS["bg"], fg=COLORS["cyan"],
            font=("Courier New", 10, "bold"),
        ).pack(side=tk.LEFT, padx=6)

        NeonButton(
            report_row, text="MARKDOWN (.md)", width=160, height=30,
            fg=COLORS["fg"], border=COLORS["fg"],
            command=lambda: self._save_report("md"),
            font=("Courier New", 9, "bold"),
        ).pack(side=tk.LEFT, padx=4)

        NeonButton(
            report_row, text="HTML (.html)", width=140, height=30,
            fg=COLORS["cyan"], border=COLORS["cyan"],
            command=lambda: self._save_report("html"),
            font=("Courier New", 9, "bold"),
        ).pack(side=tk.LEFT, padx=4)

        # -- Next steps with editable commands --
        if next_steps:
            ns_frame = tk.Frame(self.report_frame, bg=COLORS["bg_panel"],
                                highlightbackground=COLORS["border_dim"], highlightthickness=1)
            ns_frame.pack(fill=tk.X, pady=(4, 0))

            tk.Label(
                ns_frame, text="[ RECOMMENDED NEXT STEPS -- EDIT AND RUN ]",
                bg=COLORS["bg_panel"], fg=COLORS["magenta"],
                font=("Courier New", 10, "bold"),
            ).pack(anchor="w", padx=8, pady=(4, 2))

            for step in next_steps:
                step_frame = tk.Frame(ns_frame, bg=COLORS["bg_panel"])
                step_frame.pack(fill=tk.X, padx=8, pady=3)

                tk.Label(
                    step_frame, text=step["reason"],
                    bg=COLORS["bg_panel"], fg=COLORS["fg_dim"],
                    font=("Courier New", 9), anchor="w",
                ).pack(anchor="w")

                cmd_row = tk.Frame(step_frame, bg=COLORS["bg_panel"])
                cmd_row.pack(fill=tk.X, pady=(1, 0))

                tk.Label(
                    cmd_row, text="$",
                    bg=COLORS["bg_panel"], fg=COLORS["yellow"],
                    font=("Courier New", 10, "bold"),
                ).pack(side=tk.LEFT, padx=(0, 4))

                cmd_entry = tk.Entry(
                    cmd_row, bg=COLORS["bg_input"], fg=COLORS["fg"],
                    insertbackground=COLORS["fg"],
                    font=("Courier New", 10),
                    bd=0, highlightthickness=1,
                    highlightcolor=COLORS["cyan"],
                    highlightbackground=COLORS["border_dim"],
                )
                cmd_entry.insert(0, step["command"])
                cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

                NeonButton(
                    cmd_row, text="RUN", width=70, height=26,
                    fg=COLORS["fg"], border=COLORS["fg"],
                    command=lambda e=cmd_entry: self._run_next_step_cmd(e.get()),
                    font=("Courier New", 9, "bold"),
                ).pack(side=tk.LEFT, padx=2)

                NeonButton(
                    cmd_row, text="COPY", width=70, height=26,
                    fg=COLORS["cyan_dim"], border=COLORS["cyan_dim"],
                    command=lambda e=cmd_entry: self.copy_to_clipboard(e.get()),
                    font=("Courier New", 9, "bold"),
                ).pack(side=tk.LEFT, padx=2)

    def _refresh_session_panel(self):
        """Rebuild findings + next-steps from the cumulative session log."""
        summary = self.session_log.get_findings_summary()
        if not summary.get("tools_run"):
            return
        report = self.session_log.build_cumulative_report()
        self._last_report = report
        if self._active_session:
            sess = self._get_session(self._active_session)
            if sess:
                self.report_frame = sess["report_frame"]
        self._show_post_recon_panel(report)

    def _run_next_step_cmd(self, cmd: str):
        """Execute a next-step command from the post-recon panel."""
        cmd = cmd.strip()
        if not cmd:
            return

        tool_name = cmd.split()[0] if cmd else "cmd"
        sid = self._open_new_terminal(tool_name)
        sess = self._get_session(sid)
        term = sess["terminal"]
        output_buf: list = []

        self._log_to(term, f"\n[*] === Next-step command ===\n", "phase")
        self._log_to(term, f"[*] $ {cmd}\n\n", "cmd")
        self.status_var.set(f"EXEC > Running: {cmd[:50]}...")

        def on_out(msg, _buf=output_buf):
            _buf.append(msg)
            self.root.after(0, lambda: self._log_to(term, msg))

        def on_done(code, _buf=output_buf):
            self.session_log.record_output(tool_name, cmd, "".join(_buf), code, source="next_step")
            self.root.after(0, lambda: (
                self.status_var.set(f"EXEC > Command completed (exit {code})"),
                self._refresh_session_panel(),
            ))

        run_tool(cmd, on_out, on_complete=on_done)

    def _prompt_new_hostnames(self, target_ip: str, hostnames: list):
        """Prompt user to add newly discovered hostnames to /etc/hosts."""
        from core.host_check import add_to_hosts_file
        from utils.helpers import is_ip_address

        hosts_str = ", ".join(hostnames)
        self.log_terminal(f"\n[*] Discovered hostnames not in /etc/hosts: {hosts_str}\n", "phase")

        ip = target_ip if is_ip_address(target_ip) else ""
        if not ip:
            self.log_terminal(
                f"[!] Add manually: echo \"<IP>    {' '.join(hostnames)}\" | sudo tee -a /etc/hosts\n",
                "error",
            )
            return

        answer = messagebox.askyesno(
            "NEW HOSTNAMES DISCOVERED",
            f"Recon output contains hostnames not in /etc/hosts:\n\n"
            f"{hosts_str}\n\n"
            f"Add \"{ip}    {' '.join(hostnames)}\" to /etc/hosts?\n"
            f"(Requires sudo)"
        )
        if answer:
            ok, msg = add_to_hosts_file(ip, hostnames)
            if ok:
                self.log_terminal(f"[+] {msg}\n", "success")
            else:
                self.log_terminal(f"[!] {msg}\n", "error")
                messagebox.showwarning("HOSTS UPDATE FAILED", msg)
        else:
            self.log_terminal(
                f"[*] Skipped. Manual command: echo \"{ip}    {' '.join(hostnames)}\" | sudo tee -a /etc/hosts\n",
                "cmd",
            )

    def _save_report(self, fmt: str):
        report = getattr(self, "_last_report", None)
        if not report:
            messagebox.showwarning("NO DATA", "No scan data to generate a report from.")
            return
        try:
            path = report.save(fmt=fmt)
            self.log_terminal(f"\n[+] Report saved to: {path}\n", "success")
            self.status_var.set(f"REPORT > Saved to {path}")
            messagebox.showinfo("REPORT SAVED", f"Report saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("ERROR", f"Failed to save report: {e}")

    def copy_to_clipboard(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("CLIPBOARD > Command copied")

    def run_module(self, module_id: str):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("NO TARGET", "Enter a target URL or IP address")
            return

        if module_id == "recon":
            self.on_recon_click()
            self.recon_target_entry.delete(0, tk.END)
            self.recon_target_entry.insert(0, target)
            return

        sid = self._open_new_terminal(f"{module_id.upper()}")
        sess = self._get_session(sid)
        term = sess["terminal"]

        self.status_var.set(f"MODULE > Running {module_id.upper()} on {target}...")
        self._log_to(term, f"[*] Starting {module_id.upper()} module on {target}\n", "phase")

        thread = threading.Thread(
            target=self._execute_module,
            args=(module_id, target, term),
            daemon=True,
        )
        thread.start()

    def _execute_module(self, module_id: str, target: str, term):
        output_buf = []
        try:
            self.root.after(0, lambda: self._log_to(term, f"[+] Module {module_id.upper()} executing\n", "success"))
            self.root.after(0, lambda: self._log_to(term, f"[*] Target: {target}\n", "cmd"))

            module_class = MODULE_REGISTRY.get(module_id)
            if module_class:
                module = module_class(self.config, self.logger)
                result = module.run(target)
                result_str = result.get("summary", str(result)) if isinstance(result, dict) else str(result) if result else ""
                output_buf.append(result_str)
                self.root.after(0, lambda: self._log_to(term, f"[+] Result: {result}\n", "success"))
            else:
                self.root.after(0, lambda: self._log_to(term, "[!] Module not found in registry\n", "error"))

            self.session_log.set_target(target)
            self.session_log.record_output(module_id, f"module:{module_id}", "\n".join(output_buf), 0, source="module")
            self.root.after(0, lambda: (
                self.status_var.set("MODULE > Execution completed"),
                self._refresh_session_panel(),
            ))
        except Exception as e:
            self.root.after(0, lambda: self._log_to(term, f"[!] Error: {str(e)}\n", "error"))
            self.root.after(0, lambda: self.status_var.set(f"ERROR > {str(e)}"))

    def _log_to(self, term_widget, message: str, tag: str = ""):
        """Write to a specific terminal widget (thread-safe when called via root.after)."""
        try:
            if tag:
                term_widget.insert(tk.END, message, tag)
            else:
                term_widget.insert(tk.END, message)
            term_widget.see(tk.END)
        except tk.TclError:
            pass

    def log_terminal(self, message: str, tag: str = ""):
        """Write to the currently active terminal session."""
        self._log_to(self.terminal, message, tag)

    def clear_terminal(self):
        try:
            current = self.term_notebook.select()
            for sid, sess in self._terminal_sessions.items():
                if str(sess["frame"]) == str(current):
                    sess["terminal"].delete(1.0, tk.END)
                    return
        except Exception:
            pass
        self.terminal.delete(1.0, tk.END)

    def run(self):
        self.root.mainloop()


def run_gui(config, logger):
    app = PlanetHackGUI(config, logger)
    app.run()
