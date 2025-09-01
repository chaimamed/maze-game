"""Simple Tkinter GUI for the maze solver.

Features:
- Load a maze text file
- Choose BFS or A* (astar)
- Visualize the maze, solution, and exploration
- Step-through solve or auto-run

This GUI uses only the standard library + Pillow (for image saving which is optional).
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
import os

from maze import Maze

CELL_SIZE = 24
CELL_BORDER = 1


class MazeApp:
    def __init__(self, root):
        self.root = root
        root.title("Maze Solver")

        self.maze = None
        self.canvas = tk.Canvas(root, bg="black")
        self.canvas.grid(row=0, column=0, columnspan=4)

        tk.Button(root, text="Load Maze", command=self.load_maze).grid(row=1, column=0)
        self.algo_var = tk.StringVar(value="bfs")
        tk.Radiobutton(root, text="BFS", variable=self.algo_var, value="bfs").grid(row=1, column=1)
        tk.Radiobutton(root, text="A*", variable=self.algo_var, value="astar").grid(row=1, column=2)
        tk.Button(root, text="Solve", command=self.solve).grid(row=1, column=3)

        tk.Button(root, text="Step", command=self.step_solve).grid(row=2, column=0)
        tk.Button(root, text="Save Image", command=self.save_image).grid(row=2, column=1)
        tk.Button(root, text="Quit", command=root.quit).grid(row=2, column=3)

        self._solve_thread = None
        self._step_mode = False

    def load_maze(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*")])
        if not path:
            return
        try:
            self.maze = Maze(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._draw_maze()

    def _draw_maze(self, show_solution=True, show_explored=True):
        if not self.maze:
            return
        h = self.maze.height
        w = self.maze.width
        self.canvas.config(width=w * CELL_SIZE, height=h * CELL_SIZE)
        self.canvas.delete("all")

        sol = self.maze.solution[1] if self.maze.solution is not None else set()
        explored = set(self.maze.explored_order)

        for i in range(h):
            for j in range(w):
                x0 = j * CELL_SIZE + CELL_BORDER
                y0 = i * CELL_SIZE + CELL_BORDER
                x1 = (j + 1) * CELL_SIZE - CELL_BORDER
                y1 = (i + 1) * CELL_SIZE - CELL_BORDER
                if self.maze.walls[i][j]:
                    color = "#282828"
                elif (i, j) == self.maze.start:
                    color = "#ff3333"
                elif (i, j) == self.maze.goal:
                    color = "#00ab1c"
                elif (i, j) in sol and show_solution:
                    color = "#dceb71"
                elif (i, j) in explored and show_explored:
                    color = "#d46155"
                else:
                    color = "#edf0fc"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)

    def solve(self):
        if not self.maze:
            messagebox.showinfo("Info", "Load a maze first")
            return
        if self._solve_thread and self._solve_thread.is_alive():
            messagebox.showinfo("Info", "Solver already running")
            return
        self._step_mode = False
        algo = self.algo_var.get()
        self._solve_thread = threading.Thread(target=self._run_solver, args=(algo,))
        self._solve_thread.start()

    def _run_solver(self, algo):
        try:
            self.maze.solve(frontier_type=algo)
            self._draw_maze()
            messagebox.showinfo("Solved", f"Solved in {self.maze.num_explored} explored states")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def step_solve(self):
        if not self.maze:
            messagebox.showinfo("Info", "Load a maze first")
            return
        if self._solve_thread and self._solve_thread.is_alive():
            messagebox.showinfo("Info", "Solver already running")
            return
        # Run solver but paint after each explored state
        self.maze.explored = set()
        self.maze.explored_order = []
        self.maze.solution = None
        self._step_mode = True
        algo = self.algo_var.get()
        self._solve_thread = threading.Thread(target=self._run_solver_step, args=(algo,))
        self._solve_thread.start()

    def _run_solver_step(self, algo):
        # A copy of a simple BFS / A* that pauses to update the UI per step
        start = self.maze.start
        goal = self.maze.goal
        if algo == 'bfs':
            frontier = deque()
            frontier_states = set()
            frontier.append((start, None, 0))
            frontier_states.add(start)
        elif algo == 'astar':
            # reuse Maze.solve astar path would be similar; for stepping we keep it simple
            from heapq import heappush, heappop
            frontier = []
            heappush = heappush
            heappop = heappop
            heappush(frontier, (0, start, None, 0))
            frontier_states = {start}
        else:
            messagebox.showerror("Error", "Unknown algorithm for step mode")
            return

        parents = {start: None}
        costs = {start: 0}

        while frontier:
            if algo == 'bfs':
                state, _, _ = frontier.popleft()
                frontier_states.discard(state)
            else:
                _, state, _, _ = heappop(frontier)
                frontier_states.discard(state)

            self.maze.explored_order.append(state)
            self.maze.explored.add(state)
            self._draw_maze()
            time.sleep(0.05)

            if state == goal:
                # reconstruct
                node = state
                actions = []
                cells = []
                while parents[node] is not None:
                    prev = parents[node]
                    # find action from prev to node
                    for a, s in self.maze.neighbors(prev):
                        if s == node:
                            actions.append(a)
                            break
                    cells.append(node)
                    node = prev
                actions.reverse(); cells.reverse()
                self.maze.solution = (actions, cells)
                self._draw_maze()
                messagebox.showinfo("Solved (step)", f"Solved in {len(self.maze.explored_order)} explored states")
                return

            for action, nbr in self.maze.neighbors(state):
                if nbr in self.maze.explored or nbr in frontier_states:
                    continue
                parents[nbr] = state
                costs[nbr] = costs[state] + 1
                if algo == 'bfs':
                    frontier.append((nbr, state, costs[nbr]))
                    frontier_states.add(nbr)
                else:
                    pr = costs[nbr] + abs(nbr[0] - goal[0]) + abs(nbr[1] - goal[1])
                    heappush(frontier, (pr, nbr, state, costs[nbr]))
                    frontier_states.add(nbr)

        messagebox.showinfo("Info", "No solution found")

    def save_image(self):
        if not self.maze:
            messagebox.showinfo("Info", "Load a maze first")
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG image', '*.png')])
        if not path:
            return
        # use existing output_image function
        try:
            self.maze.output_image(path, show_solution=True, show_explored=True)
            messagebox.showinfo("Saved", f"Image saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == '__main__':
    root = tk.Tk()
    app = MazeApp(root)
    root.mainloop()
