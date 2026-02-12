import time
import numpy as np
from gridgame import *

##############################################################################################################################

# You can visualize what your code is doing by setting the GUI argument in the following line to true.
# The render_delay_sec argument allows you to slow down the animation, to be able to see each step more clearly.

# For your final submission, please set the GUI option to False.

# The gs argument controls the grid size. You should experiment with various sizes to ensure your code generalizes.
# Please do not modify or remove lines 18 and 19.

##############################################################################################################################

game = ShapePlacementGrid(GUI=False, render_delay_sec=0.0, gs=6, num_colored_boxes=5)
shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')
np.savetxt('initial_grid.txt', grid, fmt="%d")

##############################################################################################################################

# Initialization

# shapePos is the current position of the brush.

# currentShapeIndex is the index of the current brush type being placed (order specified in gridgame.py, and assignment instructions).

# currentColorIndex is the index of the current color being placed (order specified in gridgame.py, and assignment instructions).

# grid represents the current state of the board.

    # -1 indicates an empty cell
    # 0 indicates a cell colored in the first color (indigo by default)
    # 1 indicates a cell colored in the second color (taupe by default)
    # 2 indicates a cell colored in the third color (veridian by default)
    # 3 indicates a cell colored in the fourth color (peach by default)

# placedShapes is a list of shapes that have currently been placed on the board.

    # Each shape is represented as a list containing three elements: a) the brush type (number between 0-8),
    # b) the location of the shape (coordinates of top-left cell of the shape) and c) color of the shape (number between 0-3)

    # For instance [0, (0,0), 2] represents a shape spanning a single cell in the color 2=veridian, placed at the top left cell in the grid.

# done is a Boolean that represents whether coloring constraints are satisfied. Updated by the gridgames.py file.

##############################################################################################################################

shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')


print(shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done)


####################################################
# Timing your code's execution for the leaderboard.
####################################################

start = time.time()  # <- do not modify this.



##########################################
# Write all your code in the area below.
##########################################


import random
import math

# LLM use disclosure: I used an LLM to help brainstorm and polish this first-choice local search strategy.
# I reviewed and adapted the generated ideas/code to ensure it follows the assignment constraints.


def export_state():
    return game.execute("export")


def move_brush_to(target_x: int, target_y: int):
    shape_pos, _, _, _, _, _ = export_state()
    x, y = shape_pos[0], shape_pos[1]

    while x < target_x:
        shape_pos, _, _, _, _, _ = game.execute("right")
        x = shape_pos[0]
    while x > target_x:
        shape_pos, _, _, _, _, _ = game.execute("left")
        x = shape_pos[0]
    while y < target_y:
        shape_pos, _, _, _, _, _ = game.execute("down")
        y = shape_pos[1]
    while y > target_y:
        shape_pos, _, _, _, _, _ = game.execute("up")
        y = shape_pos[1]


def set_shape(target_shape_idx: int):
    _, cur_shape, _, _, _, _ = export_state()
    while cur_shape != target_shape_idx:
        _, cur_shape, _, _, _, _ = game.execute("switchshape")


def set_color(target_color_idx: int):
    _, _, cur_color, _, _, _ = export_state()
    while cur_color != target_color_idx:
        _, _, cur_color, _, _, _ = game.execute("switchcolor")


def covered_cells(shape_arr: np.ndarray, pos):
    cells = []
    for i, row in enumerate(shape_arr):
        for j, cell in enumerate(row):
            if cell:
                cells.append((pos[0] + j, pos[1] + i))
    return cells


def adjacent_conflicts_for_color(g: np.ndarray, cells, color_idx: int) -> int:
    n = g.shape[0]
    conflicts = 0
    for (x, y) in cells:
        if x > 0 and g[y, x - 1] == color_idx:
            conflicts += 1
        if x + 1 < n and g[y, x + 1] == color_idx:
            conflicts += 1
        if y > 0 and g[y - 1, x] == color_idx:
            conflicts += 1
        if y + 1 < n and g[y + 1, x] == color_idx:
            conflicts += 1
    return conflicts


def best_color_for_cells(g: np.ndarray, cells):
    colors = list(range(4))
    random.shuffle(colors)
    best_color = colors[0]
    best_val = 10**9

    for color in colors:
        val = adjacent_conflicts_for_color(g, cells, color)
        if val < best_val:
            best_val = val
            best_color = color

    return best_color, best_val


