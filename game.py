import gzip
import pickle
import sys
from random import choice, randint, seed
from time import time, time_ns
from typing import List

import pygame

from source.globals import *
from source.noise import Generator
from source.screen import Color, TitleMenu
from source.sound import Sound
from source.sprite import SpritePool

# Pygame initialization
pygame.init()
pygame.font.init()

Sound.initialize()

# Load the Consolas font
font = pygame.font.Font("./assets/terrain.ttf", 16)
text = pygame.font.Font("./assets/terrain.ttf", 16)

# Initialize the Pygame screen with predefined width and height and set window title
screen = pygame.display.set_mode(SCREEN_SIZE_T)
screen.set_alpha(None)

overlay = pygame.image.load('./assets/overlay.png').convert_alpha()
winicon = pygame.image.load('./assets/icon.png').convert_alpha()

pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.TEXTINPUT])
pygame.display.set_caption("Minicraft Potato Edition")
pygame.display.set_icon(winicon)

clock = pygame.time.Clock()

title_menu: TitleMenu = TitleMenu(screen, text)
sprite_pool: SpritePool = SpritePool(font)


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
        - `health       (int)`: The initial health value of the tile.
    """

    def __init__(self, ID: int, chars: list[str], fc, bc, solid: bool, replacement: int | None, health: int | None):
        self.ID = ID
        self.chars = chars
        self.char = choice(chars)
        self.foreground = fc
        self.background = self._set_backcolor(bc)
        self.solid = solid
        self.replacement = replacement
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
            self.sprite = self._get_sprite()

    ### Tile private

    def _set_backcolor(self, bc):
        rand_num = randint(2, 3)
        return tuple(char // rand_num  for char in bc) if bc is not None else bc

    def _get_sprite(self):
        return sprite_pool.get(self.char, self.foreground, self.background)

    ### Tile public

    def render(self) -> pygame.Surface:
        if self.sprite is None:
            self.sprite = self._get_sprite()

        return self.sprite

    def unrender(self) -> None:
        """ Unrenders (deletes) the tile sprite, freeing up memory """
        if self.sprite is not None:
            del self.sprite
            self.sprite = None

    def hurt(self, x: int, y: int, damage: int) -> None:
        if self.health is not None:
            self.health -= damage
            Sound.play("genericHurt")
            if (self.health <= 0) and (self.replacement is not None):
                World.set_tile_id(x, y, self.replacement)
                self.unrender()

    def clone(self):
        """ Returns a copy of the tile instance """
        return Tile(self.ID, self.chars, self.foreground, self.background, self.solid, self.replacement, self.health)


tiles = {
    # NAME               ID,   CHARS,                                   FOREGROUND,      BACKGROUND,      SOLID?,  REPLACEMENT, HEALTH
    "empty":         Tile(0,   ['¿?'],                                  (255, 000, 000), ( 64, 000, 000), False,   None,        None ),
    "player":        Tile(1,   ['☻'],                                   (000, 255, 255), (000, 000, 000), False,   None,        None ),

    "ocean":         Tile(2,   ["~'", "'~"],                            ( 44,  44, 178), ( 44,  44, 178), False,   None,        None ),
    "sea":           Tile(3,   ['≈˜', '˜≈'],                            ( 54,  54, 217), ( 54,  54, 217), False,   None,        None ),
    "river":         Tile(4,   ['┬┴', '┴┬', '•┬', '┴•', '┬•', '•┴'],    ( 63,  63, 252), ( 63,  63, 252), False,   None,        None ),
    "sand":          Tile(5,   ['≈~', '~≈'],                            (210, 199, 139), (210, 199, 139), False,   6,           1    ),
    "dirt":          Tile(6,   ['~≈', '≈~'],                            (139,  69,  19), (139,  69,  19), False,   7,           1    ),
    "hole":          Tile(7,   ['•˚', '˚•'],                            (139,  69,  19), (139,  69,  19), False,   None,        None ),
    "grass":         Tile(8,   ['.ⁿ', 'ⁿ.'],                            (126, 176,  55), (126, 176,  55), False,   6,           1    ),
    "tall grass":    Tile(9,   ['"ⁿ', 'ⁿ"'],                            (108, 151,  47), (108, 151,  47), False,   8,           2    ),

    "oak tree":      Tile(10,  ['♣♠'],                                  (000, 128, 000), (000, 128, 000), True,    8,           16   ),
    "birch tree":    Tile(11,  ['¶♠'],                                  (000, 178, 000), (000, 178, 000), True,    8,           24   ),
    "pine tree":     Tile(12,  ['Γ♠'],                                  (000, 232, 000), (200, 200, 200), True,    7,           32   ),

    "cliff":         Tile(13,  ['n∩', '∩n', 'n⌂', '⌂n'],                (121, 121, 121), (111, 111, 111), True,    6,           32   ),
    "mountain":      Tile(14,  ['≈~', '~≈'],                            ( 50,  50,  50), ( 50,  50,  50), True,    13,          48   ),

    "snow":          Tile(15,  ['.ⁿ', 'ⁿ.'],                            (220, 220, 220), (200, 200, 200), False,   6,           1    ),
    "frost":         Tile(16,  ['"ⁿ', 'ⁿ"'],                            (238, 238, 238), (238, 238, 238), False,   8,           2    )
}

class World:

    seed: int | str = None  # Seed for terrain generation
    grid: bool = False  # For debugging (default: False)
    perm: list = []  # Permutation matrix for noise generation

    # Storage for terrain and chunks
    terrain: dict = {}
    spawn: tuple = (0, 0)

    initialized = False

    # Method to initialize the world
    @staticmethod
    def initialize(worldseed: int | str, area: int) -> None:

        World.seed = worldseed
        seed(worldseed)

        World.grid = False
        World.perm = Generator.permutation()

        World.terrain = {}
        World.spawn = (0, 0)

        xp = Player.x // CHUNK_SIZE
        yp = Player.y // CHUNK_SIZE

        for chunk_x in range(xp - area, xp + area):
            for chunk_y in range(yp - area, yp + area):
                World.generate_chunk(chunk_x, chunk_y)

        Player.x, Player.y = World.spawn

        World.initialized = True


    @staticmethod
    def generate_chunk(x: int, y: int) -> None:
        if (x, y) in World.terrain:
            return

        # We generaate a empty chunk first ...
        chunk = [
            [tiles["empty"].clone()] * CHUNK_SIZE for _ in range(CHUNK_SIZE)
        ]

        # IMPORTANT:
        seed(x + y)

        for h in range(CHUNK_SIZE):
            wy = y * CHUNK_SIZE + h
            ty = wy * TERRAIN_SCALE

            for w in range(CHUNK_SIZE):
                wx = x * CHUNK_SIZE + w
                tx = wx * TERRAIN_SCALE

                elevation = Generator.perlin(World.perm, tx, ty, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)
                humidity = Generator.humidity(World.perm, tx, ty, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)
                temperature = Generator.temperature(World.perm, tx, ty, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)

                current_tile = tiles["grass"].clone()

                # Generate the ocean
                if (elevation < 0.28):
                    current_tile = tiles["ocean"].clone()

                # Generate the sea
                elif (elevation > 0.28) and (elevation < 0.42):
                    current_tile = tiles["sea"].clone()

                # Generate the beach
                elif (elevation > 0.42) and (elevation < 0.60):
                    if (temperature < 0.25):
                        current_tile = tiles["snow"].clone()
                    else:
                        current_tile = tiles["sand"].clone()

                # Generate land biomes
                elif elevation < 1.75:
                    if temperature < 0.25:  # Cold regions
                        if humidity < 0.4:
                            # Tundra / Snowlands
                            if (randint(0, 8) <= 4):
                                current_tile = tiles["frost"].clone()
                            else:
                                current_tile = tiles["snow"].clone()

                        else:
                            # Tundra forest
                            if (elevation > 0.75) and (randint(0, 8) <= 4):
                                current_tile = tiles["pine tree"].clone()
                            else:
                                current_tile = tiles["frost"].clone()


                    elif temperature < 0.5:  # Cool regions
                        if humidity < 0.4:
                            # Plains / Grasslands
                            current_tile = tiles["grass"].clone()
                            if (elevation > 0.70) and (randint(0, 8) <= 4):
                                current_tile = tiles["tall grass"].clone()

                        else:
                            if (randint(0, 8) <= 4):
                                current_tile = tiles["frost"].clone()  # Taiga
                            else:
                                current_tile = tiles["snow"].clone()


                    elif temperature < 0.75:  # Temperate regions
                        if humidity < 0.3:
                            current_tile = tiles["sand"].clone()  # Desert

                        elif humidity < 0.6:
                            # Temperate forest
                            if (elevation > 0.70) and (randint(0, 8) <= 4):
                                current_tile = tiles["birch tree"].clone()


                    elif temperature < 0.9:  # Warm regions
                        if humidity < 0.3:
                            current_tile = tiles["grass"].clone()  # Savanna

                        elif humidity < 0.6:
                            if (elevation > 0.50) and (randint(0, 16) <= 8):
                                current_tile = tiles["oak tree"].clone()

                        else:
                            if (elevation > 0.50) and (randint(0, 16) <= 8):
                                current_tile = tiles["birch tree"].clone()


                    else:  # Hot regions
                        if humidity < 0.4:
                            current_tile = tiles["sand"].clone()  # Desert
                        else:
                            if (elevation > 1.16) and (randint(0, 32) <= 16):
                                if (randint(0, 1) == 1):
                                    current_tile = tiles["oak tree"].clone()
                                else:
                                    current_tile = tiles["birch tree"].clone()
                            else:
                                current_tile = tiles["grass"].clone()  # Tropical jungle


                # Generate mountain biomes
                elif elevation < 1.95:
                    current_tile = tiles["cliff"].clone()  # Low mountain
                else:
                    current_tile = tiles["mountain"].clone()  # High mountain

                chunk[h][w] = current_tile

                # Check for spawnpoint
                if World.spawn[0] == 0 and current_tile.ID in { tiles["grass"].ID, tiles["sand"].ID }:
                    World.spawn = (wx, wy)

        World.terrain[(x, y)] = chunk


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
        time = World.daytime()
        if (time < 3000):
            return int(32 + ((time / 3000) * 223))
        elif (time < 16000):
            return 255
        elif (time < 18000):
            return int(255 - (((time - 16000) / 2000) * 23))
        else:
            return 32


    @staticmethod
    def render() -> None:
        offset_x: int = SCREEN_HALF_W - (Player.x % CHUNK_SIZE) * TILE_SIZE
        offset_y: int = SCREEN_HALF_H - (Player.y % CHUNK_SIZE) * TILE_SIZE

        sprites: list = []

        if Updater.time % 6 == 0:
            overlay.set_alpha(255 - World.daylight())

        player_chunk_x = Player.cx
        player_chunk_y = Player.cy

        for x in range(-(RENDER_RANGE_H + 1), RENDER_RANGE_H + 2):
            wx_base = x * CHUNK_SIZE * TILE_SIZE + offset_x

            for y in range(-RENDER_RANGE_V, RENDER_RANGE_V + 1):
                wy_base = y * CHUNK_SIZE * TILE_SIZE + offset_y

                chunk_coord = (player_chunk_x + x, player_chunk_y + y)
                chunk = World.terrain.get(chunk_coord)

                if chunk is None:
                    World.load_chunk(*chunk_coord)
                    chunk = World.terrain.get(chunk_coord)
                    if chunk is None:
                        continue

                for tile_y in range(CHUNK_SIZE):
                    wy = wy_base + tile_y * TILE_SIZE
                    if wy < 0 or wy >= SCREEN_FULL_H:
                        continue

                    for tile_x in range(CHUNK_SIZE):
                        wx = wx_base + tile_x * TILE_SIZE
                        if wx < 0 or wx >= SCREEN_FULL_W:
                            continue

                        tile: Tile = chunk[tile_y][tile_x]
                        sprites.append((tile.render(), (wx, wy)))

        sprites.append((overlay, (0, 0)))

        # Render all sprites at once
        screen.fblits(sprites)

        if World.grid:
            for x in range(-(RENDER_RANGE_H + 1), RENDER_RANGE_H + 2):
                base_chunk_x_draw = x * CHUNK_SIZE * TILE_SIZE + offset_x

                for y in range(-RENDER_RANGE_V, RENDER_RANGE_V + 1):
                    base_chunk_y_draw = y * CHUNK_SIZE * TILE_SIZE + offset_y

                    # Calculate the neighbors chunks
                    neighbors = [
                        (player_chunk_x + x - 1, player_chunk_y + y),
                        (player_chunk_x + x + 1, player_chunk_y + y),
                        (player_chunk_x + x, player_chunk_y + y - 1),
                        (player_chunk_x + x, player_chunk_y + y + 1)
                    ]

                    # We check if all the neighbors are generated
                    all_neighbors_generated = all(chunk in World.terrain for chunk in neighbors)

                    # We calculate the chunk position on screen
                    chunk_rect = pygame.Rect(base_chunk_x_draw, base_chunk_y_draw, (CHUNK_SIZE * TILE_SIZE), (CHUNK_SIZE * TILE_SIZE))

                    # Determines the rectangle color
                    if (player_chunk_x + x, player_chunk_y + y) == (player_chunk_x, player_chunk_y):
                        pygame.draw.rect(screen, Color.MAGENTA, chunk_rect, 2)
                        pygame.draw.rect(screen, Color.BLACK, chunk_rect.inflate(-2, -2), 2)
                    elif not all_neighbors_generated:
                        pygame.draw.rect(screen, Color.RED, chunk_rect, 2)
                        pygame.draw.rect(screen, Color.BLACK, chunk_rect.inflate(-2, -2), 2)
                    else:
                        pygame.draw.rect(screen, Color.GREEN, chunk_rect, 2)
                        pygame.draw.rect(screen, Color.BLACK, chunk_rect.inflate(-2, -2), 2)


    @staticmethod
    def tick() -> None:
        """ Update chunks around the player's position """

        # Define the range of chunks to update based on the player's position
        x_range = range(Player.cx - 3, Player.cx + 4)
        y_range = range(Player.cy - 3, Player.cy + 4)

        # Iterate through the defined range of chunks
        for chunk_x in x_range:
            for chunk_y in y_range:
                # Update each chunk within the range
                World.update_chunk(chunk_x, chunk_y)


    @staticmethod
    def update_chunk(cx: int, cy: int) -> None:

        # Check if it's time to spread grass
        if (Updater.time % 32 == 0):
            if (randint(0, 16) == 8):
                World.update_tiles(
                    cx, cy,              # The chunk to update
                    tiles["dirt"],       # The tile to replace
                    tiles["grass"],      # The tile to replace with

                    # Tiles that can influence the replacement
                    [
                        tiles["grass"],
                        tiles["tall grass"]
                    ]
                )

        # Check if it's time to spread water
        if Updater.time % 8 == 0:
            World.update_tiles(
                cx, cy,              # The chunk to update
                tiles["hole"],       # The tile to replace
                tiles["river"],      # The tile to replace with

                # Tiles that can influence the replacement
                [
                    tiles["ocean"],
                    tiles["sea"],
                    tiles["river"]
                ]
            )


    @staticmethod
    def update_tiles(cx: int, cy: int, tile_target: Tile, replacement: Tile, influence_tiles: List[Tile]) -> None:
        this_chunk = World.terrain.get((cx, cy))

        if this_chunk:
            target = tile_target.ID
            replace = replacement.clone()

            # Create a copy of the chunk
            temp_chunk = [
                row[:] for row in this_chunk
            ]

            # Iterate through each tile in the chunk
            for yt in range(CHUNK_SIZE):
                for xt in range(CHUNK_SIZE):

                    # Check if the current tile matches the target tile
                    if this_chunk[yt][xt].ID == target:
                        # If influence_tiles is provided, check surrounding tiles
                        if World.tile_around(influence_tiles, xt, yt, cx, cy):
                            # Replace the target tile with the new tile
                            temp_chunk[yt][xt] = replace

            # Update the terrain with the modified chunk if changes were made
            if temp_chunk != this_chunk:
                World.terrain[(cx, cy)] = temp_chunk


    @staticmethod
    def tile_around(tiles_around: List[Tile], x: int, y: int, chunk_x: int, chunk_y: int) -> bool:
        """ Check if any of the specified tiles are around the given coordinates """

        # Define the directions to check around the given coordinates
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Check each direction for matching tiles
        for dy, dx in directions:
            new_y = (y + dy) % CHUNK_SIZE
            new_x = (x + dx) % CHUNK_SIZE
            new_chunk_x = chunk_x + (x + dx) // CHUNK_SIZE
            new_chunk_y = chunk_y + (y + dy) // CHUNK_SIZE

            # Retrieve the adjacent chunk from the terrain
            around_chunk = World.terrain.get((new_chunk_x, new_chunk_y))

            # Check if any adjacent tile matches the specified tile types
            if around_chunk:
                if around_chunk[new_y][new_x].ID in [tile.ID for tile in tiles_around]:
                    return True

        return False



