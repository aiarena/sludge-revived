from sc2 import UnitTypeId

''' - To calculate these accurately, use unit tester [or bot vs bot if micro matters significantly] and see ratio (own_army_value/enemy_army_value)
of resources needed to just barely win consistently and then put it here.
    - Smaller numbers are better. Think about how about 9 zerglings (225 resources) beats
    1 immortal (375 resources). That means that you only need 0.6 of what an immortal costs to beat it with zerglings.
    - If the efficiency of one unit to another is 100, that unit is considered completely ineffective (and never considered)
    - Add a comment like #is_tested or something of the sort if you actually do the testing for the matchup,
    otherwise everything is just what we feel like it is.'''
#TODO think of a good way to put a number relationship between units and enemy support units,
#e.g. high templar, warp prisms, sentries, etc.
unit_counters_zvz = {
    UnitTypeId.DRONE : {
        UnitTypeId.ZERGLING : 2.5,
        UnitTypeId.BANELING : 5,
        UnitTypeId.QUEEN : 5,
        UnitTypeId.ROACH : 5, #tested
        UnitTypeId.RAVAGER : 5,
        UnitTypeId.HYDRALISK : 5,
        UnitTypeId.LURKER : 5,
        UnitTypeId.INFESTOR : 5,
        UnitTypeId.SWARMHOSTMP : 5, #TODO check if this is the right tag for swarm hosts
        UnitTypeId.ULTRALISK : 5,

        UnitTypeId.MUTALISK : 5,
        UnitTypeId.CORRUPTOR : 5,
        UnitTypeId.BROODLORD : 5,
        UnitTypeId.VIPER : 5
    },

    UnitTypeId.ZERGLING : {
        UnitTypeId.DRONE : 0.4,
        UnitTypeId.ZERGLING : 1,
        UnitTypeId.BANELING : 1,
        UnitTypeId.QUEEN : 1,
        UnitTypeId.ROACH : 0.775, #tested
        UnitTypeId.RAVAGER : 1,
        UnitTypeId.HYDRALISK : 1,
        UnitTypeId.LURKER : 1,
        UnitTypeId.INFESTOR : 1,
        UnitTypeId.SWARMHOSTMP : 1, #TODO check if this is the right tag for swarm hosts
        UnitTypeId.ULTRALISK : 1,

        UnitTypeId.MUTALISK : 3,
        UnitTypeId.CORRUPTOR : 0.1,
        UnitTypeId.BROODLORD : 3,
        UnitTypeId.VIPER : 1
    },

    UnitTypeId.BANELING : {
        UnitTypeId.DRONE : 0.2,
        UnitTypeId.ZERGLING : (4/7)
    },

    UnitTypeId.ROACH :{
        UnitTypeId.DRONE : 0.2,
        UnitTypeId.ZERGLING : 1.2903, #tested
        UnitTypeId.HYDRALISK : 0.667 #tested
    },

    UnitTypeId.RAVAGER :{
        UnitTypeId.DRONE : 0.2,
        UnitTypeId.ZERGLING : 2.5806,
        UnitTypeId.ROACH : 1.7
    },

    UnitTypeId.HYDRALISK : {
        UnitTypeId.DRONE : 0.2,
        UnitTypeId.ROACH : 1.5, #tested
        UnitTypeId.MUTALISK : 0.675, #tested
    },
}

