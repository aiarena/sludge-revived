""" 



ArmyMicroManager
- assigns highest priority actions
- so theres the queen fighting the oracle at the nat. We want to maximize damage by stutterstepping the queen. If we just followed ArmyManager commands we would just attack the oracle consistently. Heres where ArmyMicroManager comes in and gives the queen a move command right after it has landed an attack. This move command will override the attack command from ArmyManager because its higher priority




ArmyMicroManager
- high priority actions (so that they override armymanager actions)
- basically all the micro is here like moving lings away from banes and what not
 """
class ArmyMicroManagerInterface():
    async def on_step(self, iteration):
        raise NotImplementedError('Army Micro Manager on_step not implemented!')