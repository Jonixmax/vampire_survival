"""
Mini Vampire Survivors  -  versión 2
------------------------------------
Sobrevive el mayor tiempo posible. Tu personaje dispara solo al enemigo más
cercano; tú te encargas de moverte, recoger gemas y elegir mejoras.

Versión 4: clases de personaje (Guerrero, Tanque, Mago) con pantalla de selección.
Versión 3: optimizada para correr a un máximo de 30 FPS (tecla F muestra los FPS).

Novedades de la versión 2:
    - Terreno infinito generado proceduralmente (cámara que sigue al jugador)
    - 4 tipos de enemigos con comportamientos distintos
    - 3 armas nuevas: cuchillas orbitales, aura y rayo (hasta nivel 5)
    - Sonido generado por código (sin archivos externos)

Controles:
    1, 2, 3 .......... elegir clase en el menú inicial
    WASD / flechas ... mover
    1, 2, 3 .......... elegir mejora al subir de nivel (o clic con el mouse)
    M ................ silenciar / activar sonido
    - / + ............ bajar / subir el volumen general
    F ................ mostrar / ocultar contador de FPS
    R ................ volver al menú de clases tras morir
    ESC .............. salir
"""
import array
import math
import random
import sys

import pygame

# --------------------------------------------------------------------------
# Configuración general (cambiar aquí es la forma más fácil de ajustar el juego)
# --------------------------------------------------------------------------
WIDTH, HEIGHT = 960, 640
FPS = 30                      # tope de cuadros por segundo (todo el movimiento usa dt, así que la velocidad no cambia)

COLOR_PLAYER = (90, 200, 255)
COLOR_PROJECTILE = (255, 230, 120)
COLOR_GEM = (110, 255, 170)
COLOR_GEM_BIG = (120, 170, 255)
COLOR_TEXT = (235, 235, 245)
COLOR_HP = (220, 60, 70)
COLOR_XP = (110, 255, 170)

PLAYER_RADIUS = 14
PROJECTILE_RADIUS = 5
GEM_RADIUS = 5
MAX_ENEMIES = 220
MAX_WEAPON_LEVEL = 5
GRID_CELL = 64                # tamaño de celda de la cuadrícula espacial de colisiones


def dist2(a, b):
    """Distancia al cuadrado entre dos puntos. Evita la raíz cuadrada, que es más lenta."""
    dx, dy = a.x - b.x, a.y - b.y
    return dx * dx + dy * dy


def seg_dist2(p, a, b):
    """Distancia al cuadrado del punto p al segmento a-b (para colisiones 'barridas')."""
    abx, aby = b.x - a.x, b.y - a.y
    length2 = abx * abx + aby * aby
    if length2 == 0:
        return dist2(p, a)
    t = max(0.0, min(1.0, ((p.x - a.x) * abx + (p.y - a.y) * aby) / length2))
    dx, dy = p.x - (a.x + abx * t), p.y - (a.y + aby * t)
    return dx * dx + dy * dy


# ==========================================================================
# TERRENO PROCEDURAL
# El mundo se divide en "chunks" de 512x512 px. Cada chunk se dibuja solo
# cuando aparece en pantalla, a partir de una semilla: la misma semilla y las
# mismas coordenadas siempre producen el mismo paisaje (sin guardar nada).
# ==========================================================================
CHUNK = 512
TILE = 64

DIRT = (86, 72, 58)
GRASS = (44, 76, 50)
GRASS_LIGHT = (58, 92, 56)
FOREST = (28, 52, 42)


