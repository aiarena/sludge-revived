# Imports have to be in this order, leave this comment here to fall back to it if they get messed up
# import sc2, sys
# from __init__ import run_ladder_game
# from sc2 import Race, Difficulty
# from sc2.player import Bot, Computer
# import random
import sc2, sys
from __init__ import run_ladder_game
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
import random

# Load bot
from bot import MyBot

bot = Bot(Race.Zerg, MyBot())

# Start game
if __name__ == "__main__":
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        result, opponentid = run_ladder_game(bot)
        print(f"{result} against opponent {opponentid}")
    else:
        # Local game
        print("Starting local game...")
            # choose a race for the opponent builtin bot
        race = random.choice([sc2.Race.Zerg, sc2.Race.Terran, sc2.Race.Protoss])  # , sc2.Race.Random
        # choose a strategy for the opponent builtin bot
        build = random.choice([
                                sc2.AIBuild.RandomBuild,
                                sc2.AIBuild.Rush,
                                sc2.AIBuild.Timing,
                                sc2.AIBuild.Power,
                                sc2.AIBuild.Macro,
                                sc2.AIBuild.Air,
                            ])

        # create the opponent builtin bot instance
        builtin_bot = sc2.player.Computer(race, sc2.Difficulty.VeryHard, build)  # CheatInsane VeryHard
        map_name = random.choice([
                                "GoldenAura513AIE"
                                ])

        sc2.run_game(
            sc2.maps.get(map_name),
            [
                # Human(Race.Terran),
                bot,
                builtin_bot,
                # Computer(Race.Protoss, Difficulty.CheatInsane),
            ],
            realtime=False,
            save_replay_as="Sludgement.SC2Replay",
        )
