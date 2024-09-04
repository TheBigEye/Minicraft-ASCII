from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Surface

from source.core.tile import fluids
from source.game import Game
from source.screen.debug import Debug
from source.sound import Sound
from source.utils.constants import *

if TYPE_CHECKING:
    from source.core.world import World

class Player:

    def __init__(self) -> None:
        # Player's world coordinates
        self.x: int = 0
        self.y: int = 0

        # Player's local chunk position
        self.cx: int = 0
        self.cy: int = 0

        # Player max health, stamina and hunger
        self.MAX_STAT: int = 20

        self.health: int = self.MAX_STAT
        self.energy: int = self.MAX_STAT
        self.hunger: int = self.MAX_STAT

        # The direction where the player is facing
        self.facing: tuple = (0, 0)
        self.cursor: bool = False
        self.world: World = None

        self.sprite = Game.sprite("☻", (000, 255, 255), 0)


    def initialize(self, world: World, sx: int, sy: int) -> None:
        self.world = world
        self.move(sx, sy)


    def swimming(self) -> bool:
        # Check if the player is swimming (in water)
        return self.world.get_tile(self.x, self.y).id in fluids


    def move(self, mx, my) -> None:
        """ Move the player"""

        # Get the diff
        fx = mx - self.x
        fy = my - self.y

        if not self.world.get_tile(mx, my).solid:
            self.x = mx
            self.y = my

        # Set the facing direction based on movement
        if fx != 0:
            self.facing = (self.x + fx, self.y)
        elif fy != 0:
            self.facing = (self.x, self.y + fy)


    def attack(self) -> None:
        """ Break the tile in the specified direction """

        if self.energy < int(0.32 * self.MAX_STAT):
            return

        xd = self.facing[0]
        yd = self.facing[1]

        self.energy = max(0, self.energy - int(0.32 * self.MAX_STAT))

        for mob in self.world.entities:
            if (mob.x == xd) and (mob.y == yd):
                mob.hurt(self.world, 8)
                return

        tile = self.world.get_tile(xd, yd)
        tile.hurt(self.world, xd, yd, 8)


    def render(self, screen: Surface) -> None:
        # Create a list to hold all the blits
        sprites: list = []

        # Highlight the front tile
        if self.cursor:
            # NOTE: Pygame blit will fail if the player are in
            # extremes distances from the world spawn point!

            xd = self.facing[0]
            yd = self.facing[1]

            # Calculate the screen coordinates of the tile in front of the player
            facing_tile = (
                SCREEN_HALF_W + ((xd - self.x) * TILE_SIZE),
                SCREEN_HALF_H + ((yd - self.y) * TILE_SIZE)
            )

            highlight = self.world.get_tile(xd, yd).sprite.copy()
            highlight.fill((16, 16, 16), None, pygame.BLEND_RGB_ADD)
            sprites.append((highlight, facing_tile))

        sx = SCREEN_HALF_W + 4
        sy = SCREEN_HALF_H

        # Then we draw the player at the center of the screen
        sprites.append((self.sprite, (sx, sy)))

        # We add the player light overlay
        Game.darkness.blit(Game.overlay, (sx - 96, sy - 92), special_flags=pygame.BLEND_RGBA_SUB)
        Game.darkness.set_alpha(255 - self.world.daylight())

        sprites.append((Game.darkness, (0, 0)))

        # Use fblits to draw all the surfaces at once
        screen.fblits(sprites)

        if Game.debug:
            Debug.render(
                screen,
                self.world.chunks,
                self.x, self.y,
                self.cx, self.cy
            )


    def update(self, ticks: int) -> None:
        # This function gets called every frame, hence we can use it to
        # decrease or regenerate the stamina or the health of the player

        self.cx = self.x // CHUNK_SIZE
        self.cy = self.y // CHUNK_SIZE

        if (ticks % 15 == 0):
            # Decrease stamina if we are swiming
            if (self.energy > 0) and self.swimming():
                self.energy = max(0, self.energy - 1)

            # Increase health if stamina is higher than half
            if (self.energy > 10):
                self.health = min(self.MAX_STAT, self.health + 1)

            self.cursor = not self.cursor


        if (ticks % 30 == 0) and (self.energy < 1):
            if self.swimming():
                self.health = max(0, self.health - 1)
                Sound.play("playerHurt")


        if (ticks % 3 == 0) and (self.energy < self.MAX_STAT):
            if not self.swimming():
                self.energy = min(self.MAX_STAT, self.energy + 1)