class Player:
    # Player's world coordinates
    x: int = 0
    y: int = 0

    # Player's local chunk position
    cx: int = 0
    cy: int = 0

    # Player's stamina which decreases when player breaks a tile
    energy: int = PLAYER_MAX_ENERGY

    # Player's health which decreases when player gets damaged
    health: int = PLAYER_MAX_HEALTH

    # The direction where the player is facing
    facing = "w"

    cursor_blink: bool = False

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
        Player.facing = direction

        return not World.get_tile(xd, yd).solid


    @staticmethod
    def break_tile(direction: str) -> None:
        """ Break the tile in the specified direction """

        xd, yd = Player.coordinates(direction, Player.x, Player.y)
        Player.facing = direction

        if Player.energy >= int(0.32 * PLAYER_MAX_ENERGY):
            Player.energy = int(max(0, Player.energy - 0.32 * PLAYER_MAX_ENERGY))
            World.get_tile(xd, yd).hurt(xd, yd, 8)


    @staticmethod
    def render() -> None:
        # Adjust the player's x and y coordinates based on the direction
        xd, yd = Player.coordinates(Player.facing, Player.x, Player.y)

        # Calculate the position of the tile in front of the player
        tile_target_x = xd - Player.x
        tile_target_y = yd - Player.y

        # Calculate the screen coordinates of the tile in front of the player
        front_tile_x = SCREEN_HALF_W + (tile_target_x * TILE_SIZE)
        front_tile_y = SCREEN_HALF_H + (tile_target_y * TILE_SIZE)

        # Create a list to hold all the blits
        sprites: list = []

        # Then we draw the player at the center of the screen
        sprites.append((tiles["player"].render(), (SCREEN_HALF_W + 4, SCREEN_HALF_H)))

        tile_image = World.get_tile(xd, yd).render()

        # Highlight the front tile
        if not Player.cursor_blink:
            tile_high = tile_image.copy()
            tile_color = World.get_tile(xd, yd).background
            tile_high.fill((tile_color[0] * 3, tile_color[1] * 3, tile_color[2] * 3), special_flags=pygame.BLEND_RGB_ADD)
            sprites.append((tile_high, (front_tile_x, front_tile_y)))

        # Use blits to draw all the images at once
        screen.fblits(sprites)


    @staticmethod
    def tick() -> None:
        # This function gets called every frame, hence we can use it to
        # decrease or regenerate the stamina or the health of the player

        Player.cx = Player.x // CHUNK_SIZE
        Player.cy = Player.y // CHUNK_SIZE


        if (Updater.time % 15 == 0):
            # Decrease stamina if we are swiming
            if( Player.energy > 0) and Player.is_swimming():
                Player.energy = max(0, Player.energy - 1)

            # Increase health if stamina is higher than half
            if (Player.energy > 10):
                Player.health = min(PLAYER_MAX_HEALTH, Player.health + 1)

            Player.cursor_blink = not Player.cursor_blink


        if (Updater.time % 30 == 0) and (Player.energy < 1):
            if Player.is_swimming():
                Player.health = max(0, Player.health - 1)
                Sound.play("playerHurt")


        if (Updater.time % 3 == 0) and (Player.energy < PLAYER_MAX_ENERGY):
            if not Player.is_swimming():
                Player.energy = min(PLAYER_MAX_ENERGY, Player.energy + 1)


