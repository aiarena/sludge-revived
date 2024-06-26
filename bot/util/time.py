from sc2 import BotAI

def getTimeInSeconds(self, bot: BotAI):
    # returns real time if game is played on "faster"
    return bot.state.game_loop * 0.725 * (1/16)