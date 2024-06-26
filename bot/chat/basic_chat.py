import random

from .chat_interface import ChatInterface
import bot.injector as injector
from ..services.chat_service import ChatService

class BasicChat(ChatInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_service: ChatService = injector.inject(ChatService)
    async def on_step(self, iteration):
        if iteration == 0:
            await self.greet()

    async def greet(self):
        await self.chat_service.send('14.7.2019 9:55')
        """ 
        msg = random.choice([
            "When I'm done half of humanity will still exist.",
            "Zerg is perfectly balanced, as all things should be."
        ])
        await self.chat_service.send(msg)
        """