class Updater:
    time = 0
    timer = 4


    @staticmethod
    def update() -> None:

        if not World.initialized:
            title_menu.tick(World)
            return

        # This function counts the elapsed time (in frames) and then it moves
        # the player or breaks the tile in front of the player if certain keys are being pressed
        # In addition to that, it also updates the chunks in the world.
        key = pygame.key.get_pressed()


        # If the player is swiming, decrease the speed
        if Player.is_swimming():
            Updater.timer = 8
        else:
            Updater.timer = 4


        if (Updater.time % Updater.timer == 0):
            if key[pygame.K_UP] and Player.can_move('w'): Player.y -= 1
            if key[pygame.K_LEFT] and Player.can_move('a'): Player.x -= 1
            if key[pygame.K_DOWN] and Player.can_move('s'): Player.y += 1
            if key[pygame.K_RIGHT] and Player.can_move('d'): Player.x += 1

            if key[pygame.K_c]:
                Player.break_tile(Player.facing)


            if key[pygame.K_LSHIFT]:
                # Toggle chunks grid
                if key[pygame.K_g]:
                    World.grid = not World.grid

                # Save world
                if key[pygame.K_s]:
                    Saveload.save_world()
                    Sound.play("eventSound")

                # Load world
                if key[pygame.K_l]:
                    Saveload.load_world()
                    Sound.play("eventSound")


            # Move the player to the spawn
            if key[pygame.K_r]:
                Player.x, Player.y = World.spawn
                Sound.play("spawnSound")

            # Move the player to the farlands
            if key[pygame.K_f]:
                Player.x += (sys.maxsize ** 16)


        World.tick()
        Player.tick()


