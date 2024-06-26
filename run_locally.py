import json

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, AIBuild, Human

from bot import MyBot

from bot.configuration.basic_configuration import BasicConfiguration

def main():
    with open("botinfo.json") as f:
        info = json.load(f)

    race = Race[info["race"]]

    run_game(maps.get("(2) Redshift LE"), [
        #Human(Race.Terran),
        Bot(race, MyBot()),
        Computer(Race.Terran, Difficulty.VeryHard, ai_build=AIBuild.Timing)
    ], realtime=False, step_time_limit=2.0, game_time_limit=(60*20), save_replay_as="test.SC2Replay")

if __name__ == '__main__':
    main()
