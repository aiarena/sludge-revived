class PriorityQueue():
    def __init__(self):
        self.queue = []

    def __str__(self):
        return self.queue.__str__()

    def __iter__(self):
        for priority in self.queue:
            yield priority[0]

    def __len__(self):
        return len(self.queue)

    def iterate2(self):
        for priority in self.queue:
            yield priority

    def enqueue(self, element, priority):
        temp = self.queue.copy()
        if len(temp) == 0:
            self.queue.insert(0, (element, priority))
        for idx, elem in enumerate(temp):
            if elem[1] < priority:
                self.queue.insert(idx, (element, priority))
                break
            if idx == len(self.queue) - 1:
                self.queue.insert(idx+1, (element, priority))

    def dequeue(self):
        return self.queue.pop(0)

    def peek(self):
        return self.queue[0][0]

    def peek2(self):
        return self.queue[0]

    def delete(self, element):
        index = None
        for idx, e in enumerate(self.queue):
            if e[0] == element:
                index = idx
                break
        if index != None:
            del self.queue[index]

    def reprioritize(self, element, priority):
        self.delete(element)
        if priority > 0:
            self.enqueue(element, priority)

    def isEmpty(self):
        return len(self.queue) == 0

    def extend(self, other):
        for p in other.iterate2():
            self.enqueue(p[0], p[1])

    def filter(self, fun):
        new = PriorityQueue()
        for p in self.queue:
            if fun(p[0], p[1]):
                new.enqueue(p[0], p[1])
        return new