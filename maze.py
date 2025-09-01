import sys
from collections import deque
from heapq import heappush, heappop
from itertools import count


class Node:
    def __init__(self, state, parent=None, action=None, cost=0):
        # cost is the path cost g(n)
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost

    def __repr__(self):
        return f"Node(state={self.state}, cost={self.cost})"


class Frontier:
    """Abstract frontier. Subclasses should maintain a frontier_states set for O(1) contains checks."""
    def add(self, node, priority=None):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def empty(self):
        raise NotImplementedError

    def contains_state(self, state):
        raise NotImplementedError


class QueueFrontier(Frontier):
    def __init__(self):
        self.frontier = deque()
        self.frontier_states = set()

    def add(self, node, priority=None):
        if node.state not in self.frontier_states:
            self.frontier.append(node)
            self.frontier_states.add(node.state)

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        node = self.frontier.popleft()
        self.frontier_states.remove(node.state)
        return node

    def empty(self):
        return len(self.frontier) == 0

    def contains_state(self, state):
        return state in self.frontier_states


class PriorityQueueFrontier(Frontier):
    def __init__(self):
        # heap entries are tuples: (priority, count, node)
        self.frontier = []
        self.frontier_states = set()
        self._counter = count()

    def add(self, node, priority=None):
        # priority must be provided (f = g + h). If omitted, use node.cost
        if node.state in self.frontier_states:
            return
        pr = node.cost if priority is None else priority
        heappush(self.frontier, (pr, next(self._counter), node))
        self.frontier_states.add(node.state)

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        _, _, node = heappop(self.frontier)
        self.frontier_states.remove(node.state)
        return node

    def empty(self):
        return len(self.frontier) == 0

    def contains_state(self, state):
        return state in self.frontier_states

class Maze:
    def __init__(self, filename):
        with open(filename) as f:
            contents = f.read()

        if contents.count("A") != 1:
            raise Exception("maze must have exactly one start point")
        if contents.count("B") != 1:
            raise Exception("maze must have exactly one goal")

        contents = contents.splitlines()
        self.height = len(contents)
        self.width = max(len(line) for line in contents)

        self.walls = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                try:
                    if contents[i][j] == "A":
                        self.start = (i, j)
                        row.append(False)
                    elif contents[i][j] == "B":
                        self.goal = (i, j)
                        row.append(False)
                    elif contents[i][j] == " ":
                        row.append(False)
                    else:
                        row.append(True)
                except IndexError:
                    row.append(False)
            self.walls.append(row)

        self.solution = None
        # For visualization / debugging: keep exploration order
        self.explored_order = []

    def print(self):
        solution = self.solution[1] if self.solution is not None else None
        print()
        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                if col:
                    print("█", end="")
                elif (i, j) == self.start:
                    print("A", end="")
                elif (i, j) == self.goal:
                    print("B", end="")
                elif solution is not None and (i, j) in solution:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()
        print()

    def neighbors(self, state):
        row, col = state
        candidates = [
            ("up", (row - 1, col)),
            ("down", (row + 1, col)),
            ("left", (row, col - 1)),
            ("right", (row, col + 1))
        ]

        result = []
        for action, (r, c) in candidates:
            if 0 <= r < self.height and 0 <= c < self.width and not self.walls[r][c]:
                result.append((action, (r, c)))
        return result

    def solve(self, frontier_type='queue'):
        """
        Solve the maze. Supported frontier_type: 'bfs' (fast queue) and 'astar' (A* with Manhattan).
        This version records exploration order in self.explored_order for UI/visualization.
        """
        self.num_explored = 0
        start = Node(state=self.start, cost=0)
        self.explored = set()
        self.explored_order = []

        if frontier_type == 'bfs' or frontier_type == 'queue':
            frontier = QueueFrontier()
            frontier.add(start)
            is_astar = False
        elif frontier_type == 'astar':
            frontier = PriorityQueueFrontier()
            # For A*, add with priority = g + h
            h = self._manhattan(self.start, self.goal)
            frontier.add(start, priority=start.cost + h)
            is_astar = True
        else:
            raise ValueError("unknown frontier_type: use 'bfs' or 'astar'")

        while True:
            if frontier.empty():
                raise Exception("no solution")

            node = frontier.remove()
            self.num_explored += 1
            self.explored.add(node.state)
            self.explored_order.append(node.state)

            if node.state == self.goal:
                actions = []
                cells = []
                while node.parent is not None:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions, cells)
                return

            for action, state in self.neighbors(node.state):
                if state in self.explored or frontier.contains_state(state):
                    continue
                child = Node(state=state, parent=node, action=action, cost=node.cost + 1)
                if is_astar:
                    pr = child.cost + self._manhattan(child.state, self.goal)
                    frontier.add(child, priority=pr)
                else:
                    frontier.add(child)

    def _manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def output_image(self, filename, show_solution=True, show_explored=False):
        from PIL import Image, ImageDraw
        cell_size = 50
        cell_border = 2

        img = Image.new("RGBA", (self.width * cell_size, self.height * cell_size), "black")
        draw = ImageDraw.Draw(img)

        solution = self.solution[1] if self.solution is not None else None
        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                if col:
                    fill = (40, 40, 40)
                elif (i, j) == self.start:
                    fill = (255, 0, 0)
                elif (i, j) == self.goal:
                    fill = (0, 171, 28)
                elif solution is not None and show_solution and (i, j) in solution:
                    fill = (220, 235, 113)
                elif solution is not None and show_explored and (i, j) in self.explored:
                    fill = (212, 97, 85)
                else:
                    fill = (237, 240, 252)
                draw.rectangle(
                    ([(j * cell_size + cell_border, i * cell_size + cell_border),
                      ((j + 1) * cell_size - cell_border, (i + 1) * cell_size - cell_border)]),
                    fill=fill
                )

        img.save(filename)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python maze.py maze.txt")

    maze = Maze(sys.argv[1])
    print("Maze:")
    maze.print()
    print("Solving...")
    maze.solve()
    print("States Explored:", maze.num_explored)
    print("Solution:")
    maze.print()
    maze.output_image("maze.png", show_explored=True)


