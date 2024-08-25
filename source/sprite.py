import pygame


class SpritePool:
    def __init__(self, font: pygame.font.Font) -> None:
        self.pool: dict = {}
        self.font = font

    def get(self, char: str, foreground: tuple, background: tuple) -> pygame.Surface:
        key = (char, foreground, background)

        # If the sprite already exists in the pool, we reuse it
        if key in self.pool:
            return self.pool[key]

        # If not, we create a new sprite and add it to the pool
        sprite = self.font.render(char, False, foreground, background).convert()
        self.pool[key] = sprite
        return sprite
