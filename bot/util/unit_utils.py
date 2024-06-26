from typing import List

from sc2.units import Units

def group_army(army: Units, distance: int) -> List[Units]:
    groups: List[Units] = []
    already_grouped_tags = []

    for unit in army:
        if unit.tag in already_grouped_tags:
            continue
        neighbors: Units = army.closer_than(distance, unit.position)
        groups.append(neighbors)
        already_grouped_tags.extend(neighbors.tags)
    
    return groups