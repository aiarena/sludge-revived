from ...util.priority_queue import PriorityQueue

class SpendingInterface():
    def get_current_priorities(self) -> PriorityQueue:
        raise NotImplementedError("Not implemented")
