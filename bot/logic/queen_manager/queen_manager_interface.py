class QueenManagerInterface:
    async def on_step(self, iteration):
        raise NotImplementedError('Queen manager on_step not implemented')