def count_adj_conflicts(g: np.ndarray) -> int:
    n = g.shape[0]
    conflicts = 0
    for y in range(n):
        for x in range(n):
            color = g[y, x]
            if color == -1:
                continue
            if x + 1 < n and g[y, x + 1] == color:
                conflicts += 1
            if y + 1 < n and g[y + 1, x] == color:
                conflicts += 1
    return conflicts


def score_state(g: np.ndarray, placed_shapes: list) -> float:
    empties = int(np.sum(g == -1))
    conflicts = count_adj_conflicts(g)
    colors_used = len(set(int(v) for v in g.flatten() if v != -1))

    # Strongly prioritize validity, then completion, then mild shape/color minimization.
    return 30000 * conflicts + 350 * empties + 4 * len(placed_shapes) + 8 * colors_used


def restart_by_undoing_all():
    while True:
        _, _, _, _, ps, _ = export_state()
        if not ps:
            return
        game.execute("undo")


def random_candidate(g: np.ndarray):
    n = g.shape[0]

    # Prefer larger sparse shapes early; bias toward 1x1 near the end for guaranteed closure.
    empties = int(np.sum(g == -1))
    progress = 1.0 - (empties / (n * n))

    if random.random() < 0.20 + 0.65 * progress:
        shape_idx = 0
    else:
        shape_idx = random.choice([1, 2, 3, 4, 5, 6, 7, 8])

    shape_arr = game.shapes[shape_idx]
    h, w = shape_arr.shape
    x = random.randint(0, n - w)
    y = random.randint(0, n - h)

    return shape_idx, shape_arr, (x, y)


def force_single_cell_progress(g: np.ndarray):
    empties = list(zip(*np.where(g == -1)))
    if not empties:
        return

    y, x = random.choice(empties)
    chosen_color, _ = best_color_for_cells(g, [(x, y)])

    move_brush_to(x, y)
    set_shape(0)
    set_color(chosen_color)
    game.execute("place")


MAX_NEIGHBORS_PER_STEP = 120
MAX_STUCK_STEPS = 140
MAX_RESTARTS = 14
time_limit_sec = 80

stuck_steps = 0
restarts = 0
iteration = 0

while time.time() - start < time_limit_sec:
    shapePos, cur_shape, cur_color, grid, placedShapes, done = export_state()
    if done:
        break

    current_score = score_state(grid, placedShapes)
    accepted = False

    # Decaying temperature for occasional uphill moves.
    temperature = max(0.35, 2.8 * math.exp(-iteration / 900.0))

    for _ in range(MAX_NEIGHBORS_PER_STEP):
        shape_idx, shape_arr, (x, y) = random_candidate(grid)

        if not game.canPlace(grid, shape_arr, (x, y)):
            continue

        cells = covered_cells(shape_arr, (x, y))
        if not any(grid[cy, cx] == -1 for (cx, cy) in cells):
            continue

        color_idx, _ = best_color_for_cells(grid, cells)

        move_brush_to(x, y)
        set_shape(shape_idx)
        set_color(color_idx)

        prev_len = len(placedShapes)
        _, _, _, grid2, placed2, done2 = game.execute("place")
        if len(placed2) == prev_len:
            continue

        new_score = score_state(grid2, placed2)
        delta = new_score - current_score

        if delta <= 0:
            accepted = True
            break

        # First-choice local search with stochastic acceptance of some worse neighbors.
        accept_prob = math.exp(-delta / (180.0 * temperature))
        if random.random() < accept_prob:
            accepted = True
            break

        game.execute("undo")

    if accepted:
        stuck_steps = 0
    else:
        stuck_steps += 1

        # Ensure monotonic progress when sampling gets unlucky.
        if stuck_steps % 8 == 0:
            _, _, _, g_now, _, done_now = export_state()
            if not done_now and np.any(g_now == -1):
                force_single_cell_progress(g_now)

        if stuck_steps >= MAX_STUCK_STEPS:
            restarts += 1
            if restarts > MAX_RESTARTS:
                break
            restart_by_undoing_all()
            stuck_steps = 0

    iteration += 1

shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = export_state()
print("Finished. done =", done, "shapes =", len(placedShapes), "empties =", int(np.sum(grid == -1)))





########################################

# Do not modify any of the code below.

########################################

end=time.time()

np.savetxt('grid.txt', grid, fmt="%d")
with open("shapes.txt", "w") as outfile:
    outfile.write(str(placedShapes))
with open("time.txt", "w") as outfile:
    outfile.write(str(end-start))
