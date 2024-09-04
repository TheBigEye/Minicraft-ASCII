from __future__ import annotations

from math import cos, radians, sin
from random import randint, seed
from typing import TYPE_CHECKING

from pygame import Surface

from source.core.mob import mobs
from source.core.perlin import Perlin
from source.core.tile import fluids, tiles
from source.game import Game
from source.utils.constants import *

if TYPE_CHECKING:
    from source.core.mob import Mob
    from source.core.player import Player
    from source.core.tile import Tile


class World:

    def __init__(self, player: Player) -> None:
        self.seed = None  # Seed for terrain generation
        self.perm: list = []  # Permutation matrix for noise generation

        # Storage for terrain and chunks
        self.chunks: dict = {}
        self.entities: list = []
        self.ticks: int = 0

        # Spawn point
        self.sx = 0
        self.sy = 0

        self.player = player
        self.loaded = False


    def initialize(self, worldseed) -> None:
        self.seed = worldseed
        seed(self.seed)

        self.perm = Perlin.permutation()

        xp = self.player.x // CHUNK_SIZE
        yp = self.player.y // CHUNK_SIZE

        for cx in range((xp - 3), (xp + 3)):
            for cy in range((yp - 3), (yp + 3)):
                self.load_chunk(cx, cy)

        self.player.initialize(self, self.sx, self.sy)

        self.loaded = True


    def load_chunk(self, x: int, y: int) -> None:

        if (x, y) in self.chunks:
            return

        # We generaate a empty chunk first ...
        chunk = [
            [tiles["empty"].clone()] * CHUNK_SIZE for _ in range(CHUNK_SIZE)
        ]

        for h in range(CHUNK_SIZE):
            wy = y * CHUNK_SIZE + h
            ty = wy * TERRAIN_SCALE

            for w in range(CHUNK_SIZE):
                wx = x * CHUNK_SIZE + w
                tx = wx * TERRAIN_SCALE

                elevation = Perlin.heightmap(self.perm, tx, ty, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)
                humidity = Perlin.humidity(self.perm, tx, ty, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)
                temperature = Perlin.temperature(self.perm, tx, ty, TERRAIN_PERSISTENCE, TERRAIN_OCTAVES)

                current_tile = tiles["grass"].clone()

                # Generate the ocean
                if (elevation < 0.28):
                    current_tile = tiles["ocean"].clone()

                elif (elevation > 0.28) and (elevation < 0.32):
                    if (temperature < 0.25):
                        current_tile = tiles["iceberg"].clone()
                    else:
                        current_tile = tiles["ocean"].clone()

                # Generate the sea
                elif (elevation > 0.32) and (elevation < 0.42):
                    if (temperature < 0.25):
                        current_tile = tiles["ice"].clone()
                    else:
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
                            if (elevation > 0.75) and (randint(0, 16) <= 4):
                                current_tile = tiles["pine tree"].clone()
                            else:
                                current_tile = tiles["frost"].clone()


                    elif temperature < 0.5:  # Cool regions
                        if humidity > 0.4:
                            # Plains / Grasslands
                            if (elevation > 0.70) and (randint(0, 8) <= 4):
                                current_tile = tiles["tallgrass"].clone()
                            else:
                                current_tile = tiles["grass"].clone() # Snowy grass
                        else:
                            if (randint(0, 8) <= 4):
                                current_tile = tiles["frost"].clone() # Snowy tallgrass
                            else:
                                current_tile = tiles["snow"].clone() # Snowy grass


                    elif temperature < 0.70:  # Temperate regions
                        if humidity > 0.4:
                            # Temperate forest
                            if (elevation > 0.50) and (randint(0, 16) <= 4):
                                current_tile = tiles["oak tree"].clone()


                    elif temperature < 0.9:  # Warm regions
                        if humidity < 0.3:
                            current_tile = tiles["sand"].clone()  # Savanna

                        elif (humidity > 0.3) and (humidity < 0.5):
                            current_tile = tiles["grass"].clone()  # Plains

                        else:
                            if (elevation > 0.60) and (randint(0, 32) <= 8):
                                if (randint(0, 1) == 1):
                                    current_tile = tiles["oak tree"].clone()
                                else:
                                    current_tile = tiles["birch tree"].clone()


                    else:  # Hot regions
                        if humidity < 0.4:
                            current_tile = tiles["sand"].clone()  # Desert

                        elif (humidity > 0.4) and (humidity < 0.6):
                            current_tile = tiles["grass"].clone()  # Plains

                        else:
                            if (elevation > 0.60) and (randint(0, 32) <= 8):
                                if (randint(0, 1) == 1):
                                    current_tile = tiles["oak tree"].clone()
                                else:
                                    current_tile = tiles["birch tree"].clone()


                # Generate mountain biomes
                elif elevation < 1.95:
                    current_tile = tiles["stone"].clone()  # Low mountain
                else:
                    current_tile = tiles["gravel"].clone()  # High mountain

                chunk[h][w] = current_tile

                # Check for spawnpoint
                if (self.sx == 0 and self.sy == 0):
                    if current_tile.id in { tiles["grass"].id, tiles["sand"].id, tiles["snow"].id }:
                        self.sx = wx
                        self.sy = wy


        self.chunks[(x, y)] = chunk


    def get_tile(self, x: int, y: int) -> Tile:
        """ Get the character at coordinates in the world """
        # Calculate the chunk coordinates
        cx = x // CHUNK_SIZE
        cy = y // CHUNK_SIZE

        # Load the chunk at the calculated chunk coordinates
        self.load_chunk(cx, cy)

        # Calculate the local coordinates within the chunk
        ly = y % CHUNK_SIZE
        lx = x % CHUNK_SIZE

        # Return the tile at the calculated local coordinates in the world
        return self.chunks[(cx, cy)][ly][lx]


    def set_tile(self, x: int, y: int, tile: int | Tile) -> None:
        """ Update the world map with the replacement tile, either by Tile object or tile ID """
        # Calculate the chunk coordinates
        cx = x // CHUNK_SIZE
        cy = y // CHUNK_SIZE

        # Load the chunk at the calculated chunk coordinates
        self.load_chunk(cx, cy)

        # Calculate the local coordinates within the chunk
        ly = y % CHUNK_SIZE
        lx = x % CHUNK_SIZE

        # Determine the correct Tile object
        if isinstance(tile, int):
            tile = tiles[Game.tile[tile]].clone()
        else:
            tile = tile.clone()

        # Set the tile in the terrain
        self.chunks[(cx, cy)][ly][lx] = tile


    def spawn_mob(self, x: int, y: int, mob: Mob) -> None:
        """ Create and add a new mob to the world """

        # Limitar el número máximo de mobs
        if len(self.entities) > 16:
            return

        # Obtener la tile solo una vez para evitar llamadas repetidas
        tile = self.get_tile(x, y)

        # Verificar si la tile es adecuada para spawnear el mob
        if tile.id in fluids or tile.solid:
            return

        # Asignar las coordenadas al mob y añadirlo al mundo
        mob.x = x
        mob.y = y

        self.entities.append(mob)


    def despawn_mob(self, x: int, y: int) -> None:
        """ Create and add a new mob to the world """

        for mob in self.entities:
            if (mob.x == x) and (mob.y == y):
                self.entities.remove(mob)
                return


    # FIX FIX THIS SHIT: optimize this
    def daylight(self) -> int:
        if (self.ticks < 3000):
            return int(16 + ((self.ticks / 3000) * 239))
        elif (self.ticks < 16000):
            return 255
        elif (self.ticks < 18000):
            return int(255 - (((self.ticks - 16000) / 2000) * 239))
        else:
            return 16


    def render(self, screen: Surface) -> None:
        sprites: list = []

        xo: int = SCREEN_HALF_W - (self.player.x % CHUNK_SIZE) * TILE_SIZE
        yo: int = SCREEN_HALF_H - (self.player.y % CHUNK_SIZE) * TILE_SIZE

        for x in range(-(RENDER_RANGE_H + 1), RENDER_RANGE_H + 2):
            xr = x * CHUNK_SIZE * TILE_SIZE + xo

            for y in range(-RENDER_RANGE_V, RENDER_RANGE_V + 1):
                yr = y * CHUNK_SIZE * TILE_SIZE + yo

                chunk_coord = (self.player.cx + x, self.player.cy + y)
                chunk = self.chunks.get(chunk_coord)

                if chunk is None:
                    self.load_chunk(*chunk_coord)
                    chunk = self.chunks.get(chunk_coord)
                    if chunk is None:
                        continue

                for yt in range(CHUNK_SIZE):
                    wy = yr + yt * TILE_SIZE
                    if wy < 0 or wy >= SCREEN_FULL_H:
                        continue

                    for xt in range(CHUNK_SIZE):
                        wx = xr + xt * TILE_SIZE
                        if wx < 0 or wx >= SCREEN_FULL_W:
                            continue

                        tile: Tile = chunk[yt][xt]
                        sprites.append((tile.sprite, (wx, wy)))


        # Filtrar y renderizar solo los mobs dentro del área de renderizado
        for mob in self.entities:
            xo = SCREEN_HALF_W + (mob.x - self.player.x) * TILE_SIZE
            yo = SCREEN_HALF_H + (mob.y - self.player.y) * TILE_SIZE

            # Verifica si el mob está dentro del área visible de la pantalla
            if 0 <= xo < SCREEN_FULL_W and 0 <= yo < SCREEN_FULL_H:
                sprites.append((mob.sprite, (xo + 4, yo)))


        # Render all sprites at once
        screen.fblits(sprites)


    def update(self, ticks) -> None:
        """ Update chunks around the player's position """

        self.ticks = ticks % 24000

        rx = range(self.player.cx - 3, self.player.cx + 4)
        ry = range(self.player.cy - 3, self.player.cy + 4)

        if ticks % 4 == 0:
            spawn_distance = randint(8, 16) * TILE_SIZE
            angle = randint(0, 359)

            rad_angle = radians(angle)
            cos_angle = cos(rad_angle) * spawn_distance
            sin_angle = sin(rad_angle) * spawn_distance

            if randint(0, 1) == 0:
                sx = int(self.player.x + cos_angle)
            else:
                sx = int(self.player.x - cos_angle)

            if randint(0, 1) == 0:
                sy = int(self.player.y + sin_angle)
            else:
                sy = int(self.player.y - sin_angle)

            if not any((mob.x == sx) and (mob.y == sy) for mob in self.entities):
                self.spawn_mob(sx, sy, mobs["pig"].clone())

        # Iterate through the defined range of chunks
        for cx in rx:
            for cy in ry:
                # Update each chunk within the range
                if ticks % 32 == 0:
                    if (randint(0, 8) == 4):
                        self.update_tiles(
                            cx, cy,              # The chunk to update
                            tiles["dirt"],       # The tile to replace
                            tiles["grass"],      # The tile to replace with

                            # Tiles that can influence the replacement
                            [
                                tiles["grass"],
                                tiles["tallgrass"]
                            ]
                        )

                # Check if it's time to spread water
                if ticks % 8 == 0:
                    self.update_tiles(
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

        if (ticks % 4 == 0):
            for mob in self.entities:
                if randint(0, 8) == 4:
                    mob.move(self)


    def update_tiles(self, cx: int, cy: int, tile_target: Tile, parent: Tile, influences: list) -> None:
        this_chunk = self.chunks.get((cx, cy))

        if this_chunk:
            target = tile_target.id
            replace = parent.clone()

            # Create a copy of the chunk
            temp_chunk = [
                row[:] for row in this_chunk
            ]

            # Iterate through each tile in the chunk
            for yt in range(CHUNK_SIZE):
                for xt in range(CHUNK_SIZE):

                    # Check if the current tile matches the target tile
                    if this_chunk[yt][xt].id == target:
                        # If influence_tiles is provided, check surrounding tiles
                        if self.tiles_around(influences, xt, yt, cx, cy):
                            # Replace the target tile with the new tile
                            temp_chunk[yt][xt] = replace

            # Update the terrain with the modified chunk if changes were made
            if temp_chunk != this_chunk:
                self.chunks[(cx, cy)] = temp_chunk


    def tiles_around(self, tiles_around: list, x: int, y: int, cx: int, cy: int) -> bool:
        """ Check if any of the specified tiles are around the given coordinates """

        # Define the directions to check around the given coordinates
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Check each direction for matching tiles
        for dy, dx in directions:
            new_y = (y + dy) % CHUNK_SIZE
            new_x = (x + dx) % CHUNK_SIZE
            new_chunk_x = cx + (x + dx) // CHUNK_SIZE
            new_chunk_y = cy + (y + dy) // CHUNK_SIZE

            # Retrieve the adjacent chunk from the terrain
            around_chunk = self.chunks.get((new_chunk_x, new_chunk_y))

            # Check if any adjacent tile matches the specified tile types
            if around_chunk:
                if around_chunk[new_y][new_x].id in [tile.id for tile in tiles_around]:
                    return True

        return False
