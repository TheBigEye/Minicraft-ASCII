
""" The gamelay speed is dependent for this """
GAME_TICKS: int = 30.0

SCREEN_FULL_W: int = 768
SCREEN_FULL_H: int = 512

SCREEN_HALF_W: int = SCREEN_FULL_W // 2
SCREEN_HALF_H: int = SCREEN_FULL_H // 2

SCREEN_SIZE_T: tuple = (SCREEN_FULL_W, SCREEN_FULL_H)
SCREEN_SIZE_I: int = (SCREEN_FULL_W * SCREEN_FULL_H)

RENDER_RANGE_V: int = 2
RENDER_RANGE_H: int = RENDER_RANGE_V * 1

TILE_SIZE: int = 16
CHUNK_SIZE: int = 8


""" Changing this is like adjusting the terrain detail resolution.
    The higher it is, the smaller the terrain will look, and if
    it's lower, the terrain will appear larger and more expansive.
"""
TERRAIN_SCALE: float = 0.0017
TERRAIN_PERSISTENCE: float = 0.46
TERRAIN_OCTAVES: int = 8
