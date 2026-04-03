"""
Human Typer - Realistic Human Typing Simulator
A desktop application that simulates human-like typing behavior.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import random
import math
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
import sys

# Try to import pynput for keyboard simulation
try:
    from pynput.keyboard import Controller, Key
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

# ─────────────────────────────────────────────
#  DATA CLASSES & CONSTANTS
# ─────────────────────────────────────────────

# Common short words that experienced typists type faster
COMMON_WORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "of",
    "and", "or", "but", "for", "so", "as", "be", "do", "go", "he",
    "she", "we", "you", "i", "me", "my", "if", "by", "up", "no",
    "hi", "ok", "yes", "no", "was", "are", "has", "had", "not",
    "can", "will", "did", "got", "get", "let", "put", "run", "set",
}

# Character difficulty multipliers (harder chars take longer)
CHAR_DIFFICULTY = {
    # Easy home row
    'a': 0.85, 's': 0.85, 'd': 0.85, 'f': 0.85,
    'j': 0.85, 'k': 0.85, 'l': 0.85,
    # Medium
    'e': 0.90, 'r': 0.90, 't': 0.90, 'y': 0.90,
    'u': 0.90, 'i': 0.90, 'o': 0.90, 'p': 0.90,
    'g': 0.90, 'h': 0.90, 'n': 0.90,
    # Harder
    'q': 1.15, 'w': 1.05, 'z': 1.25, 'x': 1.20,
    'c': 1.00, 'v': 1.10, 'b': 1.10, 'm': 1.00,
    # Numbers and symbols (much harder)
    '1': 1.4, '2': 1.4, '3': 1.4, '4': 1.4, '5': 1.5,
    '6': 1.5, '7': 1.4, '8': 1.4, '9': 1.4, '0': 1.4,
    '!': 1.6, '@': 1.7, '#': 1.6, '$': 1.6, '%': 1.8,
    '^': 1.8, '&': 1.7, '*': 1.7, '(': 1.6, ')': 1.6,
    '-': 1.3, '_': 1.5, '=': 1.4, '+': 1.5,
    '[': 1.4, ']': 1.4, '{': 1.6, '}': 1.6,
    ';': 1.1, ':': 1.3, "'": 1.2, '"': 1.4,
    ',': 1.1, '.': 1.0, '/': 1.3, '?': 1.4,
    ' ': 0.80,
}

# Typing profiles
PROFILES = {
    "Fast Typist": {
        "base_wpm": 90,
        "variance": 0.08,
        "typo_rate": 0.018,
        "pause_short": (0.05, 0.15),
        "pause_sentence": (0.3, 0.8),
        "burst_chance": 0.25,
        "hesitation_chance": 0.04,
        "description": "Experienced typist, minimal hesitation",
    },
    "Average Typist": {
        "base_wpm": 50,
        "variance": 0.15,
        "typo_rate": 0.04,
        "pause_short": (0.10, 0.30),
        "pause_sentence": (0.6, 1.5),
        "burst_chance": 0.12,
        "hesitation_chance": 0.10,
        "description": "Normal everyday typing speed",
    },
    "Slow Thinker": {
        "base_wpm": 25,
        "variance": 0.25,
        "typo_rate": 0.07,
        "pause_short": (0.20, 0.60),
        "pause_sentence": (1.2, 3.5),
        "burst_chance": 0.05,
        "hesitation_chance": 0.20,
        "description": "Deliberate, thoughtful typing with pauses",
    },
    "Hunt & Peck": {
        "base_wpm": 15,
        "variance": 0.35,
        "typo_rate": 0.10,
        "pause_short": (0.30, 1.0),
        "pause_sentence": (2.0, 5.0),
        "burst_chance": 0.02,
        "hesitation_chance": 0.30,
        "description": "Two-finger typing, very variable speed",
    },
}

# Neighboring keys for realistic typo generation
NEIGHBOR_KEYS = {
    'a': ['q', 'w', 's', 'z'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['s', 'e', 'r', 'f', 'c', 'x'],
    'e': ['w', 'r', 'd', 's'],
    'f': ['d', 'r', 't', 'g', 'v', 'c'],
    'g': ['f', 't', 'y', 'h', 'b', 'v'],
    'h': ['g', 'y', 'u', 'j', 'n', 'b'],
    'i': ['u', 'o', 'k', 'j'],
    'j': ['h', 'u', 'i', 'k', 'm', 'n'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p', ';'],
    'm': ['n', 'j', 'k', ','],
    'n': ['b', 'h', 'j', 'm'],
    'o': ['i', 'p', 'l', 'k'],
    'p': ['o', ';', 'l'],
    'q': ['w', 'a'],
    'r': ['e', 't', 'f', 'd'],
    's': ['a', 'w', 'e', 'd', 'x', 'z'],
    't': ['r', 'y', 'g', 'f'],
    'u': ['y', 'i', 'j', 'h'],
    'v': ['c', 'f', 'g', 'b'],
    'w': ['q', 'e', 's', 'a'],
    'x': ['z', 's', 'd', 'c'],
    'y': ['t', 'u', 'h', 'g'],
    'z': ['a', 's', 'x'],
    ' ': [' '],
}


@dataclass
class TypingStats:
    """Tracks real-time typing statistics."""
    chars_typed: int = 0
    words_typed: int = 0
    typos_made: int = 0
    start_time: float = 0.0
    wpm_history: list = field(default_factory=list)
    last_wpm_sample: float = 0.0

    def current_wpm(self) -> float:
        elapsed = time.time() - self.start_time
        if elapsed < 1.0:
            return 0.0
        return (self.words_typed / elapsed) * 60.0

    def reset(self):
        self.chars_typed = 0
        self.words_typed = 0
        self.typos_made = 0
        self.start_time = time.time()
        self.wpm_history.clear()
        self.last_wpm_sample = time.time()


# ─────────────────────────────────────────────
#  SETTINGS
# ─────────────────────────────────────────────

class Settings:
    """Holds all configurable typing settings."""

    def __init__(self):
        self.wpm: int = 50
        self.profile: str = "Average Typist"
        self.enable_typos: bool = True
        self.typing_style: str = "Natural"  # Natural, Robotic, Burst
        self.countdown_seconds: int = 3

    def get_base_delay(self) -> float:
        """Convert WPM to seconds per character (avg 5 chars per word)."""
        chars_per_minute = self.wpm * 5
        return 60.0 / chars_per_minute

    def get_profile(self) -> dict:
        return PROFILES.get(self.profile, PROFILES["Average Typist"])


# ─────────────────────────────────────────────
#  TYPING ENGINE
# ─────────────────────────────────────────────

class TypingEngine:
    """
    Core engine that simulates realistic human typing.
    Handles timing, typos, pauses, and keyboard output.
    """

    def __init__(self, settings: Settings, stats: TypingStats,
                 on_progress=None, on_char=None, on_done=None):
        self.settings = settings
        self.stats = stats
        self.on_progress = on_progress  # callback(pct: float)
        self.on_char = on_char          # callback(char, wpm)
        self.on_done = on_done          # callback()

        self._paused = threading.Event()
        self._paused.set()  # Not paused initially
        self._stop_flag = threading.Event()

        if KEYBOARD_AVAILABLE:
            self.keyboard = Controller()
        else:
            self.keyboard = None

        # Fatigue model: typing slows slightly over time
        self._fatigue_factor = 1.0
        self._chars_since_break = 0

    # ── Public Controls ──────────────────────

    def pause(self):
        self._paused.clear()

    def resume(self):
        self._paused.set()

    def stop(self):
        self._stop_flag.set()
        self._paused.set()  # Unblock if paused

    def is_running(self) -> bool:
        return not self._stop_flag.is_set()

    # ── Main Typing Loop ─────────────────────

    def type_text(self, text: str):
        """
        Main entry point. Types the given text with human-like behavior.
        Should be called from a background thread.
        """
        self._stop_flag.clear()
        self.stats.reset()
        self._fatigue_factor = 1.0
        self._chars_since_break = 0

        total_chars = len(text)
        i = 0

        while i < len(text) and not self._stop_flag.is_set():
            # Wait if paused
            self._paused.wait()
            if self._stop_flag.is_set():
                break

            char = text[i]

            # ── Decide whether to make a typo ──
            if (self.settings.enable_typos
                    and char.isalpha()
                    and self._should_make_typo(char)):
                i = self._type_with_typo(text, i)
            else:
                self._type_char(char)
                i += 1

            # ── Post-char logic ──
            self._apply_fatigue()
            self._maybe_hesitate(char)

            if char == ' ':
                self.stats.words_typed += 1
                self._maybe_word_pause(text, i)

            if char in '.!?':
                self._sentence_pause()

            # Sample WPM every second
            now = time.time()
            if now - self.stats.last_wpm_sample >= 1.0:
                self.stats.wpm_history.append(
                    round(self.stats.current_wpm(), 1)
                )
                self.stats.last_wpm_sample = now

            # Progress callback
            if self.on_progress:
                self.on_progress(i / total_chars)

        # Final word count
        if text and not text[-1] == ' ':
            self.stats.words_typed += 1

        if self.on_progress:
            self.on_progress(1.0)
        if self.on_done:
            self.on_done()

    # ── Timing Calculations ──────────────────

    def _char_delay(self, char: str) -> float:
        """
        Calculate delay before typing a character.
        Considers WPM setting, character difficulty, fatigue, and variance.
        """
        base = self.settings.get_base_delay()
        profile = self.settings.get_profile()

        # Character difficulty multiplier
        difficulty = CHAR_DIFFICULTY.get(char.lower(), 1.0)

        # Variance: human timing is never perfectly consistent
        variance = profile["variance"]
        jitter = random.gauss(1.0, variance)
        jitter = max(0.3, min(2.5, jitter))  # Clamp extremes

        # Burst typing: occasionally type multiple chars very fast
        if random.random() < profile["burst_chance"]:
            burst_factor = random.uniform(0.4, 0.7)
        else:
            burst_factor = 1.0

        delay = base * difficulty * jitter * burst_factor * self._fatigue_factor
        return max(0.02, delay)

    def _apply_fatigue(self):
        """Gradually slow typing to simulate muscle fatigue."""
        self._chars_since_break += 1
        # Every ~200 chars, add a tiny slowdown
        if self._chars_since_break > 200:
            self._fatigue_factor = min(1.3, self._fatigue_factor + 0.001)
        # Occasional micro-recovery
        if random.random() < 0.005:
            self._fatigue_factor = max(1.0, self._fatigue_factor - 0.05)

    def _should_make_typo(self, char: str) -> bool:
        """Determine if a typo should occur for this character."""
        profile = self.settings.get_profile()
        rate = profile["typo_rate"]
        # More typos when fatigued
        rate *= self._fatigue_factor
        return random.random() < rate

    def _maybe_hesitate(self, char: str):
        """Add random hesitation pauses (thinking moments)."""
        profile = self.settings.get_profile()
        if random.random() < profile["hesitation_chance"]:
            pause = random.uniform(0.15, 0.60)
            self._sleep(pause)

    def _maybe_word_pause(self, text: str, pos: int):
        """Add a natural pause between words."""
        profile = self.settings.get_profile()
        lo, hi = profile["pause_short"]
        # Longer pause before long words
        upcoming = self._next_word(text, pos)
        if len(upcoming) > 8:
            pause = random.uniform(lo * 1.3, hi * 1.5)
        else:
            pause = random.uniform(lo, hi)
        self._sleep(pause)

    def _sentence_pause(self):
        """Longer pause at end of sentences."""
        profile = self.settings.get_profile()
        lo, hi = profile["pause_sentence"]
        pause = random.uniform(lo, hi)
        self._sleep(pause)

    # ── Typing Actions ───────────────────────

    def _type_char(self, char: str):
        """Type a single character with appropriate delay."""
        delay = self._char_delay(char)
        self._sleep(delay)

        if self.keyboard:
            try:
                self.keyboard.type(char)
            except Exception:
                pass  # Silently skip unsupported chars
        else:
            # Simulation mode (no real keyboard output)
            pass

        self.stats.chars_typed += 1
        if self.on_char:
            self.on_char(char, self.stats.current_wpm())

    def _type_with_typo(self, text: str, pos: int) -> int:
        """
        Type a character with a typo, then correct it.
        Returns the new position in the text.
        """
        char = text[pos]
        typo_char = self._get_typo_char(char)

        # Type the wrong character
        self._type_char(typo_char)
        self.stats.typos_made += 1

        # Brief pause before noticing the error (50-300ms)
        notice_delay = random.uniform(0.05, 0.30)

        # Sometimes type 1-2 more chars before noticing
        extra_chars = 0
        if random.random() < 0.35:
            extra_count = random.randint(1, 2)
            for j in range(extra_count):
                if pos + 1 + j < len(text):
                    self._type_char(text[pos + 1 + j])
                    extra_chars += 1

        self._sleep(notice_delay)

        # Backspace to correct
        backspace_count = 1 + extra_chars
        for _ in range(backspace_count):
            self._sleep(random.uniform(0.04, 0.10))
            if self.keyboard:
                try:
                    self.keyboard.press(Key.backspace)
                    self.keyboard.release(Key.backspace)
                except Exception:
                    pass

        # Small pause after correction (reorienting)
        self._sleep(random.uniform(0.08, 0.25))

        # Type the correct character
        self._type_char(char)
        return pos + 1  # Move past the corrected char

    def _get_typo_char(self, char: str) -> str:
        """Return a realistic neighboring-key typo for the given character."""
        lower = char.lower()
        neighbors = NEIGHBOR_KEYS.get(lower, [lower])
        typo = random.choice(neighbors)

        # Preserve capitalization
        if char.isupper():
            return typo.upper()
        return typo

    # ── Helpers ──────────────────────────────

    def _sleep(self, seconds: float):
        """Interruptible sleep that respects pause/stop flags."""
        step = 0.05
        elapsed = 0.0
        while elapsed < seconds:
            if self._stop_flag.is_set():
                return
            self._paused.wait()
            time.sleep(min(step, seconds - elapsed))
            elapsed += step

    @staticmethod
    def _next_word(text: str, pos: int) -> str:
        """Get the next word starting at pos."""
        end = text.find(' ', pos)
        if end == -1:
            return text[pos:]
        return text[pos:end]


# ─────────────────────────────────────────────
#  SPEED CHART (Canvas-based real-time graph)
# ─────────────────────────────────────────────

class SpeedChart(tk.Canvas):
    """
    A canvas widget that plots live WPM over time.
    Shows a smooth line graph with a gradient fill.
    """

    MAX_POINTS = 60  # Show last 60 seconds

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.data: deque = deque(maxlen=self.MAX_POINTS)
        self.configure(bg="#0d1117")
        self.bind("<Configure>", self._on_resize)
        self._draw_empty()

    def add_point(self, wpm: float):
        self.data.append(wpm)
        self._redraw()

    def reset(self):
        self.data.clear()
        self._draw_empty()

    def _on_resize(self, event):
        self._redraw()

    def _draw_empty(self):
        self.delete("all")
        w, h = self.winfo_width() or 400, self.winfo_height() or 120
        self._draw_grid(w, h, max_val=100)
        self.create_text(
            w // 2, h // 2,
            text="Typing speed will appear here",
            fill="#3d4550",
            font=("Courier", 10)
        )

    def _redraw(self):
        if not self.data:
            self._draw_empty()
            return

        self.delete("all")
        w = self.winfo_width() or 400
        h = self.winfo_height() or 120
        pad = 10

        max_val = max(max(self.data) * 1.2, 60)
        self._draw_grid(w, h, max_val)

        points = list(self.data)
        n = len(points)
        if n < 2:
            return

        def to_x(i): return pad + (i / (self.MAX_POINTS - 1)) * (w - 2 * pad)
        def to_y(v): return h - pad - (v / max_val) * (h - 2 * pad)

        # Build polygon for gradient fill
        coords = [to_x(0), h - pad]
        for i, v in enumerate(points):
            coords += [to_x(i), to_y(v)]
        coords += [to_x(n - 1), h - pad]
        self.create_polygon(coords, fill="#1a3a5c", outline="", smooth=True)

        # Draw the line
        line_coords = []
        for i, v in enumerate(points):
            line_coords += [to_x(i), to_y(v)]
        self.create_line(line_coords, fill="#00aaff", width=2,
                         smooth=True, joinstyle="round")

        # Current WPM label
        last = points[-1]
        lx, ly = to_x(n - 1), to_y(last)
        self.create_oval(lx - 4, ly - 4, lx + 4, ly + 4,
                         fill="#00aaff", outline="#ffffff", width=1)
        self.create_text(lx - 5, ly - 14, text=f"{last:.0f}",
                         fill="#00aaff", font=("Courier", 9, "bold"), anchor="e")

    def _draw_grid(self, w, h, max_val):
        pad = 10
        # Horizontal grid lines
        for frac in [0.25, 0.5, 0.75, 1.0]:
            y = h - pad - frac * (h - 2 * pad)
            self.create_line(pad, y, w - pad, y, fill="#1e2530", dash=(4, 6))
            label = f"{frac * max_val:.0f}"
            self.create_text(w - pad + 2, y, text=label,
                             fill="#3d4550", font=("Courier", 8), anchor="w")
        # Axis label
        self.create_text(pad, pad - 2, text="WPM",
                         fill="#3d4550", font=("Courier", 8), anchor="w")


# ─────────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────────

class HumanTyperApp(tk.Tk):
    """
    Main application window.
    Organizes the UI into logical sections and connects everything.
    """

    # ── Colour palette ────────────────────────
    BG        = "#0d1117"
    BG2       = "#161b22"
    BG3       = "#21262d"
    ACCENT    = "#00aaff"
    ACCENT2   = "#00ff9d"
    TEXT      = "#e6edf3"
    TEXT_DIM  = "#7d8590"
    BORDER    = "#30363d"
    DANGER    = "#ff5757"
    WARNING   = "#ffa657"
    SUCCESS   = "#3fb950"

    def __init__(self):
        super().__init__()

        self.settings = Settings()
        self.stats = TypingStats()
        self.engine: Optional[TypingEngine] = None
        self._typing_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._is_paused = False

        self._build_window()
        self._build_ui()
        self._start_stat_refresh()

    # ── Window Setup ─────────────────────────

    def _build_window(self):
        self.title("Human Typer  ·  Realistic Typing Simulator")
        self.geometry("820x760")
        self.minsize(680, 640)
        self.configure(bg=self.BG)
        self.resizable(True, True)

        # Apply ttk theme
        style = ttk.Style(self)
        style.theme_use("clam")
        self._configure_styles(style)

    def _configure_styles(self, style: ttk.Style):
        s = style

        # Scale (slider)
        s.configure("H.Horizontal.TScale",
                     background=self.BG2,
                     troughcolor=self.BG3,
                     sliderlength=18,
                     sliderrelief="flat")

        # Checkbutton
        s.configure("H.TCheckbutton",
                     background=self.BG2,
                     foreground=self.TEXT,
                     font=("Courier", 10))
        s.map("H.TCheckbutton",
              background=[("active", self.BG2)],
              foreground=[("active", self.ACCENT)])

        # Combobox
        s.configure("H.TCombobox",
                     fieldbackground=self.BG3,
                     background=self.BG3,
                     foreground=self.TEXT,
                     arrowcolor=self.ACCENT,
                     bordercolor=self.BORDER,
                     lightcolor=self.BG3,
                     darkcolor=self.BG3,
                     font=("Courier", 10))

        # Progressbar
        s.configure("H.Horizontal.TProgressbar",
                     background=self.ACCENT,
                     troughcolor=self.BG3,
                     bordercolor=self.BG3,
                     lightcolor=self.ACCENT,
                     darkcolor=self.ACCENT)

    # ── UI Construction ───────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=self.BG, pady=0)
        hdr.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(hdr, text="⌨  HUMAN TYPER",
                 bg=self.BG, fg=self.ACCENT,
                 font=("Courier", 18, "bold")).pack(side="left")

        self._status_lbl = tk.Label(hdr, text="● READY",
                                     bg=self.BG, fg=self.SUCCESS,
                                     font=("Courier", 10))
        self._status_lbl.pack(side="right", pady=6)

        self._sep(self)

        # ── Main columns ──
        main = tk.Frame(self, bg=self.BG)
        main.pack(fill="both", expand=True, padx=20)

        left = tk.Frame(main, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(main, bg=self.BG, width=210)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # ── LEFT: Text Input ──
        self._build_text_panel(left)
        self._build_controls(left)
        self._build_progress(left)
        self._build_chart(left)

        # ── RIGHT: Settings ──
        self._build_settings_panel(right)

        # ── Footer ──
        self._sep(self)
        self._build_footer()

    def _build_text_panel(self, parent):
        frm = self._card(parent, "TEXT TO TYPE")
        self._text_input = scrolledtext.ScrolledText(
            frm,
            height=6,
            font=("Courier", 11),
            bg=self.BG3,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground=self.ACCENT,
            selectforeground=self.BG,
            relief="flat",
            bd=0,
            wrap="word",
            padx=10,
            pady=8,
        )
        self._text_input.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        self._text_input.insert("1.0",
            "The quick brown fox jumps over the lazy dog. "
            "Pack my box with five dozen liquor jugs!")

        # Char counter
        self._char_count = tk.Label(frm, text="chars: 89",
                                     bg=self.BG2, fg=self.TEXT_DIM,
                                     font=("Courier", 9))
        self._char_count.pack(side="right", padx=6, pady=2)
        self._text_input.bind("<KeyRelease>", self._update_char_count)
        frm.pack(fill="x", pady=(0, 8))

    def _build_controls(self, parent):
        frm = tk.Frame(parent, bg=self.BG)
        frm.pack(fill="x", pady=(0, 8))

        # Start / Pause / Stop
        self._btn_start = self._btn(frm, "▶  START TYPING",
                                     self._on_start, color=self.SUCCESS)
        self._btn_start.pack(side="left", padx=(0, 6))

        self._btn_pause = self._btn(frm, "⏸  PAUSE",
                                     self._on_pause, color=self.WARNING)
        self._btn_pause.pack(side="left", padx=(0, 6))
        self._btn_pause.configure(state="disabled")

        self._btn_stop = self._btn(frm, "■  STOP",
                                    self._on_stop, color=self.DANGER)
        self._btn_stop.pack(side="left")
        self._btn_stop.configure(state="disabled")

        # Countdown label
        self._countdown_lbl = tk.Label(frm, text="",
                                        bg=self.BG, fg=self.WARNING,
                                        font=("Courier", 13, "bold"))
        self._countdown_lbl.pack(side="right")

    def _build_progress(self, parent):
        frm = self._card(parent, "PROGRESS")

        self._progress_var = tk.DoubleVar(value=0)
        prog = ttk.Progressbar(frm,
                                variable=self._progress_var,
                                maximum=100,
                                style="H.Horizontal.TProgressbar")
        prog.pack(fill="x", padx=2, pady=(2, 4))

        # Stat row
        stat_row = tk.Frame(frm, bg=self.BG2)
        stat_row.pack(fill="x")

        self._stat_wpm  = self._stat_label(stat_row, "WPM",   "0")
        self._stat_chars = self._stat_label(stat_row, "CHARS", "0")
        self._stat_words = self._stat_label(stat_row, "WORDS", "0")
        self._stat_typos = self._stat_label(stat_row, "TYPOS", "0")
        self._stat_time  = self._stat_label(stat_row, "TIME",  "0:00")

        frm.pack(fill="x", pady=(0, 8))

    def _build_chart(self, parent):
        frm = self._card(parent, "LIVE SPEED GRAPH  (WPM over time)")
        self._chart = SpeedChart(frm, height=110, bd=0, highlightthickness=0)
        self._chart.pack(fill="x", padx=1, pady=1)
        frm.pack(fill="x", pady=(0, 8))

    def _build_settings_panel(self, parent):
        # WPM Slider
        wpm_card = self._card(parent, "SPEED  (WPM)")
        self._wpm_var = tk.IntVar(value=self.settings.wpm)
        self._wpm_display = tk.Label(wpm_card,
                                      text=f"{self.settings.wpm} wpm",
                                      bg=self.BG2,
                                      fg=self.ACCENT,
                                      font=("Courier", 16, "bold"))
        self._wpm_display.pack()

        slider = ttk.Scale(wpm_card,
                            from_=5, to=150,
                            variable=self._wpm_var,
                            command=self._on_wpm_change,
                            style="H.Horizontal.TScale",
                            orient="horizontal")
        slider.pack(fill="x", padx=4, pady=(2, 4))

        marks = tk.Frame(wpm_card, bg=self.BG2)
        marks.pack(fill="x", padx=4)
        for val, lbl in [(5, "5"), (50, "50"), (100, "100"), (150, "150")]:
            tk.Label(marks, text=lbl, bg=self.BG2, fg=self.TEXT_DIM,
                     font=("Courier", 8)).pack(side="left",
                                               expand=True if val != 5 else False)
        wpm_card.pack(fill="x", pady=(0, 8))

        # Profile
        profile_card = self._card(parent, "TYPING PROFILE")
        self._profile_var = tk.StringVar(value=self.settings.profile)
        combo = ttk.Combobox(profile_card,
                              textvariable=self._profile_var,
                              values=list(PROFILES.keys()),
                              state="readonly",
                              style="H.TCombobox",
                              font=("Courier", 10))
        combo.pack(fill="x", padx=4, pady=(2, 4))
        combo.bind("<<ComboboxSelected>>", self._on_profile_change)

        self._profile_desc = tk.Label(profile_card,
                                       text=PROFILES[self.settings.profile]["description"],
                                       bg=self.BG2, fg=self.TEXT_DIM,
                                       font=("Courier", 8),
                                       wraplength=190, justify="left")
        self._profile_desc.pack(fill="x", padx=4, pady=(0, 4))
        profile_card.pack(fill="x", pady=(0, 8))

        # Options
        opts_card = self._card(parent, "OPTIONS")
        self._typo_var = tk.BooleanVar(value=self.settings.enable_typos)
        ttk.Checkbutton(opts_card,
                         text="Simulate typos + correction",
                         variable=self._typo_var,
                         style="H.TCheckbutton",
                         command=self._on_typo_toggle).pack(anchor="w", pady=2)

        if not KEYBOARD_AVAILABLE:
            tk.Label(opts_card,
                     text="⚠ pynput not installed\n(simulation mode only)",
                     bg=self.BG2, fg=self.WARNING,
                     font=("Courier", 8), justify="left").pack(anchor="w", padx=4, pady=4)

        opts_card.pack(fill="x", pady=(0, 8))

        # Countdown setting
        cd_card = self._card(parent, "COUNTDOWN (sec)")
        self._cd_var = tk.IntVar(value=self.settings.countdown_seconds)
        for v in [0, 3, 5]:
            tk.Radiobutton(cd_card, text=str(v) if v else "Off",
                            variable=self._cd_var, value=v,
                            bg=self.BG2, fg=self.TEXT,
                            selectcolor=self.BG3,
                            activebackground=self.BG2,
                            font=("Courier", 9),
                            command=self._on_cd_change).pack(side="left", padx=6)
        cd_card.pack(fill="x", pady=(0, 8))

    def _build_footer(self):
        foot = tk.Frame(self, bg=self.BG)
        foot.pack(fill="x", padx=20, pady=(4, 12))
        tk.Label(foot,
                 text="Switch to target window after starting  ·  For demonstrations & accessibility only",
                 bg=self.BG, fg=self.TEXT_DIM,
                 font=("Courier", 9)).pack(side="left")

    # ── Widget Helpers ────────────────────────

    def _card(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=self.BORDER, bd=0)
        tk.Label(outer, text=title,
                 bg=self.BORDER, fg=self.TEXT_DIM,
                 font=("Courier", 8, "bold"),
                 padx=8, pady=2).pack(fill="x", anchor="w")
        inner = tk.Frame(outer, bg=self.BG2, padx=6, pady=6)
        inner.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        # Make inner behave as the return value for adding children
        # but return outer so it can be packed
        outer._inner = inner
        # Redirect pack_children to inner
        outer._real_inner = inner

        class ProxyFrame(tk.Frame):
            def __init__(self_, *a, **kw):
                pass

        # Monkey-patch: children added to outer go to inner
        def pack_to_inner(widget, **kw):
            widget.pack(in_=inner, **kw)

        # Actually just return inner so callers pack into it
        inner._title = title
        return inner

    def _btn(self, parent, text: str, cmd, color: str) -> tk.Button:
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg=self.BG,
            font=("Courier", 10, "bold"),
            relief="flat", bd=0,
            padx=12, pady=6,
            cursor="hand2",
            activebackground=color,
            activeforeground=self.BG,
        )

    def _stat_label(self, parent, name: str, value: str):
        """Creates a stat box and returns the value label for updates."""
        box = tk.Frame(parent, bg=self.BG3, padx=8, pady=4)
        box.pack(side="left", expand=True, fill="x", padx=2)
        tk.Label(box, text=name, bg=self.BG3, fg=self.TEXT_DIM,
                 font=("Courier", 7)).pack()
        val = tk.Label(box, text=value, bg=self.BG3, fg=self.TEXT,
                       font=("Courier", 13, "bold"))
        val.pack()
        return val

    def _sep(self, parent):
        tk.Frame(parent, bg=self.BORDER, height=1).pack(fill="x",
                                                         padx=20, pady=6)

    # ── Event Handlers ────────────────────────

    def _on_wpm_change(self, val):
        v = int(float(val))
        self.settings.wpm = v
        self._wpm_display.configure(text=f"{v} wpm")
        if self.engine:
            self.engine.settings.wpm = v

    def _on_profile_change(self, event=None):
        p = self._profile_var.get()
        self.settings.profile = p
        self._profile_desc.configure(
            text=PROFILES[p]["description"]
        )

    def _on_typo_toggle(self):
        self.settings.enable_typos = self._typo_var.get()

    def _on_cd_change(self):
        self.settings.countdown_seconds = self._cd_var.get()

    def _on_start(self):
        text = self._text_input.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("No Text", "Please enter text to type.")
            return

        cd = self.settings.countdown_seconds
        if cd > 0:
            self._run_countdown(cd, lambda: self._begin_typing(text))
        else:
            self._begin_typing(text)

    def _run_countdown(self, seconds: int, callback):
        """Show a countdown then fire callback."""
        self._btn_start.configure(state="disabled")
        self._countdown_lbl.configure(text=f"Starting in {seconds}…")

        def tick(n):
            if n <= 0:
                self._countdown_lbl.configure(text="")
                callback()
                return
            self._countdown_lbl.configure(text=f"Starting in {n}…")
            self.after(1000, lambda: tick(n - 1))

        tick(seconds)

    def _begin_typing(self, text: str):
        self._is_running = True
        self._is_paused = False
        self._set_status("TYPING", self.ACCENT)
        self._btn_start.configure(state="disabled")
        self._btn_pause.configure(state="normal")
        self._btn_stop.configure(state="normal")
        self._chart.reset()
        self._update_char_count()

        self.engine = TypingEngine(
            settings=self.settings,
            stats=self.stats,
            on_progress=self._on_progress,
            on_char=self._on_char_typed,
            on_done=self._on_typing_done,
        )

        self._typing_thread = threading.Thread(
            target=self.engine.type_text,
            args=(text,),
            daemon=True,
        )
        self._typing_thread.start()

    def _on_pause(self):
        if not self.engine:
            return
        if self._is_paused:
            self.engine.resume()
            self._is_paused = False
            self._btn_pause.configure(text="⏸  PAUSE")
            self._set_status("TYPING", self.ACCENT)
        else:
            self.engine.pause()
            self._is_paused = True
            self._btn_pause.configure(text="▶  RESUME")
            self._set_status("PAUSED", self.WARNING)

    def _on_stop(self):
        if self.engine:
            self.engine.stop()
        self._reset_ui_state()

    def _on_progress(self, pct: float):
        self.after(0, lambda: self._progress_var.set(pct * 100))

    def _on_char_typed(self, char: str, wpm: float):
        pass  # Stats update handled by refresh loop

    def _on_typing_done(self):
        self.after(0, self._handle_done)

    def _handle_done(self):
        self._set_status("DONE", self.SUCCESS)
        self._reset_ui_state()
        # Final WPM to chart
        final_wpm = self.stats.current_wpm()
        if final_wpm > 0:
            self._chart.add_point(final_wpm)

    def _reset_ui_state(self):
        self._is_running = False
        self._is_paused = False
        self._btn_start.configure(state="normal")
        self._btn_pause.configure(state="disabled", text="⏸  PAUSE")
        self._btn_stop.configure(state="disabled")
        self._countdown_lbl.configure(text="")

    def _set_status(self, text: str, color: str):
        self._status_lbl.configure(text=f"● {text}", fg=color)

    def _update_char_count(self, event=None):
        text = self._text_input.get("1.0", "end-1c")
        self._char_count.configure(text=f"chars: {len(text)}")

    # ── Live Stat Refresh ─────────────────────

    def _start_stat_refresh(self):
        self._refresh_stats()

    def _refresh_stats(self):
        if self._is_running and self.engine and self.engine.is_running():
            wpm = self.stats.current_wpm()
            elapsed = time.time() - self.stats.start_time

            self._stat_wpm.configure(text=f"{wpm:.0f}")
            self._stat_chars.configure(text=str(self.stats.chars_typed))
            self._stat_words.configure(text=str(self.stats.words_typed))
            self._stat_typos.configure(text=str(self.stats.typos_made))

            m = int(elapsed // 60)
            s = int(elapsed % 60)
            self._stat_time.configure(text=f"{m}:{s:02d}")

            # Update chart
            if self.stats.wpm_history:
                latest = self.stats.wpm_history[-1]
                if not self._chart.data or self._chart.data[-1] != latest:
                    self._chart.add_point(latest)

        self.after(500, self._refresh_stats)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    if not KEYBOARD_AVAILABLE:
        print(
            "Note: pynput is not installed. Running in simulation mode.\n"
            "Install it with:  pip install pynput\n"
        )

    app = HumanTyperApp()
    app.mainloop()


if __name__ == "__main__":
    main()