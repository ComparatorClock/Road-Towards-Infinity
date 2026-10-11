"""Road Towards Infinity - a clicker game about ever-bigger numbers."""
import re
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple
from PIL import Image, ImageTk

# ══════════════════════════════════════════════════════════════════════
# 1. GAME DATA  (everything you might want to tweak lives here)
# ══════════════════════════════════════════════════════════════════════

SAVE_FILE = Path("saves.txt")
BG_DIR = "assets/backgrounds/"
AUTOSAVE_MS = 30_000
NUMBER_PREFIX = "Last Significant Number: "
PLACES = 10                      # digit buttons: ones ... billions
CAP = 10 ** PLACES               # reaching ten billion ends this stage

RESOLUTIONS = [
    ("A quarter of HD (qHD)", 960, 540),
    ("Wide Super VGA", 1024, 576),
    ("High Definition (HD)", 1280, 720),
    ("High Definition+", 1600, 900),
    ("Full High Definition", 1920, 1080),
    ("Quad Wide XGA", 2048, 1152),
    ("Quadruple HD (QHD)", 2560, 1440),
    ("3K", 2880, 1620),
    ("Quad HD+ (QHD+)", 3200, 1800),
    ("4K Ultra HD (UHD)", 3840, 2160),]

# Name shown when the player first reaches 10^1, 10^2, ... 10^10.
# Index n also unlocks bronze medal n.
MILESTONE_NAMES = [
    "Ten", "Hundred", "Thousand", "Ten Thousand", "Hundred Thousand",
    "Million", "Ten Million", "Hundred Million", "Billion", "Ten Billion",]

class MedalDef(NamedTuple):
    medal_id: str
    title: str
    desc: str

BRONZE_MEDALS = [
    MedalDef("0A", "Multiple digits?!?", "Wow! How many digits can there be?"),
    MedalDef("0B", "A Franklin", "CASH MONEYYY"),
    MedalDef("0C", "Thou art so numerous thou art like sand", "By medieval standards, this was a lot of people."),
    MedalDef("0D", "Ben Franklin's Orchestra", "Ten grand can be called a band of Benjamins. Metal!"),
    MedalDef("0E", "Edge of Space", "The Karman Line is a hundred thousand Minecraft Blocks above sea level!"),
    MedalDef("0F", "Standard of Success", "If you have a million bucks, seriously, please retire - you don't need more than that."),
    MedalDef("0G", "Even More Innumerable", "Ten million is a lot of people by today's standards. That's like, one whole world-class city!"),
    MedalDef("0H", "Deep Space", "An astronomical unit - from the Earth to the Sun - is a little under 93 million miles..."),
    MedalDef("0I", "Typical Gov't Spending", "A stealth bomber costs about this much - a single high-tech plane!!"),
    MedalDef("0J", "Having a Conversation", "I don't know why this is called a dialogue..."),]
SILVER_MEDAL = MedalDef("0Z", "Next stop: Exponents", "Let's start counting how many digits we have!")
SILVER_COST = 10

class AchievementDef(NamedTuple):
    target: int          # exact value that must be hit
    before_medal: str    # shown in the hint
    hint: str
    title: str
    desc: str
    number_name: str     # shown in the "Last Significant Number" label
    bg_label: str        # button text for the background it unlocks
    bg_file: str         # assets/backgrounds/<bg_file>.png

ACHIEVEMENTS = [
    AchievementDef(69, "0B", "( ͡° ͜ʖ ͡°)", "*Catcalls*", '"My, you are quite handsome!"', "Sixty-Nine", "NSFW Joke", "69"),
    AchievementDef(666, "0C", "What number do Christians most fear?", "The Mark of the Beast", "*Doom OST plays*", "Six Hundred and Sixty Six", "Demonic", "666"),
    AchievementDef(1337, "0D", "Ar3 y0u a l33t g@mer?", "L33t Xp3rt", "Welc0me t0 th3 b1g le@gues, pl@yer!", "Thirteen Hundred and Thirty-Seven", "L33t Sp33k", "hachorz"),
    AchievementDef(92955807, "0H", "The scale of empty is...", "The Final Frontier", "These are the voyages...", "Ninety-Two Million, Nine Hundred and Fifty-Five Thousand, Eight Hundred and Seven", "The Infinite Dark", "cosmos"),
    AchievementDef(299792458, "0I", "The ultimate speed is...", "v = c", "Nothing goes faster than light. Except the fabric of reality itself :/", "Two Hundred and Ninety-Nine Million, Seven Hundred and Ninety-Two Thousand, Four Hundred and Fifty-Eight", "Massless Velocity", "light"),
    AchievementDef(8300678395, "0J", "Global Population", "The Total of Humanity", "Being Diverse Since the Stone Age!", "Eight Billion, Three Hundred Million, Six Hundred and Seventy-Eight Thousand, Three Hundred and Ninety-Five", "Human Variety", "diversity"),]

