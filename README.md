Maze project
===========

This repo contains a small maze solver and a Tkinter GUI to visualize and solve mazes.

Files:
- `maze.py` - optimized maze representation and solver (BFS and A* support).
- `maze_gui.py` - small Tkinter app to load mazes, choose algorithm, visualize exploration, step through solving, and save an image.
- `maze1.txt`, `maze2.txt`, `maze3.txt` - sample mazes.
- `requirements.txt` - Pillow is optional for image output.

Quick start (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
python maze_gui.py
```

Or run headless solver:

```powershell
python maze.py maze1.txt
```

Notes:
- The solver was refactored to use O(1) frontier contains checks and supports A* (manhattan heuristic).
- The GUI is intentionally lightweight and uses Tkinter (no extra dependencies besides Pillow for image export).

Next improvements you might want:
- Add unit tests for Maze parsing and solver correctness.
- Add more heuristics and a benchmark harness.
- Improve UI polish and controls (speed slider, animation pause/resume, etc.).
