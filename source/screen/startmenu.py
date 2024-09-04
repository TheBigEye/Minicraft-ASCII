from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

import pygame
from pygame import Font, Surface

from source.screen.screen import Color
from source.screen.shader import Shader
from source.sound import Sound
from source.utils.constants import *

if TYPE_CHECKING:
    from source.core.world import World


class StartMenu:
    def __init__(self, world: World, font: Font) -> None:
        self.world = world
        self.font = font

        self.filter = Shader().filter

        self.overlay = pygame.Surface(SCREEN_SIZE_T, pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 255))

        self.seed_input: str = ""

        self.title_text = [
            "      ███╗   ███╗ ██╗ ███╗   ██╗ ██╗  ██████╗ ██████╗   █████╗  ███████╗ ████████╗  ",
            "     ████╗ ████║ ██║ ████╗  ██║ ██║ ██╔════╝ ██╔══██╗ ██╔══██╗ ██╔════╝ ╚══██╔══╝   ",
            "    ██╔████╔██║ ██║ ██╔██╗ ██║ ██║ ██║      ██████╔╝ ███████║ █████╗      ██║       ",
            "   ██║ ██╔╝██║ ██║ ██║ ██╗██║ ██║ ██║      ██╔══██╗ ██╔══██║ ██╔══╝      ██║        ",
            "  ██║  ╚╝ ██║ ██║ ██║  ████║ ██║  ██████╗ ██║  ██║ ██║  ██║ ██║         ██║         ",
            "  ╚═╝     ╚═╝ ╚═╝ ╚═╝  ╚═══╝ ╚═╝  ╚═════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝         ╚═╝         ",
            "                                 ‟ POTATO EDITION ”                                 "
        ]

        self.title_text = [
            line.replace("█", symbol) for line, symbol in zip(self.title_text, ["▒", "▓", "▓", "█", "█", "█", " "])
        ]

        # Initialize color variables for the title
        self.color_increment: int = 2

        # Opcity values for fade effect
        self.menu_alpha: int = 0
        self.title_alpha: int = 0

        self.cursor_visible: bool = True
        self.cursor_timer: int = 0

        self.line_height: int = 16

        self.seed_text = self.font.render("Enter World Seed:", False, Color.CYAN, Color.BLACK).convert()
        self.seed_rect = self.seed_text.get_rect(center = (SCREEN_HALF_W, (SCREEN_HALF_H + 32)))

        self.author_text = self.font.render("Game by TheBigEye", False, Color.CYAN, Color.BLACK).convert()
        self.author_rect = self.author_text.get_rect(bottomleft = (4, SCREEN_FULL_H))

        self.version_text = self.font.render("Infdev 0.31", False, Color.CYAN, Color.BLACK).convert()
        self.version_rect = self.version_text.get_rect(bottomright = (SCREEN_FULL_W - 4, SCREEN_FULL_H))

        self.seed_input_rect = pygame.Rect((SCREEN_HALF_W - 136), (SCREEN_HALF_H + 48), 272, 40)

        self.initialized = False


    def update(self) -> None:
        if not self.initialized:
            pygame.mixer.music.load('./assets/sounds/titleTheme.ogg')
            pygame.mixer.music.play(-1, fade_ms = 12000)

            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(self.seed_input_rect)
            self.initialized = True

        # On init the title menu, we increase the
        # eleemtns opcity for an nice fade-in effect
        if (self.menu_alpha < 255):
            self.overlay.set_alpha(255 - self.menu_alpha)
            self.menu_alpha += 1

        if (self.title_alpha < 128):
            self.title_alpha += 1

        # If the opcaity is full, we do a little
        # title fade-in / fade-on loop animation
        else:
            self.title_alpha += self.color_increment
            if self.title_alpha in (250, 128):
                self.color_increment = -self.color_increment

        # Text input cursor blinking
        self.cursor_timer = (self.cursor_timer + 1) % 8
        if self.cursor_timer == 0:
            self.cursor_visible = not self.cursor_visible

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input()
                pygame.quit()

            elif event.type == pygame.TEXTINPUT :
                if len(self.seed_input) < 32:
                    self.seed_input += event.text
                    Sound.play("typingSound")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.key.stop_text_input()

                    if len(self.seed_input) == 0:
                        world_seed = randint(-(2**19937-1), 2**19937-1)
                    else:
                        world_seed = self.seed_input

                    Sound.play("confirmSound")
                    pygame.mixer.music.fadeout(2000)
                    pygame.mixer.music.unload()

                    self.world.initialize(world_seed)

                    self.initialized = False
                elif event.key == pygame.K_BACKSPACE:
                    self.seed_input = self.seed_input[:-1]


    def render(self, screen: Surface) -> None:
        sprites: list = []

        y = (16 * 7)

        for line in self.title_text:
            title_surface = self.font.render(line, False, (0, self.title_alpha, self.title_alpha), 0).convert()
            title_rect = title_surface.get_rect(center = (SCREEN_HALF_W, y))
            sprites.append((title_surface, title_rect))
            y += self.line_height

        sprites.append((self.seed_text, self.seed_rect))

        # Render and display input text with cursor
        input_cursor = self.seed_input + ("█" if self.cursor_visible else " ")
        input_text = self.font.render(input_cursor, False, Color.GREY, Color.BLACK).convert()
        input_rect = input_text.get_rect(center = self.seed_input_rect.center)

        sprites.append((input_text, input_rect))
        sprites.append((self.author_text, self.author_rect))
        sprites.append((self.version_text, self.version_rect))

        pygame.draw.rect(screen, Color.CYAN, self.seed_input_rect, 1)

        sprites.append((self.overlay, (0, 0)))
        sprites.append((self.filter, (0, 0)))

        screen.fblits(sprites)