def hash01(ix, iy, seed):
    """Número pseudoaleatorio estable entre 0 y 1 para una coordenada entera."""
    h = ((ix * 73856093) ^ (iy * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def value_noise(x, y, seed, scale):
    """Ruido suave: interpola entre valores aleatorios de una cuadrícula."""
    fx, fy = x / scale, y / scale
    ix, iy = math.floor(fx), math.floor(fy)
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)   # suavizado
    a = hash01(ix, iy, seed)
    b = hash01(ix + 1, iy, seed)
    c = hash01(ix, iy + 1, seed)
    d = hash01(ix + 1, iy + 1, seed)
    return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def biome_color(n):
    """Convierte un valor de ruido (0..1) en color: tierra -> pasto -> bosque."""
    if n < 0.35:
        return lerp_color(DIRT, GRASS, n / 0.35)
    if n < 0.65:
        return lerp_color(GRASS, GRASS_LIGHT, (n - 0.35) / 0.30)
    return lerp_color(GRASS_LIGHT, FOREST, (n - 0.65) / 0.35)


class Terrain:
    def __init__(self, seed):
        self.seed = seed
        self.chunks = {}

    def build_chunk(self, cx, cy):
        surf = pygame.Surface((CHUNK, CHUNK))
        base_x, base_y = cx * CHUNK, cy * CHUNK

        # 1) Suelo: un color por baldosa según el ruido del bioma
        for ty in range(CHUNK // TILE):
            for tx in range(CHUNK // TILE):
                wx = base_x + tx * TILE + TILE / 2
                wy = base_y + ty * TILE + TILE / 2
                n = value_noise(wx, wy, self.seed, 700)
                detail = (value_noise(wx, wy, self.seed + 7, 120) - 0.5) * 14
                color = tuple(max(0, min(255, int(c + detail))) for c in biome_color(n))
                surf.fill(color, (tx * TILE, ty * TILE, TILE, TILE))

        # 2) Decoración aleatoria (determinista por chunk)
        rng = random.Random((self.seed * 1000003) ^ (cx * 73856093) ^ (cy * 19349663))
        for _ in range(12 + rng.randrange(10)):
            lx = rng.randint(40, CHUNK - 40)
            ly = rng.randint(40, CHUNK - 40)
            n = value_noise(base_x + lx, base_y + ly, self.seed, 700)
            roll = rng.random()
            if n > 0.62 and roll < 0.55:
                self.draw_tree(surf, lx, ly, rng)
            elif n < 0.40 and roll < 0.55:
                self.draw_rock(surf, lx, ly, rng)
            elif roll < 0.75:
                self.draw_tuft(surf, lx, ly, rng)
            else:
                self.draw_bush(surf, lx, ly, rng)
        return surf.convert()

    @staticmethod
    def draw_tuft(surf, x, y, rng):
        for dx in (-4, 0, 4):
            h = rng.randint(5, 10)
            pygame.draw.line(surf, (74, 120, 66), (x + dx, y), (x + dx + rng.randint(-2, 2), y - h), 2)

    @staticmethod
    def draw_rock(surf, x, y, rng):
        w, h = rng.randint(14, 30), rng.randint(10, 20)
        pygame.draw.ellipse(surf, (40, 38, 44), (x - w // 2 + 3, y - h // 2 + 4, w, h))   # sombra
        pygame.draw.ellipse(surf, (112, 110, 118), (x - w // 2, y - h // 2, w, h))
        pygame.draw.ellipse(surf, (150, 148, 156), (x - w // 4, y - h // 2 + 2, w // 2, h // 3))

    @staticmethod
    def draw_bush(surf, x, y, rng):
        r = rng.randint(9, 15)
        for ox, oy in ((-r // 2, 0), (r // 2, 0), (0, -r // 2)):
            pygame.draw.circle(surf, (30, 70, 44), (x + ox, y + oy), r)
        pygame.draw.circle(surf, (48, 100, 58), (x - 2, y - r // 2 - 2), r // 2)

    @staticmethod
    def draw_tree(surf, x, y, rng):
        r = rng.randint(22, 34)
        pygame.draw.ellipse(surf, (14, 30, 24), (x - r, y + r // 2, r * 2, r))               # sombra
        pygame.draw.rect(surf, (74, 54, 38), (x - 5, y - 4, 10, r))                           # tronco
        pygame.draw.circle(surf, (24, 62, 44), (x, y - r // 2), r)                            # copa
        pygame.draw.circle(surf, (36, 86, 56), (x - r // 4, y - r // 2 - r // 4), r // 2)     # brillo

    def draw(self, screen, cam):
        cx0, cy0 = math.floor(cam.x / CHUNK), math.floor(cam.y / CHUNK)
        cx1, cy1 = math.floor((cam.x + WIDTH) / CHUNK), math.floor((cam.y + HEIGHT) / CHUNK)
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                if (cx, cy) not in self.chunks:
                    self.chunks[(cx, cy)] = self.build_chunk(cx, cy)
                screen.blit(self.chunks[(cx, cy)], (cx * CHUNK - int(cam.x), cy * CHUNK - int(cam.y)))
        # Liberar memoria: olvidar chunks lejanos (se regeneran idénticos si se vuelve)
        if len(self.chunks) > 30:
            mid_x, mid_y = (cx0 + cx1) / 2, (cy0 + cy1) / 2
            for key in [k for k in self.chunks if abs(k[0] - mid_x) > 3 or abs(k[1] - mid_y) > 3]:
                del self.chunks[key]


# ==========================================================================
# SONIDO (sintetizado por código: no se necesitan archivos de audio)
# ==========================================================================
RATE = 22050


def make_tone(f_start, f_end, dur, vol=0.4, wave="square", decay=1.6, cutoff=1800):
    """Genera un efecto: una onda cuya frecuencia se desliza de f_start a f_end.

    Para que no suene áspero:
      - cutoff: filtro paso-bajo que recorta los agudos (las ondas cuadrada y de
        sierra son ricas en armónicos agudos, que es lo que suena "duro").
      - ataque: sube el volumen en 4 ms en lugar de empezar de golpe (evita el "clic").
    """
    n = int(RATE * dur)
    samples = array.array("h")
    phase = 0.0
    smooth = 0.0
    alpha = 1 - math.exp(-2 * math.pi * cutoff / RATE)    # coeficiente del filtro de 1 polo
    attack = max(1, int(RATE * 0.004))
    for i in range(n):
        t = i / n
        freq = f_start + (f_end - f_start) * t
        phase += freq / RATE
        frac = phase % 1.0
        if wave == "square":
            v = 1.0 if frac < 0.5 else -1.0
        elif wave == "saw":
            v = 2 * frac - 1
        elif wave == "noise":
            v = random.uniform(-1, 1)
        else:
            v = math.sin(2 * math.pi * phase)
        if wave != "sine":
            smooth += alpha * (v - smooth)                # suaviza los agudos
            v = smooth
        env = ((1 - t) ** decay) * min(1.0, i / attack)
        samples.append(int(v * vol * env * 32767))
    return samples


def make_music():
    """Un arpegio oscuro en La menor que se repite en bucle."""
    notes = [110, 131, 165, 220, 165, 131, 123, 147, 185, 247, 185, 147]
    samples = array.array("h")
    for f in notes:
        samples.extend(make_tone(f, f, 0.24, vol=0.7, wave="saw", decay=2.2, cutoff=500))
    return samples


class Audio:
    # Tiempo mínimo entre repeticiones, para que muchos golpes no saturen el audio
    GAPS = {"hit": 0.05, "kill": 0.06, "gem": 0.05, "shoot": 0.08}

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.master = 0.5             # volumen general (0.0 a 1.0); se cambia con las teclas - y +
        self.sounds = {}
        self.last = {}
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
        except (pygame.error, NotImplementedError):
            print("Aviso: no se pudo iniciar el audio. El juego seguirá sin sonido.")
            return
        self.enabled = True
        defs = {
            "shoot": (900, 500, 0.07, 0.18, "square"),
            "hit": (220, 120, 0.05, 0.25, "noise"),
            "kill": (300, 80, 0.12, 0.30, "saw"),
            "gem": (700, 1300, 0.08, 0.20, "sine"),
            "hurt": (180, 60, 0.25, 0.45, "saw"),
            "zap": (1600, 200, 0.18, 0.35, "saw"),
            "levelup": (400, 1000, 0.45, 0.35, "square"),
            "gameover": (300, 40, 1.0, 0.45, "saw"),
        }
        for name, (f1, f2, dur, vol, wave) in defs.items():
            self.sounds[name] = pygame.mixer.Sound(buffer=make_tone(f1, f2, dur, vol, wave).tobytes())
        self.music = pygame.mixer.Sound(buffer=make_music().tobytes())
        self.music.play(loops=-1)
        self.apply_volume()

    def play(self, name):
        if not self.enabled or self.muted:
            return
        now = pygame.time.get_ticks() / 1000.0
        if now - self.last.get(name, -1) < self.GAPS.get(name, 0):
            return
        self.last[name] = now
        self.sounds[name].play()

    def toggle_mute(self):
        if not self.enabled:
            return
        self.muted = not self.muted
        self.apply_volume()

    MUSIC_BASE = 0.35             # la música suena más baja que los efectos

    def apply_volume(self):
        """Aplica el volumen general a todos los sonidos."""
        for snd in self.sounds.values():
            snd.set_volume(self.master)
        self.music.set_volume(0.0 if self.muted else self.MUSIC_BASE * self.master)

    def change_volume(self, delta):
        if not self.enabled:
            return
        self.master = max(0.0, min(1.0, round(self.master + delta, 2)))
        self.apply_volume()


# ==========================================================================
# ARMAS Y MEJORAS
# ==========================================================================
WEAPONS = {
    "cuchillas": ("Cuchillas orbitales", "Cuchillas giran a tu alrededor", "Más cuchillas y más rápidas"),
    "aura": ("Aura ardiente", "Daña a los enemigos cercanos", "Aura más grande y más fuerte"),
    "rayo": ("Rayo", "Rayos caen sobre enemigos", "Más rayos y más daño"),
}


def _mul(attr, factor):
    def apply(p):
        setattr(p, attr, getattr(p, attr) * factor)
    return apply


def _add_projectile(p):
    p.projectile_count += 1


def _heal(p):
    p.hp = min(p.max_hp, p.hp + p.max_hp * 0.4)


def _more_hp(p):
    p.max_hp += 20
    p.hp += 20


# Mejoras generales (siempre disponibles): (nombre, descripción, función)
GENERIC_UPGRADES = [
    ("Daño +25%", "Todas tus armas golpean más fuerte", _mul("damage", 1.25)),
    ("Cadencia +20%", "Proyectiles y rayos más frecuentes", _mul("fire_rate", 1.20)),
    ("Proyectil extra", "Un proyectil más por disparo", _add_projectile),
    ("Velocidad +10%", "Te mueves más rápido", _mul("speed", 1.10)),
    ("Imán +40%", "Recoges gemas desde más lejos", _mul("pickup_radius", 1.40)),
    ("Curación", "Recuperas 40% de tu vida", _heal),
    ("Vida máx. +20", "Más vida máxima", _more_hp),
]


# ==========================================================================
# CLASES DE PERSONAJE
# Cada clase cambia las estadísticas iniciales, el arma con la que empiezas y
# tiene una pasiva. armor es un multiplicador del daño recibido (0.75 = -25%).
# ==========================================================================
CLASSES = {
    "guerrero": dict(
        name="Guerrero", color=(240, 190, 80),
        desc="Equilibrado, lucha cuerpo a cuerpo.",
        hp=120, speed=225, damage=1.15, fire_rate=1.0, pickup=70, armor=1.0, regen=0.0, xp_mult=1.0,
        weapon="cuchillas", passive="Daño +15%"),
    "tanque": dict(
        name="Tanque", color=(110, 150, 230),
        desc="Lento pero casi imposible de derribar.",
        hp=220, speed=185, damage=0.9, fire_rate=1.0, pickup=70, armor=0.75, regen=0.8, xp_mult=1.0,
        weapon="aura", passive="Armadura y regeneración"),
    "mago": dict(
        name="Mago", color=(175, 110, 240),
        desc="Frágil y veloz: gana poder muy rápido.",
        hp=75, speed=235, damage=1.0, fire_rate=1.3, pickup=110, armor=1.0, regen=0.0, xp_mult=1.2,
        weapon="rayo", passive="+20% XP, cadencia +30%"),
}
CLASS_ORDER = ["guerrero", "tanque", "mago"]


# ==========================================================================
# ENTIDADES
# ==========================================================================
class Player:
    def __init__(self, class_key="guerrero"):
        c = CLASSES[class_key]
        self.class_key = class_key
        self.pos = pygame.Vector2(0, 0)        # el mundo es infinito: se empieza en el origen
        self.speed = float(c["speed"])
        self.max_hp = float(c["hp"])
        self.hp = float(c["hp"])
        self.damage = c["damage"]              # multiplicador de daño de TODAS las armas
        self.fire_rate = c["fire_rate"]        # multiplicador de cadencia
        self.armor = c["armor"]                # multiplicador del daño recibido
        self.regen = c["regen"]                # vida recuperada por segundo
        self.xp_mult = c["xp_mult"]            # multiplicador de experiencia ganada
        self.projectile_count = 1
        self.pickup_radius = float(c["pickup"])
        self.level = 1
        self.xp = 0
        self.xp_to_next = 5
        self.shoot_timer = 0.0
        self.invulnerable = 0.0
        self.weapons = {c["weapon"]: 1}        # cada clase empieza con un arma distinta

    def move(self, keys, dt):
        direction = pygame.Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if direction.length_squared() > 0:
            direction = direction.normalize()   # evita ir más rápido en diagonal
        self.pos += direction * self.speed * dt

    def add_xp(self, amount):
        """Suma experiencia. Devuelve True si se subió de nivel."""
        self.xp += amount * self.xp_mult
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.35) + 2
            return True
        return False


# Tipos de enemigo. speed = rango; hp y hp_scale = vida base y extra por minuto.
ENEMY_TYPES = {
    "murcielago": dict(radius=8, speed=(150, 175), hp=8, hp_scale=6, dmg=6, gem=1, color=(170, 90, 220)),
    "zombi": dict(radius=12, speed=(55, 80), hp=20, hp_scale=18, dmg=10, gem=1, color=(210, 70, 90)),
    "bruto": dict(radius=21, speed=(38, 50), hp=90, hp_scale=60, dmg=18, gem=5, color=(230, 130, 50)),
    "espectro": dict(radius=11, speed=(85, 105), hp=28, hp_scale=20, dmg=12, gem=2, color=(120, 230, 240)),
}


class Enemy:
    def __init__(self, kind, pos, minutes):
        info = ENEMY_TYPES[kind]
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.radius = info["radius"]
        self.speed = random.uniform(*info["speed"]) + minutes * 8
        self.hp = info["hp"] + minutes * info["hp_scale"]
        self.dmg = info["dmg"]
        self.gem = info["gem"]
        self.color = info["color"]
        self.phase = random.uniform(0, 6.28)
        self.blade_cd = 0.0        # evita que una cuchilla golpee en cada frame

    def update(self, target, dt, t):
        direction = target - self.pos
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        if self.kind == "espectro":
            # Avanza en zigzag: suma un desplazamiento lateral que oscila con el tiempo
            perp = pygame.Vector2(-direction.y, direction.x)
            direction = (direction + perp * 0.9 * math.sin(t * 3 + self.phase)).normalize()
        self.pos += direction * self.speed * dt
        self.blade_cd = max(0.0, self.blade_cd - dt)


class Projectile:
    SPEED = 450.0
    LIFETIME = 1.3

    def __init__(self, pos, direction, damage):
        self.pos = pygame.Vector2(pos)
        self.prev = pygame.Vector2(pos)     # posición del frame anterior (colisión barrida)
        self.vel = direction.normalize() * self.SPEED
        self.damage = damage
        self.life = self.LIFETIME

    def update(self, dt):
        self.prev = self.pos.copy()
        self.pos += self.vel * dt
        self.life -= dt


class Gem:
    def __init__(self, pos, value=1):
        self.pos = pygame.Vector2(pos)
        self.value = value
        self.attracted = False


# ==========================================================================
# LÓGICA PRINCIPAL DEL JUEGO
# ==========================================================================
class Game:
    def __init__(self, audio):
        self.audio = audio
        self.font = pygame.font.SysFont(None, 26)
        self.font_big = pygame.font.SysFont(None, 56)
        self.font_small = pygame.font.SysFont(None, 23)
        self.text_cache = {}      # texto ya renderizado (renderizar fuentes cada frame es caro)
        self.aura_cache = {}
        self.overlay_cache = {}
        self.show_fps = False
        self.fps = 0.0
        self.reset()
        self.state = "menu"            # el juego empieza en la selección de clase

    def reset(self, class_key="guerrero"):
        self.player = Player(class_key)
        self.terrain = Terrain(random.randrange(1 << 30))   # ¡mundo nuevo en cada partida!
        self.enemies = []
        self.projectiles = []
        self.gems = []
        self.zaps = []                  # efectos visuales de rayos: [inicio, fin, tiempo]
        self.time = 0.0
        self.kills = 0
        self.spawn_timer = 0.0
        self.blade_angle = 0.0
        self.blade_positions = []
        self.aura_timer = 0.0
        self.zap_timer = 1.0
        self.state = "playing"          # "playing" | "levelup" | "gameover"
        self.choices = []

    def start(self, index):
        """Empieza una partida nueva con la clase elegida en el menú."""
        self.reset(CLASS_ORDER[index])
        self.state = "playing"
        self.audio.play("levelup")

    def to_menu(self):
        self.reset()
        self.state = "menu"

    @property
    def cam(self):
        """Esquina superior izquierda de la vista (la cámara sigue al jugador)."""
        return pygame.Vector2(self.player.pos.x - WIDTH / 2, self.player.pos.y - HEIGHT / 2)

    # ---------------------------- Spawns ----------------------------------
    def pick_enemy_kind(self):
        """Elige el tipo de enemigo según el tiempo transcurrido."""
        t = self.time
        weights = {
            "zombi": 4.0,
            "murcielago": 0.5 if t < 20 else 1.5,
            "bruto": 0.0 if t < 60 else min(1.5, (t - 60) / 60),
            "espectro": 0.0 if t < 100 else min(1.5, (t - 100) / 80),
        }
        kinds = list(weights)
        return random.choices(kinds, weights=[weights[k] for k in kinds])[0]

    def spawn_enemy(self):
        """Aparece en un anillo justo fuera de la pantalla, alrededor del jugador."""
        if len(self.enemies) >= MAX_ENEMIES:
            return
        angle = random.uniform(0, math.tau)
        dist = math.hypot(WIDTH, HEIGHT) / 2 + 40
        pos = self.player.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * dist
        self.enemies.append(Enemy(self.pick_enemy_kind(), pos, self.time / 60))

    # ---------------------------- Update ----------------------------------
    def update(self, dt, keys):
        if self.state != "playing":
            return

        p = self.player
        self.time += dt
        p.move(keys, dt)
        p.invulnerable = max(0.0, p.invulnerable - dt)
        p.hp = min(p.max_hp, p.hp + p.regen * dt)     # regeneración (solo el Tanque)

        self.spawn_timer -= dt
        interval = max(0.25, 1.0 - self.time * 0.008)
        while self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer += interval

        self.auto_shoot(dt)
        self.update_weapons(dt)

        for e in self.enemies:
            e.update(p.pos, dt, self.time)
        for pr in self.projectiles:
            pr.update(dt)
        for z in self.zaps:
            z[2] -= dt

        self.handle_collisions()
        self.collect_gems(dt)

        self.projectiles = [pr for pr in self.projectiles if pr.life > 0]
        self.zaps = [z for z in self.zaps if z[2] > 0]
        # Enemigos que quedaron muy lejos se descartan (el spawn los repone cerca)
        self.enemies = [e for e in self.enemies if dist2(e.pos, p.pos) < 1400 ** 2]

        if p.hp <= 0:
            self.state = "gameover"
            self.audio.play("gameover")

    def auto_shoot(self, dt):
        """Arma base: dispara al enemigo más cercano."""
        p = self.player
        p.shoot_timer -= dt
        if p.shoot_timer > 0 or not self.enemies:
            return
        p.shoot_timer = 1.0 / (1.5 * p.fire_rate)

        nearest = min(self.enemies, key=lambda e: (e.pos - p.pos).length_squared())
        base = nearest.pos - p.pos
        if base.length_squared() == 0:
            return
        base_angle = math.atan2(base.y, base.x)

        spread = math.radians(12)
        n = p.projectile_count
        for i in range(n):
            angle = base_angle + (i - (n - 1) / 2) * spread
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            self.projectiles.append(Projectile(p.pos, direction, 12 * p.damage))
        self.audio.play("shoot")

    def update_weapons(self, dt):
        """Cuchillas orbitales, aura ardiente y rayo."""
        p = self.player
        lv = p.weapons

        if "cuchillas" in lv:
            level = lv["cuchillas"]
            count = 1 + level
            self.blade_angle += (3.0 + 0.4 * level) * dt
            self.blade_positions = []
            for i in range(count):
                a = self.blade_angle + math.tau * i / count
                pos = p.pos + pygame.Vector2(math.cos(a), math.sin(a)) * 90
                self.blade_positions.append(pos)
                for e in self.enemies:
                    if e.blade_cd <= 0 and dist2(e.pos, pos) < (e.radius + 10) ** 2:
                        e.hp -= (10 + 2 * level) * p.damage
                        e.blade_cd = 0.35
                        self.audio.play("hit")
        else:
            self.blade_positions = []

        if "aura" in lv:
            level = lv["aura"]
            self.aura_timer -= dt
            if self.aura_timer <= 0:
                self.aura_timer = 0.5
                radius = self.aura_radius()
                for e in self.enemies:
                    if dist2(e.pos, p.pos) < (radius + e.radius) ** 2:
                        e.hp -= (4 + 3 * level) * p.damage

        if "rayo" in lv:
            level = lv["rayo"]
            self.zap_timer -= dt
            if self.zap_timer <= 0:
                self.zap_timer = 2.4 / p.fire_rate
                near = [e for e in self.enemies if (e.pos - p.pos).length_squared() < 450 ** 2]
                for e in random.sample(near, min(level, len(near))):
                    e.hp -= (28 + 8 * level) * p.damage
                    self.zaps.append([e.pos + pygame.Vector2(random.randint(-20, 20), -320), pygame.Vector2(e.pos), 0.18])
                if near:
                    self.audio.play("zap")

    def aura_radius(self):
        return 55 + 15 * self.player.weapons.get("aura", 0)

    def handle_collisions(self):
        p = self.player

        # Cuadrícula espacial: cada enemigo se guarda en su celda, así un proyectil
        # solo se compara con los enemigos cercanos (no con los ~200 a la vez).
        grid = {}
        for e in self.enemies:
            grid.setdefault((int(e.pos.x // GRID_CELL), int(e.pos.y // GRID_CELL)), []).append(e)

        # Proyectil vs enemigo. Se revisa el SEGMENTO recorrido en el frame (prev -> pos),
        # no solo el punto final: a 30 FPS un proyectil avanza ~15 px por frame y de otro
        # modo podría atravesar a un enemigo pequeño sin detectarlo.
        for pr in self.projectiles:
            mx, my = (pr.pos.x + pr.prev.x) / 2, (pr.pos.y + pr.prev.y) / 2
            cx, cy = int(mx // GRID_CELL), int(my // GRID_CELL)
            hit = None
            for gx in (cx - 1, cx, cx + 1):
                for gy in (cy - 1, cy, cy + 1):
                    for e in grid.get((gx, gy), ()):
                        if seg_dist2(e.pos, pr.prev, pr.pos) < (e.radius + PROJECTILE_RADIUS) ** 2:
                            hit = e
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                hit.hp -= pr.damage
                pr.life = 0
                self.audio.play("hit")

        # Enemigos muertos sueltan una gema (los más fuertes, una más valiosa)
        alive = []
        for e in self.enemies:
            if e.hp <= 0:
                self.kills += 1
                self.gems.append(Gem(e.pos, e.gem))
                self.audio.play("kill")
            else:
                alive.append(e)
        self.enemies = alive

        # Enemigo vs jugador (con ventana de invulnerabilidad)
        if p.invulnerable <= 0:
            for e in self.enemies:
                if dist2(e.pos, p.pos) < (e.radius + PLAYER_RADIUS) ** 2:
                    p.hp -= e.dmg * p.armor
                    p.invulnerable = 0.5
                    self.audio.play("hurt")
                    break

    def collect_gems(self, dt):
        p = self.player
        remaining = []
        pickup2 = p.pickup_radius ** 2
        touch2 = (PLAYER_RADIUS + GEM_RADIUS) ** 2
        for g in self.gems:
            d2 = dist2(g.pos, p.pos)
            if d2 < pickup2:
                g.attracted = True
            if g.attracted and d2 > 0:
                g.pos += (p.pos - g.pos).normalize() * 380 * dt
            if d2 < touch2:
                self.audio.play("gem")
                if p.add_xp(g.value):
                    self.open_level_up()
            else:
                remaining.append(g)
        self.gems = remaining

    # ------------------------- Subida de nivel -----------------------------
    def build_choices(self):
        """Arma la lista de mejoras posibles: generales + armas nuevas/mejoras de armas."""
        p = self.player
        options = list(GENERIC_UPGRADES)
        for key, (name, desc, up_desc) in WEAPONS.items():
            level = p.weapons.get(key, 0)
            if level == 0:
                options.append((f"Nueva arma: {name}", desc, lambda pl, k=key: pl.weapons.__setitem__(k, 1)))
            elif level < MAX_WEAPON_LEVEL:
                options.append((f"{name} (nivel {level + 1})", up_desc,
                                lambda pl, k=key: pl.weapons.__setitem__(k, pl.weapons[k] + 1)))
        return options

    def open_level_up(self):
        self.state = "levelup"
        self.choices = random.sample(self.build_choices(), 3)
        self.audio.play("levelup")

    def choose_upgrade(self, index):
        if self.state == "levelup" and 0 <= index < len(self.choices):
            self.choices[index][2](self.player)
            self.state = "playing"

    # ---------------------------- Dibujo ----------------------------------
    def text(self, surface, msg, pos, font=None, color=COLOR_TEXT, center=False):
        font = font or self.font
        key = (msg, id(font), color)
        img = self.text_cache.get(key)
        if img is None:
            if len(self.text_cache) > 300:
                self.text_cache.clear()
            img = self.text_cache[key] = font.render(msg, True, color)
        rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        surface.blit(img, rect)

    def overlay(self, alpha):
        """Capa oscura semitransparente (se crea una sola vez por nivel de opacidad)."""
        if alpha not in self.overlay_cache:
            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            surf.fill((0, 0, 0, alpha))
            self.overlay_cache[alpha] = surf
        return self.overlay_cache[alpha]

    def aura_surface(self, r):
        if r not in self.aura_cache:
            aura = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (255, 120, 40, 60), (r, r), r)
            pygame.draw.circle(aura, (255, 170, 60, 140), (r, r), r, 3)
            self.aura_cache[r] = aura
        return self.aura_cache[r]

    def draw(self, screen):
        cam = self.cam
        p = self.player
        self.terrain.draw(screen, cam)
        if self.state == "menu":
            screen.blit(self.overlay(150), (0, 0))
            self.draw_menu(screen)
            return

        def sp(pos):
            return (int(pos.x - cam.x), int(pos.y - cam.y))

        # Aura (un círculo semitransparente alrededor del jugador)
        if "aura" in p.weapons:
            r = int(self.aura_radius())
            screen.blit(self.aura_surface(r), (sp(p.pos)[0] - r, sp(p.pos)[1] - r))

        for g in self.gems:
            big = g.value > 1
            pygame.draw.circle(screen, COLOR_GEM_BIG if big else COLOR_GEM, sp(g.pos), GEM_RADIUS + (3 if big else 0))
        for e in self.enemies:
            self.draw_enemy(screen, e, sp(e.pos))
        for pr in self.projectiles:
            pygame.draw.circle(screen, COLOR_PROJECTILE, sp(pr.pos), PROJECTILE_RADIUS)
        for bp in self.blade_positions:
            x, y = sp(bp)
            pygame.draw.polygon(screen, (220, 225, 240), [(x, y - 11), (x + 6, y), (x, y + 11), (x - 6, y)])
            pygame.draw.polygon(screen, (120, 130, 160), [(x, y - 11), (x + 6, y), (x, y + 11), (x - 6, y)], 2)
        for start, end, _ in self.zaps:
            pygame.draw.line(screen, (255, 255, 200), sp(start), sp(end), 5)
            pygame.draw.line(screen, (120, 190, 255), sp(start), sp(end), 2)

        # Jugador (parpadea mientras es invulnerable)
        if p.invulnerable <= 0 or int(p.invulnerable * 20) % 2 == 0:
            self.draw_player(screen, p.class_key, (WIDTH // 2, HEIGHT // 2))

        self.draw_hud(screen)
        if self.state == "levelup":
            self.draw_level_up(screen)
        elif self.state == "gameover":
            self.draw_game_over(screen)

    @staticmethod
    def draw_player(screen, class_key, pos, scale=1.0):
        """Dibuja al personaje: un círculo de color con un detalle propio de cada clase."""
        x, y = pos
        r = int(PLAYER_RADIUS * scale)
        color = CLASSES[class_key]["color"]
        pygame.draw.circle(screen, (20, 25, 40), pos, r + 2)
        pygame.draw.circle(screen, color, pos, r)
        k = scale
        if class_key == "guerrero":      # espada
            pygame.draw.line(screen, (225, 228, 240), (x + 8 * k, y + 9 * k), (x + 22 * k, y - 11 * k), max(2, int(3 * k)))
            pygame.draw.line(screen, (120, 80, 40), (x + 5 * k, y + 5 * k), (x + 12 * k, y + 12 * k), max(2, int(3 * k)))
        elif class_key == "tanque":      # escudo
            shield = pygame.Rect(0, 0, 13 * k, 20 * k)
            shield.center = (x - 15 * k, y)
            pygame.draw.rect(screen, (190, 200, 225), shield, border_radius=4)
            pygame.draw.rect(screen, (70, 90, 140), shield, 2, border_radius=4)
        else:                            # mago: sombrero y bastón
            pygame.draw.polygon(screen, (90, 50, 150), [(x - 11 * k, y - 7 * k), (x + 11 * k, y - 7 * k), (x, y - 28 * k)])
            pygame.draw.line(screen, (150, 110, 60), (x + 14 * k, y + 12 * k), (x + 14 * k, y - 16 * k), max(2, int(3 * k)))
            pygame.draw.circle(screen, (255, 240, 150), (int(x + 14 * k), int(y - 18 * k)), max(2, int(4 * k)))

    @staticmethod
    def class_card_rect(i):
        w, h, gap = 290, 330, 20
        total = 3 * w + 2 * gap
        return pygame.Rect((WIDTH - total) / 2 + i * (w + gap), 175, w, h)

    def draw_menu(self, screen):
        self.text(screen, "Elige tu clase", (WIDTH / 2, 90), self.font_big, center=True)
        self.text(screen, "Pulsa 1, 2 o 3  (o haz clic en una tarjeta)", (WIDTH / 2, 135), color=(170, 170, 190), center=True)
        mouse = pygame.mouse.get_pos()
        for i, key in enumerate(CLASS_ORDER):
            c = CLASSES[key]
            rect = self.class_card_rect(i)
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(screen, (50, 50, 85) if hover else (36, 36, 64), rect, border_radius=12)
            pygame.draw.rect(screen, c["color"], rect, 3 if hover else 2, border_radius=12)
            self.text(screen, f"[{i + 1}] {c['name']}", (rect.centerx, rect.y + 28), center=True, color=c["color"])
            self.draw_player(screen, key, (rect.centerx, rect.y + 90), scale=1.8)
            self.text(screen, c["desc"], (rect.centerx, rect.y + 150), self.font_small, color=(190, 190, 210), center=True)
            lines = [
                f"Vida: {c['hp']}",
                f"Velocidad: {c['speed']}",
                f"Daño: x{c['damage']:.2f}",
                f"Arma inicial: {WEAPONS[c['weapon']][0]}",
                f"Pasiva: {c['passive']}",
            ]
            for j, line in enumerate(lines):
                self.text(screen, line, (rect.x + 16, rect.y + 185 + j * 26), self.font_small)

    def draw_enemy(self, screen, e, pos):
        x, y = pos
        if x < -40 or x > WIDTH + 40 or y < -40 or y > HEIGHT + 40:
            return   # fuera de pantalla: no se dibuja
        r = e.radius
        dark = tuple(c // 2 for c in e.color)
        if e.kind == "murcielago":
            flap = 6 * math.sin(self.time * 22 + e.phase)
            pygame.draw.polygon(screen, dark, [(x - 3, y), (x - 15, y - 7 + flap), (x - 10, y + 4)])
            pygame.draw.polygon(screen, dark, [(x + 3, y), (x + 15, y - 7 + flap), (x + 10, y + 4)])
            pygame.draw.circle(screen, e.color, pos, r)
        elif e.kind == "bruto":
            pygame.draw.circle(screen, e.color, pos, r)
            pygame.draw.circle(screen, dark, pos, r, 4)
            pygame.draw.line(screen, (30, 10, 10), (x - 9, y - 6), (x - 2, y - 3), 3)
            pygame.draw.line(screen, (30, 10, 10), (x + 9, y - 6), (x + 2, y - 3), 3)
        elif e.kind == "espectro":
            pygame.draw.circle(screen, dark, (x, y + 5), r - 2)   # estela
            pygame.draw.circle(screen, e.color, pos, r)
            pygame.draw.circle(screen, (235, 255, 255), pos, r, 2)
            pygame.draw.circle(screen, (10, 30, 40), (x - 4, y - 2), 2)
            pygame.draw.circle(screen, (10, 30, 40), (x + 4, y - 2), 2)
        else:   # zombi
            pygame.draw.circle(screen, e.color, pos, r)
            pygame.draw.circle(screen, dark, (x - 4, y - 2), 2)
            pygame.draw.circle(screen, dark, (x + 4, y - 2), 2)

    def draw_hud(self, screen):
        p = self.player
        pygame.draw.rect(screen, (40, 40, 60), (0, 0, WIDTH, 14))
        pygame.draw.rect(screen, COLOR_XP, (0, 0, WIDTH * p.xp / p.xp_to_next, 14))
        self.text(screen, f"Nivel {p.level}  -  {CLASSES[p.class_key]['name']}", (10, 20))

        pygame.draw.rect(screen, (60, 30, 36), (10, 48, 200, 14))
        pygame.draw.rect(screen, COLOR_HP, (10, 48, 200 * max(0, p.hp) / p.max_hp, 14))

        minutes, seconds = divmod(int(self.time), 60)
        self.text(screen, f"{minutes:02d}:{seconds:02d}", (WIDTH / 2, 38), self.font_big, center=True)
        self.text(screen, f"Bajas: {self.kills}", (WIDTH - 120, 20))

        # Armas equipadas (abajo a la izquierda)
        lines = ["Proyectil"] + [f"{WEAPONS[k][0]} Nv.{lv}" for k, lv in p.weapons.items()]
        for i, line in enumerate(reversed(lines)):
            self.text(screen, line, (10, HEIGHT - 28 - i * 24), color=(210, 210, 225))

        if self.show_fps:
            self.text(screen, f"FPS: {self.fps:4.1f}", (WIDTH - 120, 44), color=(255, 230, 120))

        if self.audio.enabled:
            if self.audio.muted:
                label = "M: sonido OFF"
            else:
                label = f"M: sonido ON  |  -/+: volumen {int(self.audio.master * 100)}%"
            self.text(screen, label, (WIDTH - 300, HEIGHT - 28), color=(170, 170, 190))

    def draw_level_up(self, screen):
        screen.blit(self.overlay(170), (0, 0))
        self.text(screen, "¡Subiste de nivel!", (WIDTH / 2, 110), self.font_big, center=True)
        for i, (name, desc, _) in enumerate(self.choices):
            rect = self.card_rect(i)
            pygame.draw.rect(screen, (40, 40, 70), rect, border_radius=10)
            pygame.draw.rect(screen, COLOR_XP, rect, 2, border_radius=10)
            self.text(screen, f"[{i + 1}]", (rect.centerx, rect.y + 28), center=True, color=COLOR_XP)
            self.text(screen, name, (rect.centerx, rect.y + 62), center=True)
            self.text(screen, desc, (rect.centerx, rect.y + 105), center=True, color=(170, 170, 190))

    @staticmethod
    def card_rect(i):
        w, h, gap = 290, 150, 20
        total = 3 * w + 2 * gap
        x = (WIDTH - total) / 2 + i * (w + gap)
        return pygame.Rect(x, 220, w, h)

    def draw_game_over(self, screen):
        screen.blit(self.overlay(180), (0, 0))
        minutes, seconds = divmod(int(self.time), 60)
        self.text(screen, "Has muerto", (WIDTH / 2, 230), self.font_big, color=COLOR_HP, center=True)
        self.text(screen, f"Sobreviviste {minutes:02d}:{seconds:02d}  |  Nivel {self.player.level}  |  Bajas {self.kills}",
                  (WIDTH / 2, 295), center=True)
        self.text(screen, "Pulsa R para volver al menú de clases", (WIDTH / 2, 345), center=True)


# ==========================================================================
# BUCLE PRINCIPAL
# ==========================================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Vampire Survivors")
    clock = pygame.time.Clock()
    game = Game(Audio())

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)   # limitar dt evita saltos si el juego se congela

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_m:
                    game.audio.toggle_mute()
                if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    game.audio.change_volume(-0.1)
                if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    game.audio.change_volume(0.1)
                if event.key == pygame.K_f:
                    game.show_fps = not game.show_fps
                if game.state == "levelup" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    game.choose_upgrade(event.key - pygame.K_1)
                if game.state == "gameover" and event.key == pygame.K_r:
                    game.to_menu()
                if game.state == "menu" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    game.start(event.key - pygame.K_1)
            if event.type == pygame.MOUSEBUTTONDOWN and game.state == "menu":
                for i in range(3):
                    if game.class_card_rect(i).collidepoint(event.pos):
                        game.start(i)
            if event.type == pygame.MOUSEBUTTONDOWN and game.state == "levelup":
                for i in range(3):
                    if game.card_rect(i).collidepoint(event.pos):
                        game.choose_upgrade(i)

        game.fps = clock.get_fps()
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()