unit_counters_zvp = {
    UnitTypeId.DRONE : {
        UnitTypeId.PHOTONCANNON : 1.25,
        UnitTypeId.PYLON: 1.25, 

        UnitTypeId.ZEALOT : 5, 
        UnitTypeId.ADEPT : 5, 
        UnitTypeId.SENTRY : 5,
        UnitTypeId.STALKER : 5, 
        UnitTypeId.HIGHTEMPLAR : 5,
        UnitTypeId.DARKTEMPLAR : 5, 
        UnitTypeId.ARCHON : 5, 
        UnitTypeId.IMMORTAL : 5, 
        UnitTypeId.DISRUPTOR : 5,
        UnitTypeId.COLOSSUS : 5,

        UnitTypeId.PHOENIX : 5,
        UnitTypeId.ORACLE : 5,
        UnitTypeId.VOIDRAY : 5,
        UnitTypeId.CARRIER : 5,
        UnitTypeId.TEMPEST : 5,
        UnitTypeId.MOTHERSHIP : 5,
        UnitTypeId.WARPPRISM : 5
    },

    UnitTypeId.ZERGLING : {
        UnitTypeId.PROBE : 0.4,
        UnitTypeId.ZEALOT : 0.9, #tested
        UnitTypeId.ADEPT : 0.85, #tested
        UnitTypeId.SENTRY : 0.5,
        UnitTypeId.STALKER : (4/7), #tested
        UnitTypeId.HIGHTEMPLAR : 3,
        UnitTypeId.DARKTEMPLAR : 0.625, #tested
        UnitTypeId.ARCHON : 0.79688, #tested
        UnitTypeId.IMMORTAL : 0.55, #tested
        UnitTypeId.DISRUPTOR : 1.75,
        UnitTypeId.COLOSSUS : 3,

        UnitTypeId.PHOENIX : 0.3,
        UnitTypeId.ORACLE : 1.5,
        UnitTypeId.VOIDRAY : 1.2,
        UnitTypeId.CARRIER : 1.8,
        UnitTypeId.TEMPEST : 0.4,
        UnitTypeId.MOTHERSHIP : 0.5,
        UnitTypeId.WARPPRISM : 0.1
    },

    UnitTypeId.BANELING : {
        UnitTypeId.PROBE : 0.2,
        UnitTypeId.STALKER : 100,
        UnitTypeId.IMMORTAL : 100,
        UnitTypeId.COLOSSUS : 100,

        UnitTypeId.VOIDRAY : 1.2,
        UnitTypeId.WARPPRISM : 0.1
    },

    UnitTypeId.QUEEN : {
        UnitTypeId.PROBE : 0.2,
        UnitTypeId.VOIDRAY : 0.6,
        UnitTypeId.WARPPRISM : 3
    },

    UnitTypeId.ROACH : {
        UnitTypeId.PROBE : 0.2,
        UnitTypeId.ZEALOT : 0.8,
        UnitTypeId.ADEPT : 0.7,
        UnitTypeId.IMMORTAL : 1.6, #tested
        UnitTypeId.COLOSSUS : 1,

        UnitTypeId.VOIDRAY : 3,
        UnitTypeId.WARPPRISM : 0.1
    },

    UnitTypeId.RAVAGER : {
        UnitTypeId.PROBE : 0.2,
        UnitTypeId.SENTRY : 0.6,
        UnitTypeId.COLOSSUS : 1,

        UnitTypeId.VOIDRAY : 2.7,
        UnitTypeId.WARPPRISM : 0.1
    },

    UnitTypeId.HYDRALISK : {
        UnitTypeId.PROBE : 0.2,
        UnitTypeId.STALKER : (6/7),
        UnitTypeId.IMMORTAL : 0.96, #tested
        UnitTypeId.COLOSSUS : 1.5,

        UnitTypeId.VOIDRAY : 0.75,
        UnitTypeId.WARPPRISM : 2
    },

    UnitTypeId.CORRUPTOR : {
        UnitTypeId.PROBE : 0.2,
        UnitTypeId.ZEALOT : 100,
        UnitTypeId.ADEPT : 100,
        UnitTypeId.IMMORTAL : 100,
        UnitTypeId.COLOSSUS : 0.9,

        UnitTypeId.VOIDRAY : 1.5625, #tested
        UnitTypeId.WARPPRISM : 1.5
    }
}

