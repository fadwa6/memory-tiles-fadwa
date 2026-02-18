import pygame, os, random, json

# 1) =============إعدادات عامة====================
WIDTH  = 560
HEIGHT = 680
TOP_MARGIN = 110
FPS = 60

# مدة تأثير الانتقال (Fade) بالمللي ثانية
FADE_MS = 450

# ماذا يحدث عند الفوز بآخر مستوى؟
MAX_LEVEL_BEHAVIOR = "STAY"  # "STAY" أو "MENU"

# ==================== 2) ألوان (RGB)========================

COLOR_BG = (207, 252, 246)
COLOR_BORDER = (140, 245, 230)
COLOR_TEAL_DARK = (35, 130, 130)
COLOR_TEAL_LIGHT = (55, 150, 150)
COLOR_LINE = (120, 220, 215)
COLOR_ORANGE = (245, 165, 40)
COLOR_ORANGE_BRIGHT = (255, 185, 60)
COLOR_DARK = (40, 40, 40)
COLOR_TRACK = (235, 235, 235)

CARD_BACK_COL = (175, 235, 230)
CARD_FRONT_COL = (240, 255, 254)
CARD_BORDER_COL = (90, 190, 185)

# ================ 3) تشغيل pygame (الصوت أولاً)=======================
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Tiles By:Fadwa")

# خطوط
FONT_BIG = pygame.font.SysFont("Arial", 46, bold=True)
FONT_MED = pygame.font.SysFont("Arial", 28, bold=True)
FONT_SML = pygame.font.SysFont("Arial", 20, bold=True)

# ================= 4) مسارات الملفات==================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDS_FOLDER = os.path.join(BASE_DIR, "cards")
SCORE_FILE = os.path.join(BASE_DIR, "highscore.json")

# دالة ترجع مسار كامل لملف داخل المشروع
def resource_path(file_name):
    return os.path.join(BASE_DIR, file_name)

# ================== 5) دوال مساعدة بسيطة======================

def draw_text(surface, text, font, color, x, y, center=False):
    # تحويل النص لصورة ثم رسمها
    img = font.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)

def draw_separator(surface, y):
    pygame.draw.line(surface, COLOR_LINE, (60, y), (WIDTH - 60, y), 2)

def load_high_score():
    # قراءة أعلى نتيجة من ملف json
    if not os.path.exists(SCORE_FILE):
        return 0
    try:
        f = open(SCORE_FILE, "r", encoding="utf-8")
        data = json.load(f)
        f.close()
        if "high" in data:
            return int(data["high"])
        return 0
    except:
        return 0

def save_high_score(value):
    # حفظ أعلى نتيجة في ملف json
    try:
        f = open(SCORE_FILE, "w", encoding="utf-8")
        json.dump({"high": int(value)}, f)
        f.close()
    except:
        pass

def load_image(file_name, size=None):
    # تحميل صورة من المشروع (لو ما موجودة يرجع None)
    try:
        img = pygame.image.load(resource_path(file_name)).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        return img
    except:
        return None

def load_sound(file_name, volume=0.7):
    # تحميل صوت (لو ما موجود يرجع None)
    try:
        s = pygame.mixer.Sound(resource_path(file_name))
        try:
            s.set_volume(volume)
        except:
            pass
        return s
    except:
        return None

def get_card_images():
    # جلب كل صور الكروت من مجلد cards
    paths = []
    if not os.path.isdir(CARDS_FOLDER):
        return paths

    files = os.listdir(CARDS_FOLDER)
    for f in files:
        low = f.lower()
        if low.endswith(".png") or low.endswith(".jpg") or low.endswith(".jpeg"):
            paths.append(os.path.join(CARDS_FOLDER, f))
    return paths

def try_play_music():
    # تجربة تشغيل موسيقى خلفية بصيغ مختلفة
    names = ["bg_music.mp3", "bg_music.ogg", "bg_music.wav"]
    for name in names:
        full_path = resource_path(name)
        if os.path.exists(full_path):
            try:
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.set_volume(0.35)
                pygame.mixer.music.play(-1)
                return True
            except:
                pass
    return False