INTRO_TEXT = "\n\n".join([
    "Hello, and welcome to Road Towards Infinity! This is a clicker game about exploring progressively bigger and bigger numbers...",
    "For now, you can only work with addition - but this is only the beginning! For now, click the button with the zero on it to start counting up to 10. Once you reach ten, the tens place will unlock, allowing you to add ten at a time. Digits will be unlocked like so until you reach ten billion - your first objective.",
    "Use the medals tab to track your progress. Use the settings screen to adjust choice of background, manage save states, or change the background theme.",
    "Themes can be unlocked via achievements, which are typically optional bonus challenges - can you puzzle out what the hints refer to, before it's too late?",
    "Good luck!",])
FIRST_MILESTONE_TEXT = "\n\n".join([
    "Hello again!",
    "If you are seeing this, that means you have reached ten billion - congratulations!",
    "How many of the bonus achievements did you snag? If you missed one, too bad, you'll just have to restart if you want it and/or want to 100% the game.",
    "You may have noticed that on the medals screen, you've been gaining something called Medal Points from when you collect Bronze Medals. You should now have ten - use them to purchase your very first Silver Medal, which will unlock the next stage of the game.",
    "But what is the next stage, you ask? Well, you may have noticed that it's gotten a bit tricky keeping track of the digits. To reach bigger numbers, we need more concise representations of those numbers.",
    "Enter exponents - now, the number is represented by a base (which will always be ten going forward) and something called an exponent. For now, think of the exponent as a count of how many digits the number has.",
    "Your next objective is to reach ten to the ten billion, also known as a trialogue.",
    "Be aware that you're going to get numbers far larger than you ever thought possible very quickly - good luck!",])

# ══════════════════════════════════════════════════════════════════════
# 2. STATE
# ══════════════════════════════════════════════════════════════════════

class GameState:
    """All mutable game progress in one place (instead of a dozen globals)."""
    def __init__(self):
        self.current_save = -1
        self.autosave_job = None
        self.loading = False     # True while a save is being restored
        self.reset()
    def reset(self):
        self.value = 0
        self.ach = 0             # achievements collected
        self.bronze = 0
        self.silver = 0
        self.points = 0          # medal points
        self.to_collect = 0      # medals available but not yet clicked

state = GameState()
savestates = []                  # one string per save, see serialize_save()

# Layout values recalculated whenever the resolution changes.
view = SimpleNamespace(top_height=0, value_width=0, background="default", buttons_window=None)

# ══════════════════════════════════════════════════════════════════════
# 3. MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════

root = tk.Tk()
root.title("Road Towards Infinity")
root.resizable(False, False)
root.iconphoto(False, tk.PhotoImage(file="assets/icon.png"))

game_canvas, settings_canvas, ach_canvas, medal_canvas = (tk.Canvas(root, highlightthickness=0) for _ in range(4))
ALL_CANVASES = (game_canvas, settings_canvas, ach_canvas, medal_canvas)

menus = tk.Frame(root)
menus.pack(side="bottom", fill="x")

# -- game screen: top bar (name | spacer image | number) and digit buttons
stats = tk.Frame(game_canvas, height=view.top_height)
stats.pack(side="top", fill="x")
buttons_frame = tk.Frame(game_canvas)
num_name = tk.Label(stats, text=NUMBER_PREFIX + "Zero", bg="black", fg="white", justify="center", anchor="center")
num_number = tk.Label(stats, text="0", bg="black", fg="white", justify="center", anchor="center")
image_label = tk.Label(stats, borderwidth=2, relief="raised")
digit_buttons = [None] * PLACES          # digit_buttons[p] adds 10**p; None until unlocked

