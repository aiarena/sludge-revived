from typing import Union, Optional

from sc2 import BotAI
from sc2.client import debug_pb
from sc2.position import Point2, Point3

import bot.injector as injector

class DebugService():
    def __init__(self):
        self._bot: BotAI = injector.inject(BotAI)
        self.disabled = False
        
    async def render_debug(self):
        if self.disabled:
            return
        # await self._bot._client.send_debug()
    
    def text_world(self, *args):
        if self.disabled:
            return
        # self._bot._client.debug_text_world(*args)

    def text_simple(self, msg: str):
        if self.disabled:
            return
        # if self._bot._client:
        #     debug_msg = self.to_debug_message(msg) 
        #     self._bot._client._debug_texts.append(debug_msg)

    def line_out(self, *args):
        if self.disabled:
            return
        # self._bot._client.debug_line_out(*args)

    def sphere_out(self, *args):
        if self.disabled:
            return
        # self._bot._client.debug_sphere_out(*args)

    def box_out(self, *args):
        if self.disabled:
            return
        # self._bot._client.debug_box_out(*args)
    
    def text_screen_auto(self, text: str, line: int = 0, column: int = 0, color = None):
        if self.disabled:
            return
        if isinstance(color, tuple):
            color = Point3(color)
        pos = Point2((column * 0.1, line * 0.015))
        # self._bot._client.debug_text_screen(text, pos, color, 12)

    
    # edited from python-sc2
    def to_debug_message(
        self, text: str, color=None, pos: Optional[Union[Point2, Point3]] = None, size: int = 8
    ) -> debug_pb.DebugText:
        """ Helper function to create debug texts """
        client = self._bot._client
        color = client.to_debug_color(color)
        pt3d = client.to_debug_point(pos) if isinstance(pos, Point3) else None
        if pos:
            virtual_pos = client.to_debug_point(pos) if not isinstance(pos, Point3) else None
        else:
            virtual_pos = None

        return debug_pb.DebugText(color=color, text=text, virtual_pos=virtual_pos, world_pos=pt3d, size=size)