unit_counters_zvt = {
    UnitTypeId.DRONE : {
        UnitTypeId.MARINE : 2.5,
        UnitTypeId.MARAUDER : 2.5,
        UnitTypeId.REAPER : 5,
        UnitTypeId.GHOST : 5,
        UnitTypeId.HELLION : 5,
        UnitTypeId.HELLIONTANK : 5,
        UnitTypeId.SIEGETANK : 5,
        UnitTypeId.THOR : 5,
        UnitTypeId.WIDOWMINE : 5,

        UnitTypeId.BATTLECRUISER : 5,
        UnitTypeId.RAVEN : 5,
        UnitTypeId.MEDIVAC : 5,
        UnitTypeId.LIBERATOR : 5,
        UnitTypeId.VIKING : 5,
        UnitTypeId.BANSHEE : 5,

        UnitTypeId.BUNKER : 5
    },

    UnitTypeId.ZERGLING : {
        UnitTypeId.SCV : 0.4,
        UnitTypeId.MARINE : 1,
        UnitTypeId.MARAUDER : 1,
        UnitTypeId.REAPER : 1,
        UnitTypeId.GHOST : 1,
        UnitTypeId.HELLION : 1,
        UnitTypeId.HELLIONTANK : 1.5,
        UnitTypeId.SIEGETANK : 0.8,
        UnitTypeId.SIEGETANKSIEGED : 1.4,
        UnitTypeId.THOR : 1,
        UnitTypeId.WIDOWMINE : 1,

        UnitTypeId.BATTLECRUISER : 2,
        UnitTypeId.RAVEN : 0.5,
        UnitTypeId.MEDIVAC : 0.7,
        UnitTypeId.LIBERATOR : 0.3,
        UnitTypeId.VIKING : 0.1,
        UnitTypeId.BANSHEE : 1.2,

        UnitTypeId.BUNKER : 3
    },

    UnitTypeId.BANELING : {
        UnitTypeId.SCV : 0.2,
        UnitTypeId.BATTLECRUISER : 2,
        UnitTypeId.RAVEN : 0.5,
        UnitTypeId.MEDIVAC : 0.7,
        UnitTypeId.LIBERATOR : 0.3,
        UnitTypeId.VIKING : 0.1,
        UnitTypeId.BANSHEE: 1.2,

        UnitTypeId.BUNKER : 3
    },

    UnitTypeId.ROACH : {
        UnitTypeId.SCV : 0.2,
        UnitTypeId.MARINE : 1,
        UnitTypeId.MARAUDER : 1.2,
        UnitTypeId.REAPER : 1,
        UnitTypeId.GHOST : 1,
        UnitTypeId.HELLION : 0.8,
        UnitTypeId.HELLIONTANK : 0.8,
        UnitTypeId.SIEGETANK : 0.8,
        UnitTypeId.SIEGETANKSIEGED : 2,
        UnitTypeId.THOR : 1,
        UnitTypeId.WIDOWMINE : 1,

        UnitTypeId.BATTLECRUISER : 2,
        UnitTypeId.RAVEN : 0.5,
        UnitTypeId.MEDIVAC : 0.7,
        UnitTypeId.LIBERATOR : 0.7,
        UnitTypeId.VIKING : 0.1,
        UnitTypeId.BANSHEE : 1.5,

        UnitTypeId.BUNKER : 3
    },

    UnitTypeId.RAVAGER : {
        UnitTypeId.SCV : 0.2,
        UnitTypeId.MARINE : 1,
        UnitTypeId.MARAUDER : 1,
        UnitTypeId.REAPER : 1,
        UnitTypeId.GHOST : 1,
        UnitTypeId.HELLION : 1,
        UnitTypeId.HELLIONTANK : 1,
        UnitTypeId.SIEGETANK : 0.8,
        UnitTypeId.SIEGETANKSIEGED : 1.4,
        UnitTypeId.THOR : 1,
        UnitTypeId.WIDOWMINE : 1,

        UnitTypeId.BATTLECRUISER : 2,
        UnitTypeId.RAVEN : 0.5,
        UnitTypeId.MEDIVAC : 0.7,
        UnitTypeId.LIBERATOR : 0.7,
        UnitTypeId.VIKING : 0.1,
        UnitTypeId.BANSHEE : 1.5,

        UnitTypeId.BUNKER : 3
    },

    UnitTypeId.HYDRALISK : {
        UnitTypeId.SCV : 0.2,
        UnitTypeId.MARINE : 1.2,
        UnitTypeId.MARAUDER : 1,
        UnitTypeId.REAPER : 1,
        UnitTypeId.GHOST : 1,
        UnitTypeId.HELLION : 1,
        UnitTypeId.HELLIONTANK : 1,
        UnitTypeId.SIEGETANK : 0.8,
        UnitTypeId.SIEGETANKSIEGED : 1.4,
        UnitTypeId.THOR : 1,
        UnitTypeId.WIDOWMINE : 1,

        UnitTypeId.BATTLECRUISER : 1.1,
        UnitTypeId.RAVEN : 1,
        UnitTypeId.MEDIVAC : 1,
        UnitTypeId.LIBERATOR : 1,
        UnitTypeId.VIKING : 1,
        UnitTypeId.BANSHEE : 1,

        UnitTypeId.BUNKER : 3
    },

    UnitTypeId.CORRUPTOR : {
        UnitTypeId.SCV : 0.2,
        UnitTypeId.BATTLECRUISER : 0.9
    }
}