STAT_FONT = ("Arial", 12, "bold")

def make_stat_label(parent): return tk.Label(parent, font=STAT_FONT, borderwidth=2, relief="raised")
def progress_text(label, count, total):  return f"{label}: {count}/{total} ({100 * count / total:.2f}%)"

# -- achievements screen header
ach_stats = make_stat_label(ach_canvas)
ach_stats_window = ach_canvas.create_window(0, 0, window=ach_stats, anchor="nw")

# -- medals screen header
medal_stats = tk.Frame(medal_canvas)
medal_stats.pack(side="top", fill="x")
bronze_stat, silver_stat, points_stat = (make_stat_label(medal_stats) for _ in range(3))
for label in (bronze_stat, silver_stat, points_stat): label.pack(side="left", fill="both", expand=True)

# ══════════════════════════════════════════════════════════════════════
# 4. DISPLAY HELPERS  (font fitting, tiled backgrounds, widget wrapping)
# ══════════════════════════════════════════════════════════════════════

_wrap_font = None     # one reusable Font object instead of ~200 new ones per call
_fit_cache = {}       # (normalized text, width, height) -> best font size

def _best_font_size(text, wrap_w, max_h):
    """Largest font size whose wrapped text fits in max_h (binary search)."""
    global _wrap_font
    if _wrap_font is None: _wrap_font = tkfont.Font(family="Arial", size=-12, weight="bold")
    words = text.split()
    def fits(size):
        _wrap_font.configure(size=-size)
        lines, current = 0, ""
        for word in words:
            trial = (current + " " + word) if current else word
            if _wrap_font.measure(trial) <= wrap_w or not current: current = trial
            else:
                lines += 1
                current = word
        if current: lines += 1
        return _wrap_font.metrics("linespace") * lines <= max_h
    lo, hi = 8, max(12, int(view.top_height * 0.5))
    if not fits(lo): return lo
    while lo < hi:                      # fits() is monotonic in font size
        mid = (lo + hi + 1) // 2
        if fits(mid): lo = mid
        else: hi = mid - 1
    return lo
def autowrap(label):
    wrap_w = int(view.value_width - 15)
    label.config(wraplength=wrap_w)
    text = label.cget("text")
    if not text or wrap_w <= 0 or view.top_height <= 0: return
    # Arial digits are all the same width, so "123" and "456" fit identically
    key = (re.sub(r"\d", "0", text), wrap_w, int(view.top_height))
    size = _fit_cache.get(key)
    if size is None: size = _fit_cache[key] = _best_font_size(text, wrap_w, view.top_height - 6)
    if getattr(label, "_applied_size", None) != (size, wrap_w):
        label.config(font=("Arial", -size, "bold"))
        label._applied_size = (size, wrap_w)
def wrap_widgets(canvas, max_width, pad=15, gap=10):
    """Flow a canvas's child widgets left-to-right, wrapping like text."""
    canvas.update_idletasks()
    top_offset = 0
    if canvas is ach_canvas:
        canvas.itemconfig(ach_stats_window, width=max_width)
        canvas.update_idletasks()
        top_offset = ach_stats.winfo_reqheight()
    x, y, row_h = pad, pad + top_offset, 0
    canvas.delete("floating")
    for w in canvas.winfo_children():
        if w is ach_stats: continue
        w.update_idletasks()
        w_w, w_h = w.winfo_reqwidth(), w.winfo_reqheight()
        if x + w_w > max_width - pad:
            x = pad
            y += row_h + gap
            row_h = 0
        canvas.create_window(x, y, window=w, anchor="nw", tags="floating")
        x += w_w + gap
        row_h = max(row_h, w_h)

