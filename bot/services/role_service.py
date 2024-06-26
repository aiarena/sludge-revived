from typing import List, Union, Set

from bot.model.unit_role import UnitRole

class RoleService():
    def __init__(self):
        self.roles: dict[UnitRole, set] = {}
        for role in enumerate(UnitRole):
            self.roles[role[1]]: set = set()
        self.tags: dict[str, UnitRole] = {}

    def setRole(self, tag:Union[str, List, Set], role: UnitRole):
        if isinstance(tag, list) or isinstance(tag, set):
            for t in tag:
                self.setRole(t, role)
            return
        if tag in self.tags:
            old_role = self.tags[tag]
            old_role_tags = self.roles[old_role]
            if tag in old_role_tags:
                old_role_tags.remove(tag)
        self.roles[role].add(tag)
        self.tags[tag] = role

    def getRole(self, tag: str) -> UnitRole or None:
        if tag in self.tags:
            return self.tags[tag]
        else:
            return None

    def removeTag(self, tag: str) -> None:
        if self.tags[tag]:
            self.roles[self.tags[tag]].remove(tag)
            self.tags.pop(tag)
