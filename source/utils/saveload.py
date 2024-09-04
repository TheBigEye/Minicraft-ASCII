from __future__ import annotations

import pickle
from typing import TYPE_CHECKING

from source.core.mob import mobs
from source.core.tile import tiles
from source.game import Game
from source.sound import Sound

if TYPE_CHECKING:
    from source.core.player import Player
    from source.core.world import World
    from source.utils.updater import Updater


class Saveload:

    # NOTE: basically, what we're doing is saving a list of IDs for each tile
    # (previously, we were saving the entire tile class in the World.chunks dictionary,
    # which was slow and resource-intensive). Now, we save just the ID of each tile, and
    # then when we want to load the game, it takes that list of IDs and reconstructs
    # it into a dictionary like before. I know, I know, it's not the most elegant
    # solution for now, rebuilding the classes for each tile in a massive world
    # is somewhat slow, but this way, I can avoid using Gzip :)

    @staticmethod
    def save(updater: Updater, world: World, player: Player) -> None:
        chunks = {
            chunk: [[tile.id for tile in row] for row in data]
            for chunk, data in world.chunks.items()
        }

        entities = [
            {
                'id': mob.id,
                'x': mob.x,
                'y': mob.y
            }
            for mob in world.entities
        ]

        game_data = {
            'about': {
                'name': "A Nice World"
            },
            'player': {
                'x': player.x,
                'y': player.y,
                'health': player.health,
                'energy': player.energy,
                'facing': player.facing
            },
            'chunks': chunks,
            'entities': entities,
            'worldSeed': world.seed,
            'worldPerm': world.perm,
            'worldSpawn': (world.sx, world.sy),
            'worldTicks': updater.ticks
        }

        with open('./saves/world.dat', 'wb') as file:
            pickle.dump(game_data, file, protocol=5)


    @staticmethod
    def load(updater: Updater, world: World, player: Player) -> None:
        with open('./saves/world.dat', 'rb') as file:
            game_data = pickle.load(file)

        player_data = game_data['player']

        player.x =      player_data['x']
        player.y =      player_data['y']
        player.health = player_data['health']
        player.energy = player_data['energy']
        player.facing = player_data['facing']

        world.seed =    game_data['worldSeed']
        world.perm =    game_data['worldPerm']
        world.sx =      game_data['worldSpawn'][0]
        world.sy =      game_data['worldSpawn'][1]
        updater.ticks =  game_data['worldTicks']

        # We rebuild the chunks from the tile ids
        chunks = game_data['chunks']
        world.chunks = {
            chunk: [
                [tiles[Game.tile[id]].clone() for id in row] for row in data
            ]
            for chunk, data in chunks.items()
        }

        # And also rebuild the entities
        entities = game_data['entities']
        world.entities = [
            mobs[Game.mobs[data['id']]].clone()
            for data in entities
        ]
        # We assing their positions again ...
        for mob, data in zip(world.entities, entities):
            mob.x = data['x']
            mob.y = data['y']

        Sound.play("eventSound")

        player.initialize(world, player.x, player.y)

        world.loaded = True
