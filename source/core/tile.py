from __future__ import annotations

from random import choice, randint
from typing import TYPE_CHECKING

from source.game import Game
from source.sound import Sound

if TYPE_CHECKING:
    from source.core.world import World


class Tile:

    __slots__ = (
        'id',
        'chars',
        'color',
        'solid',
        'parent',
        'health',
        'sprite'
    )

    def __init__(self, id: int, chars: list, color: tuple, solid: bool, parent: int, health: int) -> None:
        self.id = id
        self.chars = chars
        self.color = color
        self.solid = solid
        self.parent = parent
        self.health = health

        # Compile sprite
        rand_num = randint(2, 4)
        background = tuple(c // rand_num for c in self.color)
        self.sprite = Game.sprite(choice(self.chars), self.color, background)


    def hurt(self, world: World, x: int, y: int, damage: int) -> None:
        if self.health is not None:
            self.health -= damage

            Sound.play("genericHurt")

            if (self.health <= 0) and (self.parent is not None):
                world.set_tile(x, y, self.parent)


    def clone(self) -> Tile:
        """ Returns a copy of the tile instance """
        return Tile(self.id, self.chars, self.color, self.solid, self.parent, self.health)


tiles = {
    # NAME               ID,   CHARS,                                   COLOR,           SOLID?,  PARENT, HEALTH
    "empty":         Tile(0,   ['¿?'],                                  (255, 000, 000), False,   None,   None ),

    "ocean":         Tile(1,   ["~'", "'~"],                            ( 44,  44, 178), False,   None,   None ),
    "sea":           Tile(2,   ['≈˜', '˜≈'],                            ( 54,  54, 217), False,   None,   None ),
    "river":         Tile(3,   ['┬┴', '┴┬', '•┬', '┴•', '┬•', '•┴'],    ( 63,  63, 252), False,   None,   None ),

    "sand":          Tile(4,   ['≈~', '~≈'],                            (210, 199, 139), False,   5,      1    ),
    "dirt":          Tile(5,   ['~≈', '≈~'],                            (139,  69,  19), False,   6,      1    ),
    "hole":          Tile(6,   ['•˚', '˚•'],                            (139,  69,  19), False,   None,   None ),
    "grass":         Tile(7,   ['.ⁿ', 'ⁿ.'],                            (126, 176,  55), False,   5,      1    ),
    "tallgrass":     Tile(8,   ['"ⁿ', 'ⁿ"'],                            (108, 151,  47), False,   7,      2    ),

    "oak tree":      Tile(9,   ['♣♠'],                                  (000, 128, 000), True,    7,      16   ),
    "birch tree":    Tile(10,  ['¶♠'],                                  (000, 178, 000), True,    7,      24   ),
    "pine tree":     Tile(11,  ['Γ♠'],                                  (000, 232, 000), True,    6,      32   ),

    "stone":         Tile(12,  ['n∩', '∩n', 'n⌂', '⌂n'],                (121, 121, 121), True,    13,     32   ),
    "gravel":        Tile(13,  ['≈~', '~≈'],                            ( 50,  50,  50), False,   5,      4    ),

    "ice":           Tile(14,  ['≈˜', '˜≈'],                            (135, 136, 216), False,   2,      4    ),
    "snow":          Tile(15,  ['.ⁿ', 'ⁿ.'],                            (220, 220, 220), False,   5,      1    ),
    "frost":         Tile(16,  ['"ⁿ', 'ⁿ"'],                            (238, 238, 238), False,   7,      2    ),
    "iceberg":       Tile(17,  ["~'", "'~"],                            (114, 114, 184), False,   1,      2    )
}


fluids = {
    tiles["ocean"].id,
    tiles["sea"].id,
    tiles["river"].id
}