class Screen:

    HOTBAR_LENGTH = SCREEN_FULL_W // 8
    BORDER_HEIGHT = SCREEN_FULL_H - 34
    HEARTS_HEIGHT = SCREEN_FULL_H - 32
    STAMINA_HEIGHT = SCREEN_FULL_H - 16

    HOTBAR_BORDERLINE = text.render("¯", False, Color.WHITE, Color.BLACK).convert()
    HOTBAR_L_BRACKET = text.render("[", False, (32, 32, 32), Color.BLACK).convert()
    HOTBAR_R_BRACKET = text.render("]", False, (32, 32, 32), Color.BLACK).convert()
    HOTBAR_BACKGROUND = text.render(" ", False, Color.BLACK, Color.BLACK).convert()
    HEART_NONE = text.render("♥", False, (16, 16, 16)).convert()
    HEART_FULL = text.render("♥", False, Color.RED).convert()
    STAMINA_NONE = text.render("○", False, (16, 16, 16)).convert()
    STAMINA_FULL = text.render("●", False, Color.YELLOW).convert()


    @staticmethod
    def hotbar() -> None:
        sprites = []

        hotbar_sprites = [
            (Screen.HOTBAR_BORDERLINE, Screen.BORDER_HEIGHT),
            (Screen.HOTBAR_BACKGROUND, Screen.HEARTS_HEIGHT),
            (Screen.HOTBAR_BACKGROUND, Screen.STAMINA_HEIGHT)
        ]

        sprites += [(sprite[0], (i * 8, sprite[1])) for sprite in hotbar_sprites for i in range(Screen.HOTBAR_LENGTH)]

        xp_text = f"X: {Player.x}"
        yp_text = f"Y: {Player.y}"

        xp = text.render(xp_text, True, (32, 32, 32), Color.BLACK).convert()
        yp = text.render(yp_text, True, (32, 32, 32), Color.BLACK).convert()

        xp_pos = ((Screen.HOTBAR_LENGTH * 8) - 32 - (len(xp_text) * 8), Screen.HEARTS_HEIGHT)
        yp_pos = ((Screen.HOTBAR_LENGTH * 8) - 32 - (len(yp_text) * 8), Screen.STAMINA_HEIGHT)

        sprites.append((xp, xp_pos))
        sprites.append((yp, yp_pos))

        bracket_positions = [
            (8, Screen.HEARTS_HEIGHT + 1), (176, Screen.HEARTS_HEIGHT + 1),
            (8, Screen.STAMINA_HEIGHT - 1), (176, Screen.STAMINA_HEIGHT - 1)
        ]

        sprites += [(Screen.HOTBAR_L_BRACKET if i % 2 == 0 else Screen.HOTBAR_R_BRACKET, pos) for i, pos in enumerate(bracket_positions)]

        sprites += [(Screen.HEART_FULL if i < Player.health else Screen.HEART_NONE, (16 + (i * 8), Screen.HEARTS_HEIGHT + 1)) for i in range(20)]
        sprites += [(Screen.STAMINA_FULL if i < Player.energy else Screen.STAMINA_NONE, (16 + (i * 8), Screen.STAMINA_HEIGHT - 1)) for i in range(20)]

        screen.fblits(sprites)


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
                'energy': Player.energy,
                'health': Player.health,
                'facing': Player.facing
            },
            'WorldSeed': World.seed,
            'WorldPerm': World.perm,
            'WorldSpawn': World.spawn,
            'GameTime': Updater.time,
            'Terrain': World.terrain
        }

        with gzip.open('./saves/world.dat', 'wb') as file:
            pickle.dump(world_data, file, protocol=5)


    @staticmethod
    def load_world() -> None:
        with gzip.open('./saves/world.dat', 'rb') as file:
            world_data = pickle.load(file)

        player_data = world_data['Player']
        Player.x = player_data['x']
        Player.y = player_data['y']
        Player.energy = player_data['energy']
        Player.health = player_data['health']
        Player.facing = player_data['facing']

        World.seed = world_data['WorldSeed']
        World.perm = world_data['WorldPerm']
        World.spawn = world_data['WorldSpawn']
        Updater.time = world_data['GameTime']

        World.terrain = world_data['Terrain']

        World.initialized = True


def main() -> None:

    try:
        Saveload.load_world()
        Sound.play("eventSound")
    except FileNotFoundError:
        World.initialized = False

    last_time = time_ns()
    unprocessed = 0
    ns_per_tick = 1e9 / FRAMES_PER_SEC
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

            if (World.initialized):
                Updater.time += 1

            Updater.update()
            unprocessed -= 1
            should_render = True

        clock.tick(FRAMES_PER_SEC)

        if should_render:
            if (World.initialized):
                Screen.update()
            else:
                title_menu.render()

        if time() - last_timer > 1:
            last_timer += 1

            print(
                f"- FPS: {clock.get_fps():.1f} "
                f"({ticks} TPS) "
            #    f"({World.daytime()} daytime) "
            #    f"({World.daylight()} daylight)"
            )

            ticks = 0

    pygame.quit()


if __name__ == "__main__":
    main()
