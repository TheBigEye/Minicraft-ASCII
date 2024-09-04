import pygame
from pygame import Surface

from source.screen.screen import Color
from source.utils.constants import *


class Debug:

    @staticmethod
    def render(screen: Surface, chunks: list, px: int, py: int, cx: int, cy: int) -> None:
        offset_x = SCREEN_HALF_W - (px % CHUNK_SIZE) * TILE_SIZE
        offset_y = SCREEN_HALF_H - (py % CHUNK_SIZE) * TILE_SIZE

        current_chunk = (cx, cy)

        for x in range(-(RENDER_RANGE_H + 1), RENDER_RANGE_H + 2):
            base_chunk_x_draw = x * CHUNK_SIZE * TILE_SIZE + offset_x

            for y in range(-RENDER_RANGE_V, RENDER_RANGE_V + 1):
                base_chunk_y_draw = y * CHUNK_SIZE * TILE_SIZE + offset_y
                chunk_position = (cx + x, cy + y)

                # Solo calcula los vecinos si no estamos en el chunk actual
                if chunk_position != current_chunk:
                    neighbors = [
                        (chunk_position[0] - 1, chunk_position[1]),
                        (chunk_position[0] + 1, chunk_position[1]),
                        (chunk_position[0], chunk_position[1] - 1),
                        (chunk_position[0], chunk_position[1] + 1)
                    ]
                    all_neighbors_generated = all(neighbor in chunks for neighbor in neighbors)
                else:
                    all_neighbors_generated = True  # El chunk actual siempre tiene todos sus vecinos generados

                # Calcula el rectángulo del chunk
                chunk_rect = pygame.Rect(base_chunk_x_draw, base_chunk_y_draw, (CHUNK_SIZE * TILE_SIZE), (CHUNK_SIZE * TILE_SIZE))

                # Determina el color del rectángulo
                if chunk_position == current_chunk:
                    color = Color.MAGENTA
                elif not all_neighbors_generated:
                    color = Color.RED
                else:
                    color = Color.GREEN

                pygame.draw.rect(screen, color, chunk_rect, 2)
                pygame.draw.rect(screen, Color.BLACK, chunk_rect.inflate(-2, -2), 1)
