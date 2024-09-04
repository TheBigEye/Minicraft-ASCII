from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Font, Surface

from source.utils.constants import *
from source.screen.screen import Color

if TYPE_CHECKING:
    from source.core.world import Player


class Hotbar:

    def __init__(self, player: Player, font: Font) -> None:
        self.font: Font = font
        self.player: Player = player

        self.px: str = ""
        self.py: str = ""

        self.px_pos: tuple = (0, 0)
        self.py_pos: tuple = (0, 0)

        # TODO: Optimize this :(
        self.HOTBAR_LENGTH: int = SCREEN_FULL_W // 8
        self.BORDER_HEIGHT: int = SCREEN_FULL_H - 34
        self.HEARTS_HEIGHT: int = SCREEN_FULL_H - 32
        self.STAMINA_HEIGHT: int = SCREEN_FULL_H - 16

        self.BORDERLINE = font.render("¯", False, Color.WHITE, Color.BLACK).convert()
        self.BACKGROUND = font.render(" ", False, Color.BLACK, Color.BLACK).convert()

        self.L_BRACKET = font.render("[", False, Color.DARK_GREY, Color.BLACK).convert()
        self.R_BRACKET = font.render("]", False, Color.DARK_GREY, Color.BLACK).convert()

        self.HEART_NONE = font.render("♥", False, (16, 16, 16)).convert()
        self.HEART_FULL = font.render("♥", False, Color.RED).convert()
        self.STAMINA_NONE = font.render("○", False, (16, 16, 16)).convert()
        self.STAMINA_FULL = font.render("●", False, Color.YELLOW).convert()

        self.SPRITES = [
            (self.BORDERLINE, self.BORDER_HEIGHT),
            (self.BACKGROUND, self.HEARTS_HEIGHT),
            (self.BACKGROUND, self.STAMINA_HEIGHT)
        ]

        self.BRACKETS_POS = [
            (8, self.HEARTS_HEIGHT + 1), (176, self.HEARTS_HEIGHT + 1),
            (8, self.STAMINA_HEIGHT - 1), (176, self.STAMINA_HEIGHT - 1)
        ]


    def update(self) -> None:
        self.px = f"X: {self.player.x}"
        self.py = f"Y: {self.player.y}"

        self.px_pos = ((self.HOTBAR_LENGTH * 8) - 32 - (len(self.px) * 8), self.HEARTS_HEIGHT)
        self.py_pos = ((self.HOTBAR_LENGTH * 8) - 32 - (len(self.py) * 8), self.STAMINA_HEIGHT)


    def render(self, screen: Surface) -> None:
        sprites: list = []

        # Add the border, background for hearts, and background for stamina
        sprites += [
            (sprite[0], (i * 8, sprite[1]))
            for sprite in self.SPRITES
            for i in range(self.HOTBAR_LENGTH)
        ]

        # Render player coordinates
        xp = self.font.render(self.px, False, Color.DARK_GREY, Color.BLACK).convert()
        yp = self.font.render(self.py, False, Color.DARK_GREY, Color.BLACK).convert()

        # Add coordinates to sprites list
        sprites.append((xp, self.px_pos))
        sprites.append((yp, self.py_pos))

        # Add hearts (full or empty based on player health)
        sprites += [
            (self.HEART_FULL if i < self.player.health else self.HEART_NONE, (16 + (i * 8), self.HEARTS_HEIGHT + 1))
            for i in range(20)
        ]

        # Add stamina (full or empty based on player energy)
        sprites += [
            (self.STAMINA_FULL if i < self.player.energy else self.STAMINA_NONE, (16 + (i * 8), self.STAMINA_HEIGHT - 1))
            for i in range(20)
        ]

        # Draw all sprites onto the screen
        screen.fblits(sprites)
