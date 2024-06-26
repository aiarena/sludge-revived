import typing

from sc2 import BotAI

import bot.injector as injector

class ChatService():
    def __init__(self):
        self.bot: BotAI = injector.inject(BotAI)
    async def send(self, message):
        await self.bot.chat_send(message)