_raw_bg_cache = {}
def tile_background(canvas):
    canvas.update_idletasks()
    width, height = canvas.winfo_width(), canvas.winfo_height()
    if width <= 1 or height <= 1: return
    key = (view.background, width, height)
    if getattr(canvas, "_tile_key", None) == key: return                                      # already up to date
    raw = _raw_bg_cache.get(view.background)
    if raw is None:  raw = _raw_bg_cache[view.background] = Image.open(f"{BG_DIR}{view.background}.png").convert("RGB")
    tiled = Image.new("RGB", (width, height))
    for x in range(0, width, raw.width):
        for y in range(0, height, raw.height): tiled.paste(raw, (x, y))
    canvas.tiled_photo = ImageTk.PhotoImage(tiled)
    canvas.delete("tile_bg")
    canvas.create_image(0, 0, image=canvas.tiled_photo, anchor="nw", tags="tile_bg")
    canvas.tag_lower("tile_bg")
    canvas._tile_key = key
def update_bg(name):
    view.background = name
    for canvas in ALL_CANVASES: tile_background(canvas)
def update_dimensions(new_width, new_height):
    root.geometry(f"{new_width}x{new_height}")
    view.top_height = 0.20 * new_height
    spacer_width = view.top_height * 1.5
    view.value_width = 0.5 * (new_width - spacer_width) - 2

    spacer_image = Image.open("assets/spacer.png")
    spacer_image.thumbnail((spacer_width, view.top_height), Image.Resampling.LANCZOS)
    spacer = ImageTk.PhotoImage(spacer_image)
    image_label.config(image=spacer)
    image_label.image = spacer                      # keep a reference alive
    image_label.pack_forget()
    image_label.pack(expand=True, fill="y")

    if view.buttons_window is None: view.buttons_window = game_canvas.create_window(0, view.top_height, window=buttons_frame, anchor="nw")
    else: game_canvas.coords(view.buttons_window, 0, view.top_height)

    num_name.place(x=0, y=0, width=view.value_width, height=view.top_height + 4)
    num_number.place(x=view.value_width + spacer_width + 4, y=0, width=view.value_width, height=view.top_height + 4)
    autowrap(num_name)
    autowrap(num_number)

    for canvas in ALL_CANVASES: tile_background(canvas)
def show_screen(canvas):
    for other in ALL_CANVASES:
        if other is not canvas: other.pack_forget()
    canvas.pack(fill=tk.BOTH, expand=True)
    tile_background(canvas)
def custom_msg_box(title, text):
    dialog = tk.Toplevel(root)
    dialog.title(title)
    tk.Label(dialog, text=text, padx=20, pady=20, justify="left", wraplength=0.5 * root.winfo_width()).pack(fill="both", expand=True)
    tk.Button(dialog, text="OK", command=dialog.destroy, width=10).pack(pady=10)
    dialog.transient(root)
    dialog.update()
    dialog.grab_set()
    dialog.wait_window()

# ══════════════════════════════════════════════════════════════════════
# 5. COLLECTIBLES  (achievements and medals share one widget class)
# ══════════════════════════════════════════════════════════════════════

class CollectibleWidget(tk.Canvas):
    """A tile that goes locked -> available (❓) -> collected, with a hover tooltip.

    item_type: "ach" (collected automatically), "bronze" or "silver" (clicked).
    key:       the medal id ("0A") or achievement number, used for saving.
    """
    COLLECTED_ICON = {"ach": "🏅", "bronze": "🥉", "silver": "🥈"}

    def __init__(self, master, item_type, hint_text, collected_text, key, on_collected=None):
        super().__init__(master, width=50, height=50, highlightthickness=0, bd=5, highlightbackground="gray", relief="raised")
        
        self.item_type = item_type
        self.clickable = item_type != "ach"
        self.hint_text = hint_text
        self.collected_text = collected_text
        self.key = key
        self.on_collected = on_collected
        self.tipwindow = None
        self.text_id = self.create_text(30, 30, text="", font=("tahoma", "24", "normal"))
        self.reset()

        if self.clickable: self.bind("<Button-1>", self.on_collect)
        self.bind("<Enter>", self.show_tip)
        self.bind("<Leave>", self.hide_tip)
    def reset(self):
        self.is_collected = False
        self.hover_text = self.hint_text
        self.enabled = not self.clickable           # medals start locked, achievements start live
        self.itemconfig(self.text_id, text="❓" if self.enabled else "🔒")
    def set_enabled(self, status):
        was_enabled = self.enabled
        self.enabled = status
        if self.clickable:
            if status and not was_enabled:
                state.to_collect += 1
                refresh_stats()
        elif not status: self.itemconfig(self.text_id, text="❌")
        if status and not self.is_collected: self.itemconfig(self.text_id, text="❓")
    def on_collect(self, event=None):
        if not self.enabled: return
        if not self.is_collected:
            self.is_collected = True
            self.hover_text = self.collected_text
            self.itemconfig(self.text_id, text=self.COLLECTED_ICON[self.item_type])
            if self.item_type == "ach": state.ach += 1
            elif self.item_type == "bronze":
                state.bronze += 1
                state.points += 1
                state.to_collect -= 1
            else:                                   # silver spends all medal points
                state.silver += 1
                state.points = 0
                state.to_collect -= 1
            refresh_stats()
            if self.tipwindow: self.tipwindow.label.config(text=self.hover_text)
            if self.on_collected: self.on_collected()
        check_silver_unlock()
    def show_tip(self, event=None):
        if self.tipwindow or not self.hover_text: return
        x = self.winfo_rootx() + 20
        y = self.winfo_rooty() + self.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)                # no title bar
        tw.wm_geometry(f"+{x}+{y}")
        tw.label = tk.Label(tw, text=self.hover_text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("tahoma", "8", "normal"))
        tw.label.pack(ipadx=1)
    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ══════════════════════════════════════════════════════════════════════
