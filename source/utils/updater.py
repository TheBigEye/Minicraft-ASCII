from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from source.sound import Sound
from source.utils.saveload import Saveload
from source.game import Game

if TYPE_CHECKING:
    from source.core.player import Player
    from source.core.world import World


class Updater:

    def __init__(self, world: World, player: Player):
        self.ticks = 0
        self.timer = 4
        self.world = world
        self.player = player

    def update(self) -> None:

        # This function counts the elapsed time (in frames) and then it moves
        # the player or breaks the tile in front of the player if certain keys are being pressed
        # In addition to that, it also updates the chunks in the world.
        event = pygame.key.get_pressed()

        # If the player is swiming, decrease the speed
        if self.player.swimming():
            self.timer = 8
        else:
            self.timer = 4

        if (self.ticks % self.timer == 0):
            if event[pygame.K_UP]:
                self.player.move(self.player.x, self.player.y - 1)
            elif event[pygame.K_DOWN]:
                self.player.move(self.player.x, self.player.y + 1)

            if event[pygame.K_LEFT]:
                self.player.move(self.player.x - 1, self.player.y)
            elif event[pygame.K_RIGHT]:
                self.player.move(self.player.x + 1, self.player.y)

            if event[pygame.K_c]:
                self.player.attack()

            elif event[pygame.K_LSHIFT]:
                # Toggle chunks grid
                if event[pygame.K_g]:
                    Game.debug = not Game.debug

                # Save world
                if event[pygame.K_s]:
                    Saveload.save(self, self.world, self.player)
                    Sound.play("eventSound")

                # Load world
                elif event[pygame.K_l]:
                    Saveload.load(self, self.world, self.player)
                    Sound.play("eventSound")

                # Move the player to the spawn
                elif event[pygame.K_r]:
                    self.player.move(self.world.sx, self.world.sy)
                    Sound.play("spawnSound")

        self.world.update(self.ticks)
        self.player.update(self.ticks)

        self.ticks += 1
