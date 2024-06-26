import json

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human

from examples.zerg.zerg_rush import ZergRushBot
from examples.protoss.cannon_rush import CannonRushBot
from examples.terran.proxy_rax import ProxyRaxBot
from examples.protoss.threebase_voidray import ThreebaseVoidrayBot
from examples.cannonlover.cannon_lover_bot import CannonLoverBot

from bot import MyBot as Bot1
from bot import MyBot as Bot2

from bot.configuration.basic_configuration import BasicConfiguration

def main():
    with open("botinfo.json") as f:
        info = json.load(f)

    race = Race[info["race"]]

    run_game(maps.get("(2) Lost and Found LE"), [
        #Human(Race.Protoss),
        Bot(race, Bot1()),
        #Bot(Race.Zerg, ZergRushBot())
        #Bot(Race.Terran, ProxyRaxBot())
        #Bot(Race.Protoss, CannonRushBot())
        Bot(Race.Protoss, CannonLoverBot())
        #Bot(Race.Protoss, ThreebaseVoidrayBot())
        #Computer(Race.Terran, Difficulty.VeryHard)
        #Bot(race, Bot2())
    ], realtime=False, step_time_limit=2.0, game_time_limit=(60*20), save_replay_as="test.SC2Replay")

if __name__ == '__main__':
    main()