# 6. BUILD THE SCREENS
# ══════════════════════════════════════════════════════════════════════

# -- medals screen
medal_grid = tk.Frame(medal_canvas, padx=10, pady=10)
medal_grid.pack(side="top", anchor="nw")
tk.Label(medal_grid, text="Row 0:", font=("Arial", 24)).grid(row=0, column=0, padx=5, pady=5)

bronze_medals = []
for column, m in enumerate(BRONZE_MEDALS, start=1):
    widget = CollectibleWidget(medal_grid, "bronze", f"Medal {m.medal_id}\nDesc: ???", f"{m.title}\nDesc: {m.desc}", key=m.medal_id)
    widget.grid(row=0, column=column, padx=5, pady=5)
    bronze_medals.append(widget)

silver_medal = CollectibleWidget(medal_grid, "silver", f"Medal {SILVER_MEDAL.medal_id}\nDesc: Costs {SILVER_COST} Medal Points.", f"{SILVER_MEDAL.title}\nDesc: {SILVER_MEDAL.desc}", key=SILVER_MEDAL.medal_id)
silver_medal.grid(row=0, column=len(bronze_medals) + 1, padx=5, pady=5)

medal_list = bronze_medals + [silver_medal]
MEDAL_KEYS = [m.key for m in medal_list]

# -- settings screen: resolutions (left), backgrounds (right), saves (top)
resolutions_frame = tk.Frame(settings_canvas)
resolutions_frame.pack(side="left", anchor="nw")
tk.Label(resolutions_frame, text="Game Resolutions").pack(side="top", fill="x", expand=True)
for name, w, h in RESOLUTIONS: tk.Button(resolutions_frame, text=f"{name} ({w}x{h})", command=lambda w=w, h=h: update_dimensions(w, h)).pack(side="top", fill="x", expand=True)

bgs_frame = tk.Frame(settings_canvas)
bgs_frame.pack(side="right", anchor="ne")
tk.Label(bgs_frame, text="Unlocked Backgrounds").pack(side="top", fill="x", expand=True)
tk.Button(bgs_frame, text="Default", command=lambda: update_bg("default")).pack(side="top", fill="x", expand=True)
# One button per achievement; each is only packed (shown) once its achievement is collected.
bg_buttons = [tk.Button(bgs_frame, text=a.bg_label, command=lambda f=a.bg_file: update_bg(f)) for a in ACHIEVEMENTS]

def show_bg_button(index):
    if not bg_buttons[index].winfo_manager(): bg_buttons[index].pack(side="top", fill="x", expand=True)

saves_frame = tk.Frame(settings_canvas)
saves_frame.pack(side="top", anchor="n")
tk.Label(saves_frame, text="Manage save states here!").pack(side="top", fill="x", expand=True)
tk.Button(saves_frame, text="Create New Save File", command=lambda: create_save()).pack(side="top", fill="x", expand=True)
save_rows = []

