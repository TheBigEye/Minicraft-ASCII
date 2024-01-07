import gzip
import pickle
from math import floor
from random import choice, randint, seed, shuffle
import sys
from time import time, time_ns

import pygame

# Pygame initialization
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Constants for the screen
FONT_SIZE: int = 16
FONT_PATH: str = "./assets/terrain.ttf"

# Initiate Pygame's sound module and define sound files
playerHurt = pygame.mixer.Sound('./assets/sounds/playerHurt.ogg')
genericHurt = pygame.mixer.Sound('./assets/sounds/genericHurt.ogg')
confirmSound = pygame.mixer.Sound('./assets/sounds/confirmSound.ogg')
eventSound = pygame.mixer.Sound('./assets/sounds/eventSound.ogg')
spawnSound = pygame.mixer.Sound('./assets/sounds/spawnSound.ogg')
typingSound = pygame.mixer.Sound('./assets/sounds/typingSound.ogg')

# Define colors in RGB format
WHITE: tuple = (255, 255, 255)
RED: tuple = (255, 0, 0)
GREEN: tuple = (0, 255, 0)
BLUE: tuple = (0, 0, 255)
BLACK: tuple = (0, 0, 0)
CYAN: tuple = (0, 255, 255)
YELLOW: tuple = (255, 255, 0)
MAGENTA: tuple = (255, 000, 255)

# Load the Consolas font
font = pygame.font.Font(FONT_PATH, FONT_SIZE)
text = pygame.font.Font("./assets/terrain.ttf", 16)

# Define terrain parameters
TERRAIN_SCALE: float = 0.002
TERRAIN_PERSISTENCE: float = 0.5
TERRAIN_OCTAVES: int = 8

# Define world parameters
RENDER_DISTANCE_VERTICAL: int = 1
RENDER_DISTANCE_HORIZONTAL: int = 2

# Define tile size
TILE_WIDTH: int = 16
TILE_HEIGHT: int = 16

# Define chunks size
CHUNK_SIZE: int = 16

SCREEN_WIDTH: int = 768
SCREEN_HEIGHT: int = 512

# Initialize the Pygame screen with predefined width and height and set window title
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
screen.set_alpha(None)
overlay = pygame.image.load('./assets/overlay.png').convert_alpha()
pygame.display.set_caption("Minicraft")


