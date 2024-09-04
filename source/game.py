import pygame
from pygame import Surface
from pygame.font import Font

from source.utils.constants import SCREEN_SIZE_T


class Game:
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode(SCREEN_SIZE_T)
    winicon = pygame.image.load('./assets/icon.png').convert_alpha()

    pygame.event.set_allowed(
        [
            pygame.QUIT,
            pygame.KEYDOWN,
            pygame.TEXTINPUT
        ]
    )

    pygame.display.set_caption("Minicraft Potato Edition")
    pygame.display.set_icon(winicon)

    dither = [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5]
    ]

    overlay = pygame.Surface((200, 200), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 0))
    for y in range(200):
        for x in range(200):
            distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
            if distance < 100:
                # Obtener el valor del patrón de dithering basado en la posición
                dither_value = dither[y % 4][x % 4]
                # Convertir el dither_value a un rango de 0 a 255
                alpha = max(0, 255 - (distance * 2.55) - (dither_value * 10))
                overlay.set_at((x, y), (0, 0, 0, alpha))

    darkness = pygame.Surface((SCREEN_SIZE_T), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, 255))

    debug: bool = False

    sprites: dict = {}

    tile: list = []
    mobs: list = []

    font: Font = pygame.font.Font("./assets/terrain.ttf", 16)

    @staticmethod
    def initialize(font: Font, tiles: dict, mobs: dict) -> None:
        Game.font = font
        Game.tile = list(tiles)
        Game.mobs = list(mobs)


    @staticmethod
    def sprite(char: str, foreground: tuple, background: tuple) -> Surface:
        key = (char, foreground, background)

        # If the sprite already exists in the pool, we reuse it
        if key in Game.sprites:
            return Game.sprites[key]

        # If not, we create a new sprite and add it to the pool
        surface = Game.font.render(char, False, foreground, background).convert()
        Game.sprites[key] = surface
        return surface
