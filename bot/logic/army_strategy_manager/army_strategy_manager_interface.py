'''
ArmyStrategyManager
- assigns lowest priority actions
- tells units to split off to do different things, like say theres an oracle in our base, armystrategymanager will choose the closest anti air units with reosurce value a little over the enemy resource value (so lets say it chooses 2 queens) and give them an action to attack the oracle
- controls large army movements, like moving our army across the map to enemy base
'''
class ArmyStrategyManagerInterface():
    async def on_step(self):
        raise NotImplementedError('ArmyStrategyManager on_step not implemented!')