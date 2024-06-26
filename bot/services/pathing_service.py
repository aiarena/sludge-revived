import sc2pathlib
import numpy as np

from sc2 import BotAI
from sc2.position import Point2, Point3

import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.debug_service import DebugService
from bot.hooks import hookable

@hookable
class PathingService:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug: DebugService = injector.inject(DebugService)
        self.bot: BotAI = injector.inject(BotAI)

    def on_init(self):
        self.pathing_grid = self._get_pathing_grid()
    
    def update(self):
        self.threat_grid = self._get_threat_grid()
        #if self.state.getTimeInSeconds() > 2.5 * 60:
        #    self._test_path_find()
        #    self.debug_grid(self.threat_grid)

    def debug_grid(self, grid):
        pathing = grid

        rows = pathing.shape[0]
        cols = pathing.shape[1]
        
        # for x in range(0, rows):
        #     for y in range(0, cols):
        #         if pathing[x,y] == 0:
        #             self.debug.box_out(Point3((x, y, 10)), Point3((x+1, y+1, 11)))
        
    def find_path(self, origin: Point2, destination: Point2, consider_threats = False) -> 'path, dist':
        if consider_threats:
            pf = sc2pathlib.PathFind(np.array(self.threat_grid, dtype=int))
        else:
            pf = sc2pathlib.PathFind(np.array(self.pathing_grid, dtype=int))
        start_int = (int(origin.x), int(origin.y))
        end_int =(int(destination.x), int(destination.y))
        return pf.find_path(start_int, end_int, False, False, 1, None, None)

    def _test_path_find(self):
        pathing = np.array(self.pathing_grid, dtype=int)
        pf = sc2pathlib.PathFind(pathing)

        pos1 = self.state.own_natural_position
        pos2 = self.state.enemy_natural_position
        path, dist = self.find_path(pos1, pos2, True)

        for point in path:
            x = point[0]
            y = point[1]
            self.debug.box_out(Point3((x, y, 10)), Point3((x+1, y+1, 11)))
    
    def _get_pathing_grid(self):
        pathing = self.bot.game_info.pathing_grid.data_numpy
        pathing = pathing / 255
        pathing = np.swapaxes(pathing, 0, 1)
        def mapping(x):
            return 1-x
        pathing = np.vectorize(mapping)(pathing)

        return pathing
    
    def _get_threat_grid(self):
        pathing = self.pathing_grid.copy()
        width, height = pathing.shape
        for unit in self.state.enemy_units:
            pos = unit.position
            pathing[int(pos.x), int(pos.y)] = 0
        for group in self.state.enemy_groups:
            if not group.range_hull:
                continue
            points = self.get_all_boundary_coords_from_polygon(group.range_hull)
            for point in points:
                if (point[0] >= 0 and point[0] < width - 1 and
                    point[1] >= 0 and point[1] < height - 1):
                    pathing[point[0], point[1]] = 0

        return pathing
    
    def get_vertices_from_polygon(self, polygon):
        vertices = set()
        for edge in polygon:
            vertices.add(edge[0])
            vertices.add(edge[1])
        return list(vertices)
    
    
    def get_all_edge_coords(self, edge):
        x1 = edge[0][0]
        y1 = edge[0][1]
        x2 = edge[1][0]
        y2 = edge[1][1]

        return get_line(int(x1), int(y1), int(x2), int(y2))
                
    def get_all_boundary_coords_from_polygon(self, polygon):
        points = []
        for edge in polygon:
            points.extend(self.get_all_edge_coords(edge))
        return points

def get_line(x1, y1, x2, y2):
    points = []
    issteep = abs(y2-y1) > abs(x2-x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2-y1)
    error = int(deltax / 2)
    y = y1
    ystep = None
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points
