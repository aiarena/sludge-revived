import math
import random

from sc2 import UnitTypeId, AbilityId
from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point2, Point3
from sc2.ids.ability_id import AbilityId
from sc2.data import ActionResult

from .queen_manager_interface import QueenManagerInterface
from bot.services.role_service import RoleService
from bot.model.unit_role import UnitRole
from bot.services.state_service import StateService
import bot.injector as injector
from bot.services.action_service import ActionService

class DefaultQueenManager(QueenManagerInterface):
    def __init__(self):
        self.role_service: RoleService = injector.inject(RoleService)
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)

        self.enableCreepSpread: bool = True
        self.stopMakingNewTumorsWhenAtCoverage = 0.3 # stops queens from putting down new tumors and save up transfuse energy
        self.creepTargetDistance = 15 # was 10
        self.creepTargetCountsAsReachedDistance = 10 # was 25
        self.creepSpreadInterval = 10

        self.iteration = 0
        self.assigned_tags = set()

        #things that will be set later on (not all things set later on are listed here)
        self.exactExpansionLocations: list = []

    async def on_step(self, queens: Units) -> 'assigned tags':
        self.assigned_tags = set()

        for queen in queens:
            queen: Unit
            if len(queen.orders) and not queen.orders[0].ability in {AbilityId.MOVE, AbilityId.ATTACK}:
                self.assigned_tags.add(queen.tag)
        queens = queens.tags_not_in(self.assigned_tags)

        non_inject_queens: Units = queens.filter(lambda q: self.role_service.getRole(q.tag) != UnitRole.INJECT_QUEEN)

        # assign dedicated inject queens to hatches (max 4)
        if len(self.state.injected_hatches) < 4:
            for hatch in self.state.own_units(UnitTypeId.HATCHERY).sorted_by_distance_to(self.state._bot.start_location).ready:
                if hatch.tag in self.state.injected_hatches.keys():
                    continue
                if non_inject_queens.exists:
                    closest_queen: Unit = non_inject_queens.closest_to(hatch.position)
                    if closest_queen:
                        self.state.injected_hatches[hatch.tag] = closest_queen.tag
                        self.role_service.setRole(closest_queen.tag, UnitRole.INJECT_QUEEN)
                        non_inject_queens: Units = queens.filter(lambda q: self.role_service.getRole(q.tag) != UnitRole.INJECT_QUEEN)
        
        # inject hatches
        for hatch_tag in self.state.injected_hatches.copy():
            # dont inject if there are nearby units
            hatch: Unit = self.state.own_units.find_by_tag(hatch_tag)
            if hatch and self.state._bot.known_enemy_units.closer_than(15, hatch.position).exists:
                continue
            inject_queen = self.state.own_units.find_by_tag(self.state.injected_hatches[hatch_tag])
            if inject_queen:
                try:
                    abilities = await self.state._bot.get_available_abilities(inject_queen)
                    if abilities and len(abilities) > 0 and AbilityId.EFFECT_INJECTLARVA in abilities:
                        self.action_service.add(inject_queen.tag, inject_queen(AbilityId.EFFECT_INJECTLARVA, hatch))
                        self.assigned_tags.add(inject_queen.tag)
                    else:
                        # move to hatch if inject not available
                        if inject_queen.distance_to(hatch.position) > 10:
                            self.action_service.add(inject_queen.tag, inject_queen.move(hatch.position))
                            self.assigned_tags.add(inject_queen.tag)
                except:
                    pass
                    # print('inject error')
            else:
                del self.state.injected_hatches[hatch_tag]
        
        self.role_service.setRole(non_inject_queens.tags, UnitRole.CREEP_QUEEN)

        #creep spread
        self.update_iteration()
        #TODO include in state first iteration? problem is its an async function
        if self.iteration == 1 and self.enableCreepSpread:
            await self.findExactExpansionLocations()
        await self.creep_spread(queens.filter(lambda q: self.role_service.getRole(q.tag) == UnitRole.CREEP_QUEEN))

        return self.assigned_tags

    def update_iteration(self) -> None:
        #TODO figure out how to replace the things that rely on iteration
        #divide game loop by 8 to get iteration
        self.iteration = int(self.state._bot.state.game_loop/8)

    async def creep_spread(self, queens: Units) -> None:
        #copied from BurnySc2's creep bot (https://github.com/BurnySc2/burny-bots-python-sc2)
        if self.enableCreepSpread and self.iteration % self.creepSpreadInterval == 0 and \
             (self.state.getTimeInSeconds() > 3 * 60 or self.state.own_units({UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMORQUEEN}).amount < 2):
            await self.doCreepSpread(queens)

    async def findExactExpansionLocations(self):
        # execute this on start, finds all expansions where creep tumors should not be build near
        self.exactExpansionLocations = []
        for loc in self.state._bot.expansion_locations.keys():
            self.exactExpansionLocations.append(await self.find_placement(UnitTypeId.HATCHERY, loc, minDistanceToResources=5.5, placement_step=1)) # TODO: change mindistancetoresource so that a hatch still has room to be built

    async def findCreepPlantLocation(self, targetPositions, castingUnit, minRange=None, maxRange=None, stepSize=1, onlyAttemptPositionsAroundUnit=False, locationAmount=32, dontPlaceTumorsOnExpansions=True):
        """function that figures out which positions are valid for a queen or tumor to put a new tumor     
        
        Arguments:
            targetPositions {set of Point2} -- For me this parameter is a set of Point2 objects where creep should go towards 
            castingUnit {Unit} -- The casting unit (queen or tumor)
        
        Keyword Arguments:
            minRange {int} -- Minimum range from the casting unit's location (default: {None})
            maxRange {int} -- Maximum range from the casting unit's location (default: {None})
            onlyAttemptPositionsAroundUnit {bool} -- if True, it will only attempt positions around the unit (ideal for tumor), if False, it will attempt a lot of positions closest from hatcheries (ideal for queens) (default: {False})
            locationAmount {int} -- a factor for the amount of positions that will be attempted (default: {50})
            dontPlaceTumorsOnExpansions {bool} -- if True it will sort out locations that would block expanding there (default: {True})
        
        Returns:
            list of Point2 -- a list of valid positions to put a tumor on
        """

        assert isinstance(castingUnit, Unit)
        positions = []
        ability = self.state._bot._game_data.abilities[AbilityId.ZERGBUILD_CREEPTUMOR.value]
        if minRange is None: minRange = 0
        if maxRange is None: maxRange = 500

        # get positions around the casting unit
        positions = self.getPositionsAroundUnit(castingUnit, minRange=minRange, maxRange=maxRange, stepSize=stepSize, locationAmount=locationAmount)

        # stop when map is full with creep
        if len(self.positionsWithoutCreep) == 0:
            return None

        # filter positions that would block expansions
        if dontPlaceTumorsOnExpansions and hasattr(self, "exactExpansionLocations"):
            positions = [x for x in positions if self.getHighestDistance(x.closest(self.exactExpansionLocations), x) > 3] 
            # TODO: need to check if this doesnt have to be 6 actually
            # this number cant also be too big or else creep tumors wont be placed near mineral fields where they can actually be placed

        # check if any of the positions are valid
        validPlacements = await self.state._bot._client.query_building_placement(ability, positions)

        # filter valid results
        validPlacements = [p for index, p in enumerate(positions) if validPlacements[index] == ActionResult.Success]

        allTumors = self.state.own_units({UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMORQUEEN})
        # usedTumors = allTumors.filter(lambda x:x.tag in self.usedCreepTumors)
        unusedTumors = allTumors.filter(lambda x:x.tag not in self.usedCreepTumors)
        if castingUnit is not None and castingUnit in allTumors:
            unusedTumors = unusedTumors.filter(lambda x:x.tag != castingUnit.tag)

        # filter placements that are close to other unused tumors
        if len(unusedTumors) > 0:
            validPlacements = [x for x in validPlacements if x.distance_to(unusedTumors.closest_to(x)) >= 10] 

        validPlacements.sort(key=lambda x: x.distance_to(x.closest(self.positionsWithoutCreep)), reverse=False)

        if len(validPlacements) > 0:
            return validPlacements
        return None

    def getHighestDistance(self, unit1, unit2):    
        # returns just the highest distance difference, return max(abs(x2-x1), abs(y2-y1))
        # required for creep tumor placement
        assert isinstance(unit1, (Unit, Point2, Point3))
        assert isinstance(unit2, (Unit, Point2, Point3))
        if isinstance(unit1, Unit):
            unit1 = unit1.position.to2
        if isinstance(unit2, Unit):
            unit2 = unit2.position.to2
        return max(abs(unit1.x - unit2.x), abs(unit1.y - unit2.y))

    async def updateCreepCoverage(self, stepSize=None):
        if stepSize is None:
            stepSize = self.creepTargetDistance
        ability = self.state._bot._game_data.abilities[AbilityId.ZERGBUILD_CREEPTUMOR.value]

        positions = [Point2((x, y)) \
        for x in range(self.state._bot._game_info.playable_area[0]+stepSize, self.state._bot._game_info.playable_area[0] + self.state._bot._game_info.playable_area[2]-stepSize, stepSize) \
        for y in range(self.state._bot._game_info.playable_area[1]+stepSize, self.state._bot._game_info.playable_area[1] + self.state._bot._game_info.playable_area[3]-stepSize, stepSize)]

        validPlacements = await self.state._bot._client.query_building_placement(ability, positions)
        successResults = [
            ActionResult.Success, # tumor can be placed there, so there must be creep
            ActionResult.CantBuildLocationInvalid, # location is used up by another building or doodad,
            ActionResult.CantBuildTooFarFromCreepSource, # - just outside of range of creep            
            # ActionResult.CantSeeBuildLocation - no vision here      
            ]
        # self.positionsWithCreep = [p for index, p in enumerate(positions) if validPlacements[index] in successResults]
        # TODO eliminate redundancy (positionsWithoutCreep assigned twice)
        self.positionsWithCreep = [p for valid, p in zip(validPlacements, positions) if valid in successResults]
        self.positionsWithoutCreep = [p for index, p in enumerate(positions) if validPlacements[index] not in successResults]
        self.positionsWithoutCreep = [p for valid, p in zip(validPlacements, positions) if valid not in successResults]
        return self.positionsWithCreep, self.positionsWithoutCreep

    async def doCreepSpread(self, queens: Units):
        # only use queens that are not assigned to do larva injects
        allTumors = self.state.own_units({UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMORQUEEN})

        if not hasattr(self, "usedCreepTumors"):
            self.usedCreepTumors = set()

        # gather all queens that are not assigned for injecting and have 25+ energy
        unassignedQueens = queens.filter(lambda q: q.energy >= 25 and (q.is_idle or q.is_moving))

        # update creep coverage data and points where creep still needs to go
        if not hasattr(self, "positionsWithCreep") or self.iteration % self.creepSpreadInterval * 10 == 0:
            posWithCreep, posWithoutCreep = await self.updateCreepCoverage()
            totalPositions = len(posWithCreep) + len(posWithoutCreep)
            self.creepCoverage = len(posWithCreep) / totalPositions
            # print(self.getTimeInSeconds(), "creep coverage:", creepCoverage)

        # filter out points that have already tumors / bases near them
        if hasattr(self, "positionsWithoutCreep"):
            # have to set this to some values or creep tumors will clump up in corners trying to get to a point they cant reach
            self.positionsWithoutCreep = [x for x in self.positionsWithoutCreep if (allTumors | self.state.own_townhalls).closer_than(self.creepTargetCountsAsReachedDistance, x).amount < 1 or (allTumors | self.state.own_townhalls).closer_than(self.creepTargetCountsAsReachedDistance + 10, x).amount < 5] 

        # make all available queens spread creep until creep coverage is reached 50%
        if hasattr(self, "creepCoverage") and (self.creepCoverage < self.stopMakingNewTumorsWhenAtCoverage or allTumors.amount - len(self.usedCreepTumors) < 25):
            for queen in unassignedQueens:
                # locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=queen, minRange=3, maxRange=30, stepSize=2, locationAmount=16)
                if self.state.own_townhalls.ready.exists:
                    locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=queen, minRange=3, maxRange=30, stepSize=2, locationAmount=16)
                    # locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=self.townhalls.ready.random, minRange=3, maxRange=30, stepSize=2, locationAmount=16)
                    if locations is not None:
                        for loc in locations:
                            err = True
                            self.action_service.add(queen.tag, queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, loc))
                            self.assigned_tags.add(queen.tag)
                            if not err:
                                break

        
        unusedTumors = allTumors.filter(lambda x: x.tag not in self.usedCreepTumors)
        tumorsMadeTumorPositions = set()
        for tumor in unusedTumors:
            tumorsCloseToTumor = [x for x in tumorsMadeTumorPositions if tumor.distance_to(Point2(x)) < 8]
            if len(tumorsCloseToTumor) > 0:
                continue
            abilities = await self.state._bot.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                locations = await self.findCreepPlantLocation(self.positionsWithoutCreep, castingUnit=tumor, minRange=10, maxRange=10) # min range could be 9 and maxrange could be 11, but set both to 10 and performance is a little better
                if locations is not None:
                    for loc in locations:
                        #TODO might be some bug caused by err functionality (check burny's original code for this section for details)
                        err = True
                        self.action_service.add(tumor.tag, tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, loc))
                        if not err:
                            tumorsMadeTumorPositions.add((tumor.position.x, tumor.position.y))
                            self.usedCreepTumors.add(tumor.tag)
                            break

    def getPositionsAroundUnit(self, unit, minRange=0, maxRange=500, stepSize=1, locationAmount=32):
        # e.g. locationAmount=4 would only consider 4 points: north, west, east, south
        assert isinstance(unit, (Unit, Point2, Point3))
        if isinstance(unit, Unit):
            loc = unit.position.to2
        else:
            loc = unit
        positions = [Point2(( \
            loc.x + distance * math.cos(math.pi * 2 * alpha / locationAmount), \
            loc.y + distance * math.sin(math.pi * 2 * alpha / locationAmount))) \
            for alpha in range(locationAmount) # alpha is the angle here, locationAmount is the variable on how accurate the attempts look like a circle (= how many points on a circle)
            for distance in range(minRange, maxRange+1)] # distance depending on minrange and maxrange
        return positions

    async def find_placement(self, building, near, max_distance=20, random_alternative=False, placement_step=3, min_distance=0, minDistanceToResources=3):
        """Finds a placement location for building."""

        assert isinstance(building, (AbilityId, UnitTypeId))
        # assert self.can_afford(building)
        assert isinstance(near, Point2)

        if isinstance(building, UnitTypeId):
            building = self.state._bot._game_data.units[building.value].creation_ability
        else: # AbilityId
            building = self.state._bot._game_data.abilities[building.value]

        if await self.state._bot.can_place(building, near):
            return near

        for distance in range(min_distance, max_distance, placement_step):
            possible_positions = [Point2(p).offset(near).to2 for p in (
                [(dx, -distance) for dx in range(-distance, distance+1, placement_step)] +
                [(dx,  distance) for dx in range(-distance, distance+1, placement_step)] +
                [(-distance, dy) for dy in range(-distance, distance+1, placement_step)] +
                [( distance, dy) for dy in range(-distance, distance+1, placement_step)]
            )]
            if (self.state.own_townhalls | self.state._bot.state.mineral_field | self.state._bot.state.vespene_geyser).exists and minDistanceToResources > 0: 
                possible_positions = [x for x in possible_positions if (self.state._bot.state.mineral_field | self.state._bot.state.vespene_geyser).closest_to(x).distance_to(x) >= minDistanceToResources] # filter out results that are too close to resources

            res = await self.state._bot._client.query_building_placement(building, possible_positions)
            possible = [p for r, p in zip(res, possible_positions) if r == ActionResult.Success]
            if not possible:
                continue

            if random_alternative:
                return random.choice(possible)
            else:
                return min(possible, key=lambda p: p.distance_to(near))
        return None