# ==============# 6) سلايدر الصعوبة (مبتدئ: بسيط وواضح)===================
class Slider:
    def __init__(self, x, y, w, h, options, start_index=1):
        self.box = pygame.Rect(x, y, w, h)

        # مسار السلايدر
        self.track = pygame.Rect(x + 40, y + h // 2 + 25, w - 80, 16)

        self.options = options
        self.index = start_index
        self.dragging = False

    def knob_position(self):
        # حساب مكان الدائرة بناءً على index
        count = len(self.options)
        if count <= 1:
            percent = 0
        else:
            percent = self.index / (count - 1)

        knob_x = self.track.x + int(percent * self.track.w)
        knob_y = self.track.centery
        return knob_x, knob_y

    def set_index_from_mouse(self, mouse_x):
        # تحديد index حسب مكان الماوس على المسار
        if mouse_x < self.track.left:
            mouse_x = self.track.left
        if mouse_x > self.track.right:
            mouse_x = self.track.right

        count = len(self.options)
        if count <= 1:
            self.index = 0
            return

        ratio = (mouse_x - self.track.left) / self.track.w
        self.index = int(round(ratio * (count - 1)))

    def handle_event(self, e):
        # التعامل مع أحداث الماوس
        if e.type == pygame.MOUSEBUTTONDOWN:
            kx, ky = self.knob_position()
            knob_rect = pygame.Rect(0, 0, 44, 44)
            knob_rect.center = (kx, ky)

            if knob_rect.collidepoint(e.pos) or self.track.collidepoint(e.pos):
                self.dragging = True
                self.set_index_from_mouse(e.pos[0])

        elif e.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif e.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.set_index_from_mouse(e.pos[0])

    def draw(self, surface):
        # رسم صندوق السلايدر
        pygame.draw.rect(surface, COLOR_BORDER, self.box, border_radius=18)
        inner = self.box.inflate(-10, -10)
        pygame.draw.rect(surface, COLOR_BG, inner, border_radius=14)

        draw_text(surface, "DIFFICULTY", FONT_MED, COLOR_TEAL_DARK, inner.x + 18, inner.y + 15)
        draw_text(surface, "easy", FONT_MED, COLOR_TEAL_LIGHT, inner.x + 18, inner.y + 55)
        draw_text(surface, "hard", FONT_MED, COLOR_TEAL_LIGHT, inner.right - 70, inner.y + 55)

        opt = self.options[self.index]
        draw_text(surface, f"{opt['rows']} x {opt['cols']}", FONT_BIG, COLOR_ORANGE, inner.centerx, inner.y + 60, True)

        # مسار + دائرة
        pygame.draw.rect(surface, COLOR_TRACK, self.track, border_radius=10)
        kx, ky = self.knob_position()
        pygame.draw.circle(surface, COLOR_ORANGE_BRIGHT, (kx, ky), 18)

# ===================# 7) اختيار اللاعبين (مبتدئ)=======================
class PlayersBox:
    def __init__(self, x, y, w, h):
        self.box = pygame.Rect(x, y, w, h)
        self.players = 1

        self.button = pygame.Rect(0, 0, 320, 92)
        self.button.center = (x + w // 2, y + 95)

        self.img1 = load_image("players_1.png", (170, 70))
        self.img2 = load_image("players_2.png", (170, 70))

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.button.collidepoint(e.pos):
                # تبديل بين 1 و 2
                if self.players == 1:
                    self.players = 2
                else:
                    self.players = 1

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_BORDER, self.box, border_radius=18)
        inner = self.box.inflate(-10, -10)
        pygame.draw.rect(surface, COLOR_BG, inner, border_radius=14)

        draw_text(surface, "PLAYERS", FONT_MED, COLOR_TEAL_DARK, inner.centerx, inner.y + 18, True)

        pygame.draw.rect(surface, COLOR_BORDER, self.button, border_radius=20)
        btn_in = self.button.inflate(-8, -8)
        pygame.draw.rect(surface, COLOR_BG, btn_in, border_radius=16)

        if self.players == 2:
            highlight = COLOR_ORANGE_BRIGHT
        else:
            highlight = COLOR_TEAL_LIGHT

        pygame.draw.rect(surface, highlight, btn_in, 4, border_radius=16)

        if self.players == 1:
            img = self.img1
        else:
            img = self.img2

        if img:
            surface.blit(img, img.get_rect(center=(btn_in.centerx, btn_in.centery - 6)))
        else:
            draw_text(surface, "1 PLAYER" if self.players == 1 else "2 PLAYERS",
                      FONT_MED, highlight, btn_in.centerx, btn_in.centery - 8, True)

        draw_text(surface, "SOLO" if self.players == 1 else "VS",
                  FONT_SML, COLOR_TEAL_LIGHT, inner.centerx, inner.bottom - 25, True)

# =========================================================
# 8) منطق اللعبة (نسخة مبتدئ)
# =========================================================
class Game:
    def __init__(self):
        # حالات اللعبة: MENU / PLAY / WIN / OVER
        self.state = "MENU"

        # أعلى نتيجة (للعب الفردي)
        self.high_score = load_high_score()

        # واجهة المستخدم
        self.slider = Slider(40, 180, 480, 170, [
            {"rows": 2, "cols": 3, "time": 30},
            {"rows": 3, "cols": 4, "time": 50},
            {"rows": 4, "cols": 4, "time": 70},
            {"rows": 4, "cols": 5, "time": 100},
            {"rows": 6, "cols": 6, "time": 150},
        ])

        self.players_box = PlayersBox(40, 360, 480, 150)

        # صور الكروت
        self.card_files = get_card_images()

        # مستويات
        self.level = self.slider.index
        self.max_level = len(self.slider.options) - 1

        # أصوات وصور أزرار
        self.flip_sound = load_sound("flip.wav", 0.7)
        self.home_img = load_image("home_icon.png", (80, 80))
        self.restart_img = load_image("restart_icon.png", (80, 80))
        self.coin_img = load_image("coin_icon.png", (35, 35))

        self.home_rect = pygame.Rect(WIDTH // 2 - 120, 580, 80, 80)
        self.restart_rect = pygame.Rect(WIDTH // 2 + 40, 580, 80, 80)
        self.start_btn = pygame.Rect(180, 565, 200, 80)

        # Fade
        self.fade_alpha = 0
        self.fading = False
        self.fade_dir = 1
        self.fade_start_ticks = 0
        self.fade_action = None

        # Shake
        self.shake = 0

        # تجهيز أول مستوى
        self.reset_level(self.level)

    def reset_level(self, level_index):
        # تجهيز بيانات المستوى
        if level_index < 0:
            level_index = 0
        if level_index > self.max_level:
            level_index = self.max_level
        self.level = level_index

        opt = self.slider.options[self.level]
        self.rows = opt["rows"]
        self.cols = opt["cols"]
        self.time_limit = opt["time"]

        # حساب حجم البلاطة ومكان الشبكة
        play_h = HEIGHT - TOP_MARGIN - 40
        size1 = (WIDTH - 80) // self.cols
        size2 = play_h // self.rows
        self.tile_size = min(size1, size2)

        self.grid_w = self.tile_size * self.cols
        self.grid_h = self.tile_size * self.rows
        self.grid_x = (WIDTH - self.grid_w) // 2
        self.grid_y = TOP_MARGIN + (play_h - self.grid_h) // 2 + 20

        # اختيار صور الأزواج
        pairs = (self.rows * self.cols) // 2

        chosen = []
        if len(self.card_files) >= pairs:
            chosen = random.sample(self.card_files, pairs)
        else:
            # إذا الصور قليلة نكررها
            if len(self.card_files) == 0:
                chosen = [None] * pairs
            else:
                while len(chosen) < pairs:
                    for p in self.card_files:
                        if len(chosen) < pairs:
                            chosen.append(p)

        # تكرار كل صورة مرتين ثم خلط
        self.card_values = chosen + chosen
        random.shuffle(self.card_values)

        # تحميل صور الكروت بالحجم المناسب
        self.card_images = []
        for p in self.card_values:
            if p is None:
                self.card_images.append(None)
            else:
                try:
                    img = pygame.image.load(p).convert_alpha()
                    img = pygame.transform.smoothscale(img, (self.tile_size - 15, self.tile_size - 15))
                    self.card_images.append(img)
                except:
                    self.card_images.append(None)

        # حالة الكروت
        total = self.rows * self.cols
        self.opened = [False] * total
        self.picked = []      # نخزن رقم الكروت المفتوحة حالياً
        self.locked = False   # لمنع الضغط أثناء انتظار الإغلاق
        self.hide_timer = None  # (i1, i2, وقت_الإغلاق)

        # نقاط ووقت
        self.score = 0
        self.time_elapsed = 0

        # لاعبين
        self.player_scores = [0, 0]
        self.turn = 0

    def start(self, level_index=None):
        # بدء اللعب
        self.state = "PLAY"
        if level_index is not None:
            self.level = level_index
        self.reset_level(self.level)
        self.start_ticks = pygame.time.get_ticks()

    def begin_fade(self, action):
        # تشغيل fade وتحديد ماذا نفعل في منتصفه
        self.fading = True
        self.fade_dir = 1
        self.fade_alpha = 0
        self.fade_action = action
        self.fade_start_ticks = pygame.time.get_ticks()

    def update_fade(self):
        if not self.fading:
            return

        now = pygame.time.get_ticks()
        t = (now - self.fade_start_ticks) / FADE_MS
        if t > 1:
            t = 1

        if self.fade_dir == 1:
            self.fade_alpha = int(255 * t)
            if t >= 1:
                # تنفيذ الإجراء في منتصف التعتيم
                if self.fade_action == "START_LEVEL":
                    self.start(self.level)
                elif self.fade_action == "MENU":
                    self.state = "MENU"

                # نبدأ الرجوع (إزالة التعتيم)
                self.fade_dir = -1
                self.fade_start_ticks = pygame.time.get_ticks()

        else:
            self.fade_alpha = int(255 * (1 - t))
            if t >= 1:
                self.fade_alpha = 0
                self.fading = False

    def handle_card_click(self, pos):
        # منع الضغط إذا اللعبة مقفلة أو ليست في PLAY
        if self.locked or self.state != "PLAY":
            return

        mx, my = pos

        # التأكد أن الضغط داخل منطقة الشبكة
        inside_x = (self.grid_x <= mx < self.grid_x + self.grid_w)
        inside_y = (self.grid_y <= my < self.grid_y + self.grid_h)
        if not (inside_x and inside_y):
            return

        # تحويل مكان الماوس إلى رقم كرت
        col = (mx - self.grid_x) // self.tile_size
        row = (my - self.grid_y) // self.tile_size
        idx = int(row * self.cols + col)

        # إذا الكرت مفتوح أو تم اختيار كرتين
        if self.opened[idx] or len(self.picked) >= 2:
            return

        # فتح الكرت
        self.opened[idx] = True
        self.picked.append(idx)

        if self.flip_sound:
            self.flip_sound.play()

        # إذا اخترنا كرتين نقارنهم
        if len(self.picked) == 2:
            i1 = self.picked[0]
            i2 = self.picked[1]

            if self.card_values[i1] == self.card_values[i2]:
                # تطابق
                self.score += 10

                if self.players_box.players == 2:
                    self.player_scores[self.turn] += 1

                self.picked.clear()

                # إذا كل الكروت مفتوحة => فوز
                if all(self.opened):
                    self.end_game(True)

            else:
                # غير متطابقين
                self.locked = True
                self.shake = 10
                self.hide_timer = (i1, i2, pygame.time.get_ticks() + 700)

                # في لاعبين: غير الدور
                if self.players_box.players == 2:
                    self.turn = 1 - self.turn

    def end_game(self, win):
        # في لاعب واحد: نحسب نتيجة نهائية ونحفظ أعلى نتيجة
        if self.players_box.players == 1:
            final = self.score + max(0, self.time_limit - self.time_elapsed)
            if final > self.high_score:
                self.high_score = final
                save_high_score(final)

        self.state = "WIN" if win else "OVER"

        # إذا فوز وفيه مستوى بعده
        if win and self.level < self.max_level:
            self.level += 1
            self.begin_fade("START_LEVEL")
        elif win and MAX_LEVEL_BEHAVIOR == "MENU":
            self.begin_fade("MENU")

    def update(self):
        # تحديث منطق اللعب
        if self.state == "PLAY":
            self.time_elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000

            # إذا انتهى الوقت نخسر
            if self.time_elapsed >= self.time_limit:
                self.end_game(False)

            # تقليل الاهتزاز تدريجياً
            if self.shake > 0:
                self.shake -= 1

            # إذا وقت إغلاق كرتين الغلط
            if self.hide_timer is not None:
                i1, i2, close_time = self.hide_timer
                if pygame.time.get_ticks() >= close_time:
                    self.opened[i1] = False
                    self.opened[i2] = False
                    self.picked.clear()
                    self.hide_timer = None
                    self.locked = False

        self.update_fade()

    # ---------------- رسم الشاشات ----------------
    def draw(self, surface):
        if self.state == "MENU":
            self.draw_menu(surface)
        elif self.state == "PLAY":
            self.draw_play(surface)
        else:
            self.draw_end(surface, self.state == "WIN")

        self.draw_fade(surface)

    def draw_menu(self, surface):
        draw_text(surface, "MEMORY TILES", FONT_BIG, COLOR_TEAL_DARK, WIDTH // 2, 100, True)

        self.slider.draw(surface)
        self.players_box.draw(surface)

        pygame.draw.rect(surface, COLOR_BORDER, self.start_btn, border_radius=16)
        draw_text(surface, "START", FONT_MED, COLOR_TEAL_DARK,
                  self.start_btn.centerx, self.start_btn.centery, True)

    def draw_play(self, surface):
        # رسم الشريط العلوي
        pygame.draw.rect(surface, COLOR_BG, (0, 0, WIDTH, TOP_MARGIN))
        pygame.draw.rect(surface, COLOR_BORDER, (0, 0, WIDTH, TOP_MARGIN), 5)

        remaining = max(0, self.time_limit - self.time_elapsed)
        draw_text(surface, f"TIME: {remaining}s", FONT_SML,
                  COLOR_ORANGE if remaining < 10 else COLOR_TEAL_DARK, 30, 25)
        draw_text(surface, f"SCORE: {self.score}", FONT_SML, COLOR_TEAL_DARK, 30, 55)
        draw_text(surface, f"LEVEL: {self.level + 1}/{self.max_level + 1}",
                  FONT_SML, COLOR_TEAL_LIGHT, WIDTH - 170, 55)

        if self.players_box.players == 2:
            draw_text(surface, f"P1: {self.player_scores[0]} | P2: {self.player_scores[1]}",
                      FONT_SML, COLOR_TEAL_LIGHT, WIDTH // 2, 25, True)
            draw_text(surface, f"TURN: P{self.turn + 1}", FONT_MED, COLOR_ORANGE, WIDTH // 2, 60, True)
        else:
            draw_text(surface, f"HIGH: {self.high_score}", FONT_SML, COLOR_TEAL_LIGHT, WIDTH - 150, 25)

        draw_text(surface, "M: Menu | R: Restart", FONT_SML, COLOR_TEAL_LIGHT, WIDTH // 2, 90, True)

        # اهتزاز بسيط عند الخطأ
        if self.shake > 0:
            offx = random.randint(-self.shake, self.shake)
            offy = random.randint(-self.shake, self.shake)
        else:
            offx = 0
            offy = 0

        # رسم الشبكة (الكروت)
        total = self.rows * self.cols
        for i in range(total):
            r = i // self.cols
            c = i % self.cols

            x = self.grid_x + c * self.tile_size + offx
            y = self.grid_y + r * self.tile_size + offy

            rect = pygame.Rect(x, y, self.tile_size - 4, self.tile_size - 4)

            # لون الكرت حسب مفتوح/مغلق
            if self.opened[i]:
                pygame.draw.rect(surface, CARD_FRONT_COL, rect, border_radius=10)
                if self.card_images[i]:
                    surface.blit(self.card_images[i], self.card_images[i].get_rect(center=rect.center))
            else:
                pygame.draw.rect(surface, CARD_BACK_COL, rect, border_radius=10)

            pygame.draw.rect(surface, CARD_BORDER_COL, rect, 2, border_radius=10)

    def draw_end(self, surface, win):
        draw_text(surface, "EXCELLENT!" if win else "TIME'S UP!",
                  FONT_BIG, COLOR_TEAL_DARK, WIDTH // 2, 120, True)
        draw_separator(surface, 160)

        box = pygame.Rect(60, 210, 440, 270)
        pygame.draw.rect(surface, COLOR_BORDER, box, border_radius=22)
        inner = box.inflate(-12, -12)
        pygame.draw.rect(surface, CARD_FRONT_COL, inner, border_radius=18)

        if self.players_box.players == 1:
            final = self.score + max(0, self.time_limit - self.time_elapsed)

            draw_text(surface, "YOU EARNED", FONT_MED, COLOR_TEAL_LIGHT, WIDTH // 2, 255, True)
            if self.coin_img:
                surface.blit(self.coin_img, (WIDTH // 2 - 70, 285))
            draw_text(surface, f"{final}", FONT_BIG, COLOR_DARK, WIDTH // 2 + 20, 305, True)
            draw_text(surface, f"HIGH SCORE: {self.high_score}", FONT_SML, COLOR_TEAL_LIGHT, WIDTH // 2, 380, True)

        else:
            p1 = self.player_scores[0]
            p2 = self.player_scores[1]
            if p1 > p2:
                result = "P1 WINS!"
            elif p2 > p1:
                result = "P2 WINS!"
            else:
                result = "DRAW!"

            draw_text(surface, f"P1: {p1}  |  P2: {p2}", FONT_MED, COLOR_TEAL_DARK, WIDTH // 2, 300, True)
            draw_text(surface, result, FONT_BIG, COLOR_ORANGE, WIDTH // 2, 380, True)

        # أزرار menu و retry
        if self.home_img:
            surface.blit(self.home_img, self.home_rect)
        if self.restart_img:
            surface.blit(self.restart_img, self.restart_rect)

        draw_text(surface, "MENU", FONT_SML, COLOR_TEAL_DARK, self.home_rect.centerx, self.home_rect.bottom + 15, True)
        draw_text(surface, "RETRY", FONT_SML, COLOR_TEAL_DARK, self.restart_rect.centerx, self.restart_rect.bottom + 15, True)

    def draw_fade(self, surface):
        if self.fade_alpha <= 0:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(self.fade_alpha)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

# ================ 9) الحلقة الرئيسية (Main Loop)=================

def main():
    try_play_music()

    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        screen.fill(COLOR_BG)

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                try:
                    pygame.mixer.music.stop()
                except:
                    pass
                running = False

            # في القائمة
            if game.state == "MENU":
                game.slider.handle_event(e)
                game.players_box.handle_event(e)

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if game.start_btn.collidepoint(e.pos):
                        game.start(game.slider.index)

            # أثناء اللعب
            elif game.state == "PLAY":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    game.handle_card_click(e.pos)

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_m:
                        game.state = "MENU"
                    if e.key == pygame.K_r:
                        game.start(game.level)

            # شاشة النهاية
            else:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if game.home_rect.collidepoint(e.pos):
                        game.state = "MENU"
                    if game.restart_rect.collidepoint(e.pos):
                        game.start(game.level)

        # تحديث اللعبة ورسمها
        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