class Tile:
    """
    The `Tile` class represents a 16x16 pixel space in the game world. Each instance corresponds to a specific
    material, surface, or terrain type.

    ### Attributes:
        - `ID           (int)`: A unique identifier for each tile type.
        - `chars        (str)`: A string of characters that represent the tile's sprites.
        - `fc           (tuple or None)`: A tuple representing the RGB values of the sprite's foreground color.
        - `bc           (tuple or None)`: A tuple representing the RGB values of the sprite's background color.
        - `solid        (bool)`: A flag indicating whether the tile is solid. If `True`, the player cant walk on it.
        - `replacement  (bool)`: The replacement tile ID.
        - `value        (float)`: The noise value corresponding to the tile generation.
        - `health       (int)`: The initial health value of the tile.
    """

    def __init__(self, ID: int, chars: list, fc, bc, solid: bool, replacement: int | None, value: float | None, health: int | None):
        self.ID = ID
        self.chars = chars
        self.char = choice(chars)
        self.foreground = fc
        self.background = self._create_bcolor(bc)
        self.solid = solid
        self.replacement = replacement
        self.value = value
        self.health = health

        self.sprite = None

    ### Pickle trick!

    def __getstate__(self):
        # So we save the world tiles directly as objects, because we use pickle we can't
        # save the sprites as they are part of Pygame. But exist a little trick, so what
        # we do is exclude them using a automatic method and set them to None, so we can
        # save the tile now!

        state = self.__dict__.copy()
        state['sprite'] = None
        return state

    def __setstate__(self, state):
        # When we load the world, our class has the prites as None, so we need to recreate
        # them again, which is only done once and saves a lot of optimization

        # Which also significantly reduces memory usage.

        self.__dict__.update(state)
        if self.sprite is None:
            self.sprite = self._create_sprite()

    ### Tile private

    def _create_bcolor(self, bc):
        random_tone = randint(2, 4)
        return tuple(char // random_tone for char in bc) if bc is not None else bc

    def _create_sprite(self):
        return SpritePool.get_sprite(self.char, self.foreground, self.background)

    ### Tile public

    def render(self) -> pygame.Surface:
        if self.sprite is None:
            self.sprite = self._create_sprite()

        return self.sprite

    def unrender(self) -> None:
        if self.sprite is not None:
            self.sprite = None

    def hurt(self, x: int, y: int, damage: int) -> None:
        if self.health is not None:
            self.health -= damage
            genericHurt.play()
            if self.health <= 0 and self.replacement is not None:
                World.set_tile_id(x, y, self.replacement)

    def clone(self):
        return Tile(self.ID, self.chars, self.foreground, self.background, self.solid, self.replacement, self.value, self.health)

tiles = {
    # NAME               ID,   CHARS,                                   FOREGROUND,      BACKGROUND,      SOLID?,  REPLACEMENT, VALUE,  HEALTH
    "empty":         Tile(0,   ['¿?'],                                  (255, 000, 000), ( 64, 000, 000), False,   None,        None,   None ),
    "player":        Tile(1,   ['☻'],                                   (000, 255, 255), (000, 000, 000), False,   None,        None,   None ),

    "ocean":         Tile(2,   ["~'", "'~"],                            ( 44,  44, 178), ( 44,  44, 178), False,   None,        0.14,   None ),
    "sea":           Tile(3,   ['≈˜'],                                  ( 54,  54, 217), ( 54,  54, 217), False,   None,        0.28,   None ),
    "river":         Tile(4,   ['┬┴', '┴┬', '•┬', '┴•', '┬•', '•┴'],    ( 63,  63, 252), ( 63,  63, 252), False,   None,        None,   None ),
    "sand":          Tile(5,   ['≈~', '~≈'],                            (210, 199, 139), (210, 199, 139), False,   6,           0.42,   1    ),
    "dirt":          Tile(6,   ['~≈', '≈~'],                            (139,  69,  19), (139,  69,  19), False,   7,           None,   1    ),
    "hole":          Tile(7,   ['•˚', '˚•'],                            (139,  69,  19), (139,  69,  19), False,   None,        None,   None ),
    "grass":         Tile(8,   ['.ⁿ', 'ⁿ.'],                            (126, 176,  55), (126, 176,  55), False,   6,           0.65,   1    ),
    "tall grass":    Tile(9,   ['"ⁿ', 'ⁿ"'],                            (108, 151,  47), (108, 151,  47), False,   8,           0.88,   2    ),

    "oak tree":      Tile(10,  ['♠♣'],                                  (000, 128, 000), (000, 128, 000), True,    8,           0.96,   16   ),
    "birch tree":    Tile(11,  ['♣♠'],                                  (000, 176, 000), (000, 176, 000), True,    8,           1.04,   24   ),
    "pine tree":     Tile(12,  ['Γ♠'],                                  (000, 224, 000), (000, 224, 000), True,    7,           1.10,   32   ),

    "low mountain":  Tile(13,  ['⌂⌂'],                                  (111, 111, 111), (111, 111, 111), True,    6,           1.80,   32   ),
    "top mountain":  Tile(14,  ['▲▲'],                                  (200, 200, 200), (200, 200, 200), True,    13,          1.98,   48   )
}

class SpritePool:
    pool: dict = {}

    @staticmethod
    def initialize():
        print("\n## Initializing Sprite pool cache! ...")

        for name, tile in tiles.items():
            print(f"-> Building pool for '{name}' tile ...")

            chars = tile.chars
            foreground = tile.foreground
            background = tile.background

            for char in chars:
                for i in range(2, 4):
                    bg = tuple(col // i for col in background) if background is not None else background

                    key = (char, foreground, bg)
                    sprite = font.render(char, False, foreground, bg).convert()
                    SpritePool.pool[key] = sprite

        print("\n## Initilialized Sprite pool cache!")


    @staticmethod
    def get_sprite(char, foreground, background):
        key = (char, foreground, background)

        # Si el sprite ya existe en el pool, lo reutilizamos
        if key in SpritePool.pool:
            return SpritePool.pool[key]

        # Si no, creamos un nuevo sprite y lo agregamos al pool
        sprite = font.render(char, False, foreground, background).convert()
        SpritePool.pool[key] = sprite
        return sprite



class World:

    seed: int | str = 0  # Seed for terrain generation
    grid: bool = False  # For debugging (default: False)
    perm: list = []  # Permutation matrix for noise generation

    # Storage for terrain and chunks
    terrain: dict = {}
    spawn: tuple = (0, 0)

    # Method to initialize the world
    @staticmethod
    def initialize(worldseed: int | str, area: int) -> None:

        World.seed = worldseed
        seed(worldseed)

        World.grid = False
        World.perm = World.permutation()

        World.terrain = {}
        World.spawn = (0, 0)

        xp = Player.x // CHUNK_SIZE
        yp = Player.y // CHUNK_SIZE

        for chunk_x in range(xp - area, xp + area):
            for chunk_y in range(yp - area, yp + area):
                xp = Player.x // CHUNK_SIZE
                yp = Player.y // CHUNK_SIZE

                World.generate_chunk(chunk_x, chunk_y)

    @staticmethod
    def generate_chunk(x: int, y: int) -> None:
        if (x, y) in World.terrain:
            return

        chunk = [[tiles["empty"].clone()] * CHUNK_SIZE for _ in range(CHUNK_SIZE)]

        for h in range(CHUNK_SIZE):
            for w in range(CHUNK_SIZE):
                wy, wx = y * CHUNK_SIZE + h, x * CHUNK_SIZE + w
                terrain_value = World.terrain_value(wx, wy)
                current_tile = World.tile_from_value(terrain_value)

                if current_tile.ID == tiles["low mountain"].ID and 0.96 < terrain_value < 1.80:
                    current_tile = tiles["pine tree"].clone()
                elif 1.80 < terrain_value < 1.98:
                    current_tile = tiles["low mountain"].clone()
                elif terrain_value > 1.98:
                    current_tile = tiles["top mountain"].clone()

                if terrain_value > 0.60 and current_tile.ID in {tiles["oak tree"].ID, tiles["birch tree"].ID, tiles["pine tree"].ID} and randint(0, 8) <= 4:
                    current_tile = tiles["oak tree"].clone() if randint(0, 1) == 0 else tiles["birch tree"].clone()

                if current_tile.ID in {tiles["oak tree"].ID, tiles["birch tree"].ID, tiles["pine tree"].ID} and randint(0, 8) <= 4:
                    if 0.90 < terrain_value < 1.08 or (1.08 < terrain_value < 1.32 and randint(0, 1) == 1):
                        current_tile = tiles["tall grass"].clone()

                chunk[h][w] = current_tile

                if World.spawn[0] == 0 and current_tile.ID in {tiles["grass"].ID, tiles["sand"].ID}:
                    World.spawn = (wx, wy)

        World.terrain[(x, y)] = chunk


    @staticmethod
    def perlin(x: float, y: float, persistence: float, octaves: int) -> float:
        """ Generate Perlin noise for terrain generation """
        total: float = 0
        frequency: float = 2.16
        amplitude: float = 1.00
        max_value: float = 0
        for _ in range(octaves):
            total += World.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.1 # lacunarity
        return total / max_value

    @staticmethod
    def noise(x: float, y: float) -> float:
        """ Generate noise from a permutation matrix """
        # Retrieve the permutation matrix
        p = World.perm

        # Calculate the integer parts of x and y
        X: int = floor(x) & 255
        Y: int = floor(y) & 255

        # Calculate the fractional parts of x and y
        x -= floor(x)
        y -= floor(y)

        # Calculate the fade factor for x and y
        u: float = World.fade(x)
        v: float = World.fade(y)

        # Calculate the indices for the four corners of the current cell in the permutation matrix
        A: int = p[X] + Y
        B: int = p[X + 1] + Y

        # Perform linear interpolation and gradient calculation to generate the noise value
        n: float = World.lerp(v,
            World.lerp(u,
                World.grad(p[A], x, y),
                World.grad(p[B], x - 1, y)
            ),
            World.lerp(u,
                World.grad(p[A + 1], x, y - 1),
                World.grad(p[B + 1], x - 1, y - 1)
            )
        )

        return n

    @staticmethod
    def fade(t):
        """ Interpolation function to smooth noise """
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def lerp(t, a, b):
        """ Linear interpolation """
        return a + t * (b - a)

    @staticmethod
    def grad(h, x, y):
        """
        Generate noise gradient

        The grad function generates a noise gradient based on the provided hash, x, and y values.
        It uses bitwise operations to manipulate the hash value and determine the gradient direction.
        The result is calculated by multiplying the gradient with the sum of x and y.
        """
        # Extract the last 4 bits of the hash value
        h = h & 15

        # Determine the gradient value based on the last 3 bits of h
        grad = 1 + (h & 7)

        # Check if the 4th bit of h is set
        if h & 8:
            # Negate the gradient value if the 4th bit is set
            grad = -grad

        # Calculate the final result by multiplying the gradient with the sum of x and y
        result = grad * (x + y)

        # Return the result
        return result

    @staticmethod
    def permutation() -> list:
        """ Generate a random permutation of values for noise """
        p = list(range(256))
        shuffle(p)
        p += p
        return p

    @staticmethod
    def terrain_value(x: int, y: int) -> float:
        return World.perlin(x * TERRAIN_SCALE, y * TERRAIN_SCALE, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)

    @staticmethod
    def tile_from_value(value: float | None) -> Tile:
        """ Return a tile character based on terrain value """
        # Use a list comprehension to filter tiles with values
        matching_tiles = [
            tiles[name].clone()
            for name in tiles
            if tiles[name].value is not None and value < tiles[name].value
        ]

        # Return the first matching tile, or a clone of the "top mountain" tile if none found
        return matching_tiles[0] if matching_tiles else tiles["top mountain"].clone()

    @staticmethod
    def get_tile(x: int, y: int) -> Tile:
        """ Get the character at coordinates in the world """
        # Calculate the chunk coordinates
        cx = x // CHUNK_SIZE
        cy = y // CHUNK_SIZE

        # Load the chunk at the calculated chunk coordinates
        World.load_chunk(cx, cy)

        # Calculate the local coordinates within the chunk
        ly = y % CHUNK_SIZE
        lx = x % CHUNK_SIZE

        # Return the character at the calculated local coordinates in the world
        return World.terrain[(cx, cy)][ly][lx]

    @staticmethod
    def set_tile(x: int, y: int, tile: Tile) -> None:
        """ Update the world map with the replacement tile """
        # Calculate the chunk coordinates
        cx = x // CHUNK_SIZE
        cy = y // CHUNK_SIZE

        # Load the chunk at the calculated chunk coordinates
        World.load_chunk(cx, cy)

        # Calculate the local coordinates within the chunk
        ly = y % CHUNK_SIZE
        lx = x % CHUNK_SIZE

        World.terrain[(cx, cy)][ly][lx] = tile.clone()

    @staticmethod
    def set_tile_id(x: int, y: int, tile: int) -> None:
        """ Update the world map with the replacement tile by ID """
        # Calculate the chunk coordinates
        cx = x // CHUNK_SIZE
        cy = y // CHUNK_SIZE

        # Load the chunk at the calculated chunk coordinates
        World.load_chunk(cx, cy)

        # Calculate the local coordinates within the chunk
        ly = y % CHUNK_SIZE
        lx = x % CHUNK_SIZE

        for name in tiles:
            if tiles[name].ID == tile:
                World.terrain[(cx, cy)][ly][lx] = tiles[name].clone()

    @staticmethod
    def load_chunk(x: int, y: int) -> None:
        """ Load a chunk to memory """
        if (x, y) not in World.terrain:
            World.generate_chunk(x, y)

    @staticmethod
    def daytime() -> int:
        return Updater.time % 24000

    @staticmethod
    def daylight() -> int:
        time = Updater.time % 24000
        if time < 3000:
            return int(32 + ((time / 3000) * (255 - 32)))
        elif time < 16000:
            return 255
        elif time < 18000:
            return int(255 - (((time - 16000) / 2000) * (255 - 32)))
        else:
            return 32

    @staticmethod
    def render() -> None:
        offset_x: int = SCREEN_WIDTH // 2 - (Player.x % 16) * TILE_WIDTH
        offset_y: int = SCREEN_HEIGHT // 2 - (Player.y % 16) * TILE_HEIGHT

        sprites: list = []

        overlay.set_alpha(255 - World.daylight())

        for x in range(-(RENDER_DISTANCE_HORIZONTAL + 1), RENDER_DISTANCE_HORIZONTAL + 2):
            for y in range(-RENDER_DISTANCE_VERTICAL, RENDER_DISTANCE_VERTICAL + 1):
                World.load_chunk(Player.cx + x, Player.cy + y)
                chunk = World.terrain.get((Player.cx + x, Player.cy + y))

                if chunk is None:
                    continue

                for tile_y in range(CHUNK_SIZE):
                    for tile_x in range(CHUNK_SIZE):
                        # World positions
                        wx: int = x * CHUNK_SIZE + tile_x
                        wy: int = y * CHUNK_SIZE + tile_y

                        # Screen positions
                        sx: int = wx * TILE_WIDTH + offset_x
                        sy: int = wy * TILE_HEIGHT + offset_y

                        if 0 <= sx < SCREEN_WIDTH and 0 <= sy < SCREEN_HEIGHT:
                            tile: Tile = chunk[tile_y][tile_x]
                            sprites.append((tile.render(), (sx, sy)))
                        else:
                            tile: Tile = chunk[tile_y][tile_x]
                            tile.unrender()

        screen.blits(sprites)

        # TODO: put this into sprites cache!
        screen.blit(overlay, (0, 0))

        if World.grid:
            # Draw the debug chunks grid
            for x in range(-(RENDER_DISTANCE_HORIZONTAL + 1), RENDER_DISTANCE_HORIZONTAL + 2):
                for y in range(-RENDER_DISTANCE_VERTICAL, RENDER_DISTANCE_VERTICAL + 1):
                    neighbors = [
                        (Player.cx + x - 1, Player.cy + y),
                        (Player.cx + x + 1, Player.cy + y),
                        (Player.cx + x, Player.cy + y - 1),
                        (Player.cx + x, Player.cy + y + 1)
                    ]

                    generated_neighbors = [chunk in World.terrain for chunk in neighbors]

                    chunk_x_draw = (x * CHUNK_SIZE) * TILE_WIDTH + offset_x
                    chunk_y_draw = (y * CHUNK_SIZE) * TILE_HEIGHT + offset_y

                    chunk_rect = pygame.Rect(chunk_x_draw, chunk_y_draw, CHUNK_SIZE * TILE_WIDTH, CHUNK_SIZE * TILE_HEIGHT)

                    if (Player.cx + x, Player.cy + y) == (Player.cx, Player.cy):
                        pygame.draw.rect(screen, BLUE, chunk_rect, 1)  # Blue for current player chunk
                        pygame.draw.rect(screen, BLACK, chunk_rect.inflate(-2, -2), 1)  # White
                    elif not all(generated_neighbors):
                        pygame.draw.rect(screen, RED, chunk_rect, 1)  # Red for ungenerated
                        pygame.draw.rect(screen, BLACK, chunk_rect.inflate(-2, -2), 1)  # White
                    else:
                        pygame.draw.rect(screen, GREEN, chunk_rect, 1)  # Green for loaded
                        pygame.draw.rect(screen, BLACK, chunk_rect.inflate(-2, -2), 1)  # White

    @staticmethod
    def tick() -> None:

        for x in range(Player.cx - 2, Player.cx + 3):
            for y in range(Player.cy - 2, Player.cy + 3):
                World.update_chunk(x, y)

    @staticmethod
    def update_chunk(chunk_x: int, chunk_y: int) -> None:
        if Updater.time % 32 == 0 and randint(0, 16) == 8:
            World.update_tiles(chunk_x, chunk_y, [tiles["grass"]], tiles["dirt"], tiles["grass"])

        if Updater.time % 8 == 0:
            World.update_tiles(chunk_x, chunk_y, [tiles["ocean"], tiles["sea"], tiles["river"]], tiles["hole"], tiles["river"])

    @staticmethod
    def update_tiles(chunk_x: int, chunk_y: int, current_tiles: list, target_tile: Tile, replace_tile: Tile) -> None:
        current_chunk: list = World.terrain.get((chunk_x, chunk_y))

        if current_chunk:
            updated_chunk: list = World.update_tile(current_chunk, current_tiles, target_tile, replace_tile, chunk_x, chunk_y)
            if updated_chunk != current_chunk:
                World.terrain[(chunk_x, chunk_y)] = updated_chunk

    @staticmethod
    def update_tile(current_chunk, current_tiles: list, target_tile: Tile, replace_tile: Tile, chunk_x: int, chunk_y: int) -> list:
        temp_chunk = [row[:] for row in current_chunk]

        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                closest_tile: Tile = current_chunk[y][x]
                if closest_tile.ID == target_tile.ID and World.tile_around(current_tiles, x, y, chunk_x, chunk_y):
                    temp_chunk[y][x] = replace_tile.clone()

        return temp_chunk

    @staticmethod
    def tile_around(tiles_around: list, x: int, y: int, chunk_x: int, chunk_y: int) -> bool:
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_y = (y + dy) % CHUNK_SIZE
            new_x = (x + dx) % CHUNK_SIZE
            new_chunk_x: int = chunk_x + (x + dx) // CHUNK_SIZE
            new_chunk_y: int = chunk_y + (y + dy) // CHUNK_SIZE

            around_chunk: list = World.terrain.get((new_chunk_x, new_chunk_y))

            if around_chunk is not None:
                around_tile: Tile = around_chunk[new_y][new_x]
                if around_tile.ID in [tile.ID for tile in tiles_around]:
                    return True

        return False

class Player:
    # Player's world coordinates
    x: int = 0
    y: int = 0

    # Player's local chunk position
    cx: int = 0
    cy: int = 0

    stamina: int = 20  # Player's stamina which decreases when player breaks a tile
    health: int = 20   # Player's health which decreases when player gets damaged

    direction = "w"  # The direction where the player is facing

    cursor_blink: bool = False
    cursor_timer: int = 0

    @staticmethod
    def is_swimming() -> bool:
        # Check if the player is swimming (in water)
        current_tile = World.get_tile(Player.x, Player.y).ID
        return current_tile in (tiles["ocean"].ID, tiles["sea"].ID, tiles["river"].ID)

    @staticmethod
    def coordinates(direction: str, xd: int, yd: int) -> tuple:
        """ Adjust the player's x and y coordinates based on the direction """
        if direction == 'w': yd -= 1
        elif direction == 's': yd += 1
        elif direction == 'a': xd -= 1
        elif direction == 'd': xd += 1

        return xd, yd

    @staticmethod
    def can_move(direction: str) -> bool:
        """ Check if the player can move in the specified direction """
        xd, yd = Player.coordinates(direction, Player.x, Player.y)
        Player.direction = direction

        return not World.get_tile(xd, yd).solid

    @staticmethod
    def break_tile(direction: str) -> None:
        """ Break the tile in the specified direction """

        xd, yd = Player.coordinates(direction, Player.x, Player.y)
        Player.direction = direction

        if Player.stamina >= int(0.32 * 20):
            Player.stamina = int(max(0, Player.stamina - 0.32 * 20))
            World.get_tile(xd, yd).hurt(xd, yd, 8)

    @staticmethod
    def render() -> None:
        screen_x = SCREEN_WIDTH // 2
        screen_y = SCREEN_HEIGHT // 2

        # Adjust the player's x and y coordinates based on the direction
        xd, yd = Player.coordinates(Player.direction, Player.x, Player.y)

        # Calculate the position of the tile in front of the player
        tile_target_x = xd - Player.x
        tile_target_y = yd - Player.y

        # Calculate the screen coordinates of the tile in front of the player
        front_tile_x = screen_x + (tile_target_x * TILE_WIDTH)
        front_tile_y = screen_y + (tile_target_y * TILE_HEIGHT)

        # Then we draw the player at the center of the screen
        screen.blit(tiles["player"].render(), (screen_x + 4, screen_y))

        tile_image = World.get_tile(xd, yd).render()

        if not Player.cursor_blink:
            tile_high = tile_image.copy()
            tile_color = World.get_tile(xd, yd).background
            tile_high.fill((tile_color[0] * 3, tile_color[1] * 3, tile_color[2] * 3), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(tile_high, (front_tile_x, front_tile_y))


    @staticmethod
    def tick() -> None:
        # This function gets called every frame, hence we can use it to
        # decrease or regenerate the stamina or the health of the player

        Player.cx = Player.x // CHUNK_SIZE
        Player.cy = Player.y // CHUNK_SIZE

        Player.cursor_timer += 1
        if Player.cursor_timer >= 16:
            Player.cursor_timer = 0
            Player.cursor_blink = not Player.cursor_blink

        if Updater.time % 15 == 0:
            # Decrease stamina if we are swiming
            if Player.stamina > 0 and Player.is_swimming():
                Player.stamina = max(0, Player.stamina - 1)

            # Increase health if stamina is higher than half
            if Player.stamina > 10:
                Player.health = min(20, Player.health + 1)

        if Updater.time % 30 == 0 and Player.stamina < 1:
            if Player.is_swimming():
                Player.health = max(0, Player.health - 1)
                playerHurt.play()

        if Updater.time % 3 == 0 and Player.stamina < 20:
            if not Player.is_swimming():
                Player.stamina = min(20, Player.stamina + 1)


class Updater:
    time = 0
    timer = 4
    clock = pygame.time.Clock()

    @staticmethod
    def update() -> None:
        # This function counts the elapsed time (in frames) and then it moves
        # the player or breaks the tile in front of the player if certain keys are being pressed
        # In addition to that, it also updates the chunks in the world.
        key = pygame.key.get_pressed()

        if Player.is_swimming():
            Updater.timer = 8
        else:
            Updater.timer = 4

        if Updater.time % Updater.timer == 0:
            if key[pygame.K_UP] and Player.can_move('w'):
                Player.y -= 1

            if key[pygame.K_LEFT] and Player.can_move('a'):
                Player.x -= 1

            if key[pygame.K_DOWN] and Player.can_move('s'):
                Player.y += 1

            if key[pygame.K_RIGHT] and Player.can_move('d'):
                Player.x += 1

            if key[pygame.K_c]:
                Player.break_tile(Player.direction)

            if key[pygame.K_LSHIFT]:
                # Toggle chunks grid
                if key[pygame.K_g]:
                    World.grid = not World.grid

                # Save world
                if key[pygame.K_s]:
                    Saveload.save_world()
                    eventSound.play()

                # Load world
                if key[pygame.K_l]:
                    Saveload.load_world()
                    eventSound.play()

            # Move the player to the spawn
            if key[pygame.K_r]:
                Player.x, Player.y = World.spawn
                spawnSound.play()

            # Move the player to the farlands
            if key[pygame.K_f]:
                Player.x += (((sys.maxsize * sys.maxsize) * sys.maxsize) * sys.maxsize) * sys.maxsize

        World.tick()
        Player.tick()

class Screen:

    HOTBAR_LENGTH = SCREEN_WIDTH // 8
    BORDER_HEIGHT = SCREEN_HEIGHT - 34
    HEARTS_HEIGHT = SCREEN_HEIGHT - 32
    STAMINA_HEIGHT = SCREEN_HEIGHT - 16

    HOTBAR_BORDERLINE = text.render("¯", False, WHITE, BLACK).convert()
    HOTBAR_L_BRACKET = text.render("[", False, (32, 32, 32), BLACK).convert()
    HOTBAR_R_BRACKET = text.render("]", False, (32, 32, 32), BLACK).convert()
    HOTBAR_BACKGROUND = text.render(" ", False, BLACK, BLACK).convert()
    HEART_NONE = text.render("♥", False, (16, 16, 16)).convert()
    HEART_FULL = text.render("♥", False, RED).convert()
    STAMINA_NONE = text.render("○", False, (16, 16, 16)).convert()
    STAMINA_FULL = text.render("●", False, YELLOW).convert()

    @staticmethod
    def title() -> None:
        # Screen initialization function. Prompts a textbox for the user to enter seed value
        # for world generation.
        seed_input = ""
        seed_text = text.render("Enter World Seed:", False, (000, 255, 255), BLACK).convert()

        pygame.mixer.music.load('./assets/sounds/titleTheme.ogg')
        pygame.mixer.music.play(-1, fade_ms = 4000)

        # Initialize color variables for the title
        color_increment = 2
        cian_value = 130
        cursor_visible = True
        cursor_timer = 0

        title_text = [
            "      ███╗   ███╗ ██╗ ███╗   ██╗ ██╗  ██████╗ ██████╗   █████╗  ███████╗ ████████╗  ",
            "     ████╗ ████║ ██║ ████╗  ██║ ██║ ██╔════╝ ██╔══██╗ ██╔══██╗ ██╔════╝ ╚══██╔══╝   ",
            "    ██╔████╔██║ ██║ ██╔██╗ ██║ ██║ ██║      ██████╔╝ ███████║ █████╗      ██║       ",
            "   ██║ ██╔╝██║ ██║ ██║ ██╗██║ ██║ ██║      ██╔══██╗ ██╔══██║ ██╔══╝      ██║        ",
            "  ██║  ╚╝ ██║ ██║ ██║  ████║ ██║  ██████╗ ██║  ██║ ██║  ██║ ██║         ██║         ",
            "  ╚═╝     ╚═╝ ╚═╝ ╚═╝  ╚═══╝ ╚═╝  ╚═════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝         ╚═╝         ",
            "                                 ‟ POTATO EDITION ”                                 "
        ]

        title_text = [line.replace("█", symbol) for line, symbol in zip(title_text, ["░", "▒", "▒", "▓", "▓", "█", " "])]

        y = 16 * 7
        line_height = 16

        screen_center_x = SCREEN_WIDTH // 2
        screen_center_y = SCREEN_HEIGHT // 2

        seed_input_rect = pygame.Rect(screen_center_x - 136, screen_center_y + 48, 272, 40)

        # Start text input
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(seed_input_rect)

        running = True
        while running:
            screen.fill((0, 0, 0))

            for line in title_text:
                title_surface = text.render(line, False, (0, cian_value, cian_value), (0, 0, 0)).convert()
                title_rect = title_surface.get_rect(center=(screen_center_x, y))
                screen.blit(title_surface, title_rect)
                y += line_height

            y = 16 * 7

            # Update cian value for the blinking effect
            cian_value += color_increment
            if cian_value in (250, 128):
                color_increment = -color_increment

            cursor_timer += 1
            if cursor_timer >= 8:
                cursor_timer = 0
                cursor_visible = not cursor_visible

            seed_rect = seed_text.get_rect(center=(screen_center_x, (screen_center_y + (16 * 2))))
            screen.blit(seed_text, seed_rect)

            pygame.draw.rect(screen, (000, 255, 255), seed_input_rect, 1)

            # Render and display input text with cursor
            seed_input_with_cursor = seed_input + ("█" if cursor_visible else " ")
            input_text = text.render(seed_input_with_cursor, True, (128, 128, 128), BLACK).convert()
            input_rect = input_text.get_rect(center=seed_input_rect.center)
            screen.blit(input_text, input_rect)

            pygame.display.update()
            Updater.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    pygame.key.stop_text_input()
                elif event.type == pygame.TEXTINPUT:
                    if len(seed_input) < 32:
                        seed_input += event.text
                        typingSound.play()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if len(seed_input) == 0:
                            world_seed = randint(-(2**19937-1), 2**19937-1)
                        else:
                            world_seed = seed_input

                        confirmSound.play()
                        pygame.mixer.music.fadeout(2000)
                        pygame.mixer.music.unload()
                        pygame.key.stop_text_input()
                        World.initialize(world_seed, 3)
                        Player.x, Player.y = World.spawn
                        running = False
                    elif event.key == pygame.K_BACKSPACE:
                        seed_input = seed_input[:-1]

    @staticmethod
    def hotbar() -> None:

        surfaces: list = []

        # Prepare the hotbar background
        surfaces += [(Screen.HOTBAR_BORDERLINE, (i * 8, Screen.BORDER_HEIGHT)) for i in range(Screen.HOTBAR_LENGTH)]
        surfaces += [(Screen.HOTBAR_BACKGROUND, (i * 8, Screen.HEARTS_HEIGHT)) for i in range(Screen.HOTBAR_LENGTH)]
        surfaces += [(Screen.HOTBAR_BACKGROUND, (i * 8, Screen.STAMINA_HEIGHT)) for i in range(Screen.HOTBAR_LENGTH)]

        xp = text.render(f"X: {Player.x}", True, (32, 32, 32), BLACK).convert()
        yp = text.render(f"Y: {Player.y}", True, (32, 32, 32), BLACK).convert()

        surfaces.append((xp, ((Screen.HOTBAR_LENGTH * 8) - 32 - (len(str(Player.x)) * 8), Screen.HEARTS_HEIGHT)))
        surfaces.append((yp, ((Screen.HOTBAR_LENGTH * 8) - 32 - (len(str(Player.y)) * 8), Screen.STAMINA_HEIGHT)))

        surfaces.append((Screen.HOTBAR_L_BRACKET, (8, Screen.HEARTS_HEIGHT + 1)))
        surfaces.append((Screen.HOTBAR_R_BRACKET, (176, Screen.HEARTS_HEIGHT + 1)))

        surfaces.append((Screen.HOTBAR_L_BRACKET, (8, Screen.STAMINA_HEIGHT - 1)))
        surfaces.append((Screen.HOTBAR_R_BRACKET, (176, Screen.STAMINA_HEIGHT - 1)))

        # Prepare the hearts bar
        surfaces += [(Screen.HEART_FULL if i < Player.health else Screen.HEART_NONE, (16 + (i * 8), Screen.HEARTS_HEIGHT + 1)) for i in range(20)]

        # Prepare the stamina bar
        surfaces += [(Screen.STAMINA_FULL if i < Player.stamina else Screen.STAMINA_NONE, (16 + (i * 8), Screen.STAMINA_HEIGHT - 1)) for i in range(20)]

        # Render all at once
        screen.blits(surfaces)


    @staticmethod
    def update() -> None:
        # Draw the tiles, player, border and other stuffs here.
        # This function gets called every frame to update everything on the screen
        # First, it clears the screen
        screen.fill(0)

        World.render()
        Player.render()
        Screen.hotbar()

        pygame.display.update()


class Saveload:

    # TODO: split the save file in two prts/files, world.dat (world seed, player stuff, and config)
    # and world.sav (world saved chunks and data). So, if the player deletes
    # world.sav but world.dat is present, so the world will be generated again

    # Yeah, this uses Gzip, it make all a bit slow, but its OK

    @staticmethod
    def save_world() -> None:
        world_data = {
            'About': {
                'name': "A Nice World"
            },
            'Player': {
                'x': Player.x,
                'y': Player.y,
                'stamina': Player.stamina,
                'health': Player.health,
                'direction': Player.direction
            },
            'WorldSeed': World.seed,
            'WorldPerm': World.perm,
            'WorldSpawn': World.spawn,
            'GameTime': Updater.time,
            'Terrain': World.terrain
        }

        with gzip.open('./saves/world.dat', 'wb') as file:
            pickle.dump(world_data, file, protocol=4)

    @staticmethod
    def load_world() -> None:
        with gzip.open('./saves/world.dat', 'rb') as file:
            world_data = pickle.load(file)

        player_data = world_data['Player']
        Player.x = player_data['x']
        Player.y = player_data['y']
        Player.stamina = player_data['stamina']
        Player.health = player_data['health']
        Player.direction = player_data['direction']

        World.seed = world_data['WorldSeed']
        World.perm = world_data['WorldPerm']
        World.spawn = world_data['WorldSpawn']
        Updater.time = world_data['GameTime']

        World.terrain = world_data['Terrain']

def main() -> None:

    SpritePool.initialize()

    try:
        Saveload.load_world()
        eventSound.play()
    except FileNotFoundError:
        Screen.title()

    last_time = time_ns()
    unprocessed = 0
    ns_per_tick = 1e9 / 30
    ticks = 0
    last_timer = time()

    running = True
    while running:
        for _ in pygame.event.get(pygame.QUIT):
            running = False

        now = time_ns()
        unprocessed += (now - last_time) / ns_per_tick
        last_time = now
        should_render = False

        while unprocessed >= 1:
            ticks += 1
            Updater.time += 1
            Updater.update()
            unprocessed -= 1
            should_render = True

        Updater.clock.tick(30)

        if should_render:
            Screen.update()

        if time() - last_timer > 1:
            last_timer += 1
            print(f"- FPS: {int(Updater.clock.get_fps())} ({ticks} TPS) --- daytime: {World.daytime()} ({World.daylight()} daylight)")
            ticks = 0

    pygame.quit()


if __name__ == "__main__":
    main()