# -- achievements screen
achievement_widgets = [CollectibleWidget(ach_canvas, "ach", f"Name: ???\nCollect before Medal {a.before_medal}.\nHint: {a.hint}", f"{a.title}\nDesc: {a.desc}", key=number, on_collected=lambda i=number - 1: show_bg_button(i)) for number, a in enumerate(ACHIEVEMENTS, start=1)]
ach_canvas.bind("<Configure>", lambda e: wrap_widgets(ach_canvas, e.width))

# -- bottom menu
def add_menu_button(text, command, **options):
    button = tk.Button(menus, text=text, command=command, **options)
    button.pack(side="left", fill="both", expand=True)
    return button

add_menu_button("Settings", lambda: show_screen(settings_canvas))
game_btn = add_menu_button("Game", lambda: show_screen(game_canvas))
add_menu_button("Quit Game", root.destroy, fg="red")
achs_btn = add_menu_button("Achievements", lambda: show_screen(ach_canvas))
medals_btn = add_menu_button("Medals", lambda: show_screen(medal_canvas))
LOCKED_UNTIL_SAVE_LOADED = (game_btn, achs_btn, medals_btn)
for btn in LOCKED_UNTIL_SAVE_LOADED: btn.config(state=tk.DISABLED)

# ══════════════════════════════════════════════════════════════════════
# 7. GAME LOGIC
# ══════════════════════════════════════════════════════════════════════

def refresh_stats():
    """Redraw every progress label from `state`."""
    ach_stats.config(text=progress_text("Achievements Collected", state.ach, len(achievement_widgets)))
    bronze_stat.config(text=progress_text("Bronze Medals Collected", state.bronze, len(bronze_medals)))
    silver_stat.config(text=progress_text("Silver Medals Collected", state.silver, 1))
    points_stat.config(text=f"Medal Points: {state.points}")
    medals_btn.config(text="Medals" if state.to_collect == 0 else f"Medals ({state.to_collect})")
def check_silver_unlock():
    if state.points >= SILVER_COST and not silver_medal.enabled:
        silver_medal.set_enabled(True)
        if not state.loading: ustom_msg_box("FIRST MILESTONE ACHIEVED", FIRST_MILESTONE_TEXT)
def set_number_name(name): num_name.config(text=NUMBER_PREFIX + name)
def reset_digit_buttons():
    for i, btn in enumerate(digit_buttons):
        if btn is not None:
            btn.destroy()
            digit_buttons[i] = None
def ensure_digit_button(place):
    if digit_buttons[place] is None:
        btn = tk.Button(buttons_frame, command=lambda: add_to_value(10 ** place))
        btn.pack(side="right")
        digit_buttons[place] = btn
def add_to_value(amount):
    state.value += amount
    update_main()
def update_main():
    value = state.value
    if not silver_medal.is_collected:               # after buying the silver medal, this stage is over
        # Unlock the next digit button and bronze medal at each power of ten.
        for place in range(PLACES):
            if place == 0 or value >= 10 ** place: ensure_digit_button(place)
        for power, (medal, name) in enumerate(zip(bronze_medals, MILESTONE_NAMES), start=1):
            if value >= 10 ** power and not medal.enabled:
                medal.set_enabled(True)
                set_number_name(name)

        # Achievements need an exact value; overshooting one forfeits it.
        for ach, spec in zip(achievement_widgets, ACHIEVEMENTS):
            if value == spec.target:
                ach.on_collect()
                set_number_name(spec.number_name)
            elif value > spec.target and not ach.is_collected: ach.set_enabled(False)

        if value >= CAP:                            # stage cap reached: freeze the buttons
            for btn in digit_buttons: btn.config(state=tk.DISABLED)
        num_number.config(text=str(value))

    autowrap(num_name)
    autowrap(num_number)

    for place, btn in enumerate(digit_buttons):
        if btn is None: continue
        if place == PLACES - 1 and value >= CAP: btn.config(text=str(value)[:2])         # leading "10" of ten billion
        else: btn.config(text=str(value // 10 ** place % 10))

# ══════════════════════════════════════════════════════════════════════
# 8. SAVING AND LOADING
#    A save is one line:  "<latest medal or None>; <ach1, ach2, ... or None>"
# ══════════════════════════════════════════════════════════════════════

def read_saves():
    if not SAVE_FILE.exists(): return []
    return [line.strip() for line in SAVE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
def write_saves(): SAVE_FILE.write_text("".join(line + "\n" for line in savestates), encoding="utf-8")
def serialize_save():
    latest = None
    for medal in medal_list:                        # medals are collected in order
        if not medal.is_collected: break
        latest = medal.key
    achs = ", ".join(f"ach{a.key}" for a in achievement_widgets if a.is_collected)
    return f"{latest or 'None'}; {achs or 'None'}"
def parse_save(line):
    """Return (latest medal id or None, [achievement numbers])."""
    medal_part, _, ach_part = line.partition(";")
    medal = medal_part.strip()
    medal = medal if medal in MEDAL_KEYS else None
    numbers = []
    for token in ach_part.split(","):
        token = token.strip().lower()
        if token.startswith("ach") and token[3:].isdigit(): numbers.append(int(token[3:]))
    return medal, numbers
def save_preview(line):
    medal, achs = parse_save(line)
    if medal is None and not achs: return "Empty Save\n0 Achievements"
    return f"Latest medal: Medal {medal or 'None'}\n{len(achs)} Achievement(s)"
def save_current():
    if 0 <= state.current_save < len(savestates):
        savestates[state.current_save] = serialize_save()
        write_saves()
def schedule_autosave():
    if state.autosave_job is not None:  root.after_cancel(state.autosave_job)
    state.autosave_job = root.after(AUTOSAVE_MS, autosave)
def autosave():
    save_current()
    refresh_save_list()
    schedule_autosave()
def load_save(index):
    state.loading = True
    state.current_save = index
    state.reset()
    for widget in medal_list + achievement_widgets: widget.reset()
    for btn in bg_buttons: btn.pack_forget()
    update_bg("default")
    reset_digit_buttons()
    last_medal, ach_numbers = parse_save(savestates[index])
    value = 0
    if last_medal:
        last_index = MEDAL_KEYS.index(last_medal)
        for medal in medal_list[:last_index + 1]:
            medal.set_enabled(True)
            medal.on_collect()
        if last_index < len(bronze_medals): value = 10 ** (last_index + 1)          # the value at which that medal unlocks
    for number in ach_numbers:
        if 1 <= number <= len(achievement_widgets):
            achievement_widgets[number - 1].on_collect()
            value = max(value, ACHIEVEMENTS[number - 1].target)
    state.value = value
    state.loading = False

    refresh_stats()
    update_main()
    for btn in LOCKED_UNTIL_SAVE_LOADED: btn.config(state=tk.NORMAL)
    refresh_save_list()
    schedule_autosave()
    show_screen(game_canvas)
def create_save():
    savestates.append("None; None")
    write_saves()
    load_save(len(savestates) - 1)
    custom_msg_box("INTRODUCTION TO NUMBERS", INTRO_TEXT)
def delete_save(index):
    if not 0 <= index < len(savestates): return
    savestates.pop(index)
    write_saves()
    if state.current_save > index: state.current_save -= 1
    refresh_save_list()
def refresh_save_list():
    for row in save_rows: row.destroy()
    save_rows.clear()
    for index, line in enumerate(savestates):
        if ";" not in line: continue
        row = tk.Frame(saves_frame, bg="dark slate gray")
        row.pack(side="top", fill="x", expand=True, pady=5)
        tk.Button(row, text="✔️", command=lambda i=index: load_save(i)).pack(side="left", fill="both", expand=True)
        tk.Label(row, text=save_preview(line)).pack(side="left", fill="both", expand=True)
        delete_btn = tk.Button(row, text="🗑️", command=lambda i=index: delete_save(i))
        if index == state.current_save: delete_btn.config(state=tk.DISABLED)
        delete_btn.pack(side="left", fill="both", expand=True)
        save_rows.append(row)

# ══════════════════════════════════════════════════════════════════════
# 9. START
# ══════════════════════════════════════════════════════════════════════

savestates = read_saves()
refresh_stats()
update_dimensions(1280, 720)
show_screen(settings_canvas)
update_main()
refresh_save_list()
root.mainloop()