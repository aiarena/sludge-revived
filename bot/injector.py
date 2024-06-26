from sc2 import BotAI

from .configuration.configuration_interface import ConfigurationInterface
from .configuration.basic_configuration import BasicConfiguration

from .services.chat_service import ChatService
from .services.state_service import StateService
from .services.action_service import ActionService
from .services.role_service import RoleService
from .services.debug_service import DebugService
from .services.threat_service import ThreatService
from .services.eco_balance_service import EcoBalanceService
from bot.services.unit_group_service import UnitGroupService
from bot.services.unit_type_service import UnitTypeService
from bot.services.pathing_service import PathingService

from bot.chat.chat_interface import ChatInterface
from bot.logic.logic_interface import LogicInterface
from bot.logic.spending.spending_interface import SpendingInterface
from bot.logic.spending_actions.spending_actions_interface import SpendingActionsInterface
from bot.logic.spending.supply_mechanic.supply_mechanic_interface import SupplyMechanicInterface
from bot.logic.unit_manager.unit_manager_v3 import UnitManager_v3
from bot.logic.army_tactics_manager.army_tactics_manager_interface import ArmyTacticsManagerInterface
from bot.logic.army_micro_manager.army_micro_manager_interface import ArmyMicroManagerInterface
from bot.logic.army_strategy_manager.army_strategy_manager_interface import ArmyStrategyManagerInterface
from bot.logic.resource_manager.resource_manager_interface import ResourceManagerInterface
from bot.logic.queen_manager.queen_manager_interface import QueenManagerInterface


class Injector():
    # When implementing new injectables be careful about the order of initialization
    # dependencies need to be initialized first or you will get an error:
    # 'Injector' object has no attribute '...'
    def init(self, config: ConfigurationInterface, bot: BotAI):
        self.d = {}
        self.config: ConfigurationInterface = config
        self.d[BotAI] = bot
        bot._game_data = None
        self.d[UnitTypeService] = UnitTypeService()
        self.d[ThreatService] = ThreatService()
        self.d[DebugService] = DebugService()
        self.d[StateService] = StateService()
        self.d[ChatService] = ChatService()
        self.d[ActionService] = ActionService()
        self.d[RoleService] = RoleService()
        self.d[EcoBalanceService] = EcoBalanceService()
        self.d[UnitGroupService] = UnitGroupService()
        self.d[PathingService] = PathingService()
        self.d[ChatInterface] = config.get(ChatInterface)()
        self.d[SupplyMechanicInterface] = config.get(SupplyMechanicInterface)()
        self.d[SpendingInterface] = config.get(SpendingInterface)()
        self.d[SpendingActionsInterface] = config.get(SpendingActionsInterface)()
        self.d[ResourceManagerInterface] = config.get(ResourceManagerInterface)()
        #self.d[ArmyTacticsManagerInterface] = config.get(ArmyTacticsManagerInterface)()
        #self.d[ArmyMicroManagerInterface] = config.get(ArmyMicroManagerInterface)()
        #self.d[ArmyStrategyManagerInterface] = config.get(ArmyStrategyManagerInterface)()
        self.d[QueenManagerInterface] = config.get(QueenManagerInterface)()
        self.d[UnitManager_v3] = UnitManager_v3()
        self.d[LogicInterface] = config.get(LogicInterface)()

    def inject(self, injectable) -> any:
        return self.d[injectable]

        
injector = Injector()
inject = injector.inject