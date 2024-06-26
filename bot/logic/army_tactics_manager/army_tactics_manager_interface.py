"""

ArmyManager (or maybe ArmyTacticsManager or smth)
- assigns medim priority actions
- tells units to engage or disengage nearby enemy units
- so lets say we have 2 queens assigned to attack an oracle in the main base, but other one of the queens is already fighting against adepts at the nat. ArmyManager will tell the queen to engage the closest target and this will override the command from ArmyStrategyManager


ArmyManager does similar stuff as sludgment used to do for army management, namely controlling the army in groups:
- first we divide the army into armygroups based on position
- we iterate over armygroups and figure out engagement, retreat etc. logic. If an armygroup is idle it will be ordered to move toward the closest other armygroup (so that the groups can merge)
- actions assigned by the armymanager have low priority




"""

class ArmyTacticsManagerInterface():
    async def on_step(self):
        raise NotImplementedError('Army Manager on_step not implemented!')