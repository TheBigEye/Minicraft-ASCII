import pygame

from .globals import *
from .sound import *

from random import randint


class Color:
    WHITE: tuple    = (255, 255, 255)
    RED: tuple      = (255, 000, 000)
    GREEN: tuple    = (000, 255, 000)
    BLUE: tuple     = (000, 000, 255)
    BLACK: tuple    = (000, 000, 000)
    CYAN: tuple     = (000, 255, 255)
    YELLOW: tuple   = (255, 255, 000)
    MAGENTA: tuple  = (255, 000, 255)


class TitleMenu():
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font

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
            line.replace("█", symbol) for line, symbol in zip(self.title_text, ["░", "▒", "▒", "▓", "▓", "█", " "])
        ]

        # Initialize color variables for the title
        self.color_increment: int = 2

        # Opcity values for fade effect
        self.title_alpha: int = 0
        self.menu_alpha: int = 0
        self.cursor_alpha: int = 0

        self.cursor_visible: bool = True
        self.cursor_timer: int = 0

        self.line_height: int = 16

        self.seed_input_rect = pygame.Rect((SCREEN_HALF_W - 136), (SCREEN_HALF_H + 48), 272, 40)

        self.initialized = False


    def tick(self, world) -> None:
        if not self.initialized:
            pygame.mixer.music.load('./assets/sounds/titleTheme.ogg')
            pygame.mixer.music.play(-1, fade_ms = 12000)

            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(self.seed_input_rect)
            self.initialized = True

        # On init the title menu, we increase the
        # eleemtns opcity for an nice fade-in effect
        if (self.menu_alpha < 255):
            self.menu_alpha += 1

        if (self.menu_alpha > 32) and (self.cursor_alpha < 128):
            self.cursor_alpha += 1

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
                    if len(self.seed_input) == 0:
                        world_seed = randint(-(2**19937-1), 2**19937-1)
                    else:
                        world_seed = self.seed_input

                    Sound.play("confirmSound")
                    pygame.mixer.music.fadeout(2000)
                    pygame.mixer.music.unload()
                    pygame.key.stop_text_input()

                    world.initialize(world_seed, 3)

                    self.initialized = False
                elif event.key == pygame.K_BACKSPACE:
                    self.seed_input = self.seed_input[:-1]

    def render(self) -> None:
        self.screen.fill(0)

        sprites: list = []

        # WARNING, the following code is shitty ...
        seed_text = self.font.render("Enter World Seed:", False, (0, self.menu_alpha, self.menu_alpha), Color.BLACK).convert()
        seed_rect = seed_text.get_rect(center = (SCREEN_HALF_W, (SCREEN_HALF_H + 32)))

        copy_text = self.font.render("Game by TheBigEye", False, (0, self.menu_alpha, self.menu_alpha), Color.BLACK).convert()
        copy_rect = copy_text.get_rect(bottomleft = (4, SCREEN_FULL_H))

        vers_text = self.font.render("Infdev 0.31", False, (0, self.menu_alpha, self.menu_alpha), Color.BLACK).convert()
        vers_rect = vers_text.get_rect(bottomright = (SCREEN_FULL_W - 4, SCREEN_FULL_H))
        # End of shitty code

        y = (16 * 7)

        for line in self.title_text:
            title_surface = self.font.render(line, False, (0, self.title_alpha, self.title_alpha), 0).convert()
            title_rect = title_surface.get_rect(center = (SCREEN_HALF_W, y))
            sprites.append((title_surface, title_rect))
            y += self.line_height

        sprites.append((seed_text, seed_rect))

        # Render and display input text with cursor
        input_cursor = self.seed_input + ("█" if self.cursor_visible else " ")
        input_text = self.font.render(input_cursor, True, (self.cursor_alpha, self.cursor_alpha, self.cursor_alpha), Color.BLACK).convert()
        input_rect = input_text.get_rect(center = self.seed_input_rect.center)
        sprites.append((input_text, input_rect))

        sprites.append((copy_text, copy_rect))
        sprites.append((vers_text, vers_rect))

        pygame.draw.rect(self.screen, (0, self.menu_alpha, self.menu_alpha), self.seed_input_rect, 1)

        self.screen.fblits(sprites)

        pygame.display.update()
