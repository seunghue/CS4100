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


# ----------------------------
# Helper functions (agent-side)
# ----------------------------

# Add near the top of YOUR CODE HERE (you already import numpy; make sure random is imported too)
import random

# ----------------------------
# Helper functions (agent-side)
# ----------------------------

def export_state():
    return game.execute("export")

def count_adj_conflicts(g: np.ndarray) -> int:
    n = g.shape[0]
    c = 0
    for y in range(n):
        for x in range(n):
            if g[y, x] == -1:
                continue
            if x + 1 < n and g[y, x + 1] == g[y, x]:
                c += 1
            if y + 1 < n and g[y + 1, x] == g[y, x]:
                c += 1
    return c

# --- NEW: shape areas + big-shape incentive ---
SHAPE_AREAS = {0: 1, 1: 2, 2: 2, 3: 4, 4: 4, 5: 4, 6: 4, 7: 3, 8: 3}
BIG_SHAPES = [3, 4, 5, 6]
SMALL_SHAPES = [0, 1, 2, 7, 8]

def shape_cost(placed_shapes: list) -> float:
    # cheaper cost for larger shapes => incentivizes shapes 3/4/5/6
    return sum(1.0 / SHAPE_AREAS[s[0]] for s in placed_shapes)

def score_state(g: np.ndarray, placed_shapes: list) -> float:
    empties = int(np.sum(g == -1))
    conflicts = count_adj_conflicts(g)
    used_colors = len(set(int(v) for v in g.flatten() if v != -1))

    # correctness >> filling >> efficiency
    return (
        10000 * conflicts
        + 250 * empties
        + 20 * used_colors
        + 50 * shape_cost(placed_shapes)   # <-- big shapes cheaper
    )

# --- NEW: macro->micro schedule ---
def pick_shape_idx(grid: np.ndarray) -> int:
    empties = int(np.sum(grid == -1))
    n = grid.shape[0]
    total = n * n
    fill_progress = 1.0 - (empties / total)  # 0 early -> 1 late

    # Early: prefer big shapes heavily; late: shift toward small shapes
    p_big = 0.85 - 0.60 * fill_progress  # from ~0.85 down to ~0.25

    if random.random() < p_big:
        return random.choice(BIG_SHAPES)
    return random.choice(SMALL_SHAPES)

def move_brush_to(target_x: int, target_y: int):
    shapePos, curS, curC, g, ps, done = export_state()
    x, y = shapePos[0], shapePos[1]

    while x < target_x:
        shapePos, curS, curC, g, ps, done = game.execute("right")
        x = shapePos[0]
    while x > target_x:
        shapePos, curS, curC, g, ps, done = game.execute("left")
        x = shapePos[0]
    while y < target_y:
        shapePos, curS, curC, g, ps, done = game.execute("down")
        y = shapePos[1]
    while y > target_y:
        shapePos, curS, curC, g, ps, done = game.execute("up")
        y = shapePos[1]

def set_shape(target_shape_idx: int):
    shapePos, curS, curC, g, ps, done = export_state()
    while curS != target_shape_idx:
        shapePos, curS, curC, g, ps, done = game.execute("switchshape")

def set_color(target_color_idx: int):
    shapePos, curS, curC, g, ps, done = export_state()
    while curC != target_color_idx:
        shapePos, curS, curC, g, ps, done = game.execute("switchcolor")

def covered_cells(shape_arr: np.ndarray, pos):
    cells = []
    for i, row in enumerate(shape_arr):
        for j, cell in enumerate(row):
            if cell:
                cells.append((pos[0] + j, pos[1] + i))
    return cells

def best_color_for_placement(g: np.ndarray, cells) -> int:
    n = g.shape[0]
    best = None
    best_val = 10**9

    for color in range(4):
        add_conf = 0
        for (x, y) in cells:
            if x > 0 and g[y, x - 1] == color:
                add_conf += 1
            if x + 1 < n and g[y, x + 1] == color:
                add_conf += 1
            if y > 0 and g[y - 1, x] == color:
                add_conf += 1
            if y + 1 < n and g[y + 1, x] == color:
                add_conf += 1

        if add_conf < best_val:
            best_val = add_conf
            best = color

    return best if best is not None else 0

def restart_by_undoing_all():
    while True:
        shapePos, curS, curC, g, ps, done = export_state()
        if len(ps) == 0:
            return
        game.execute("undo")

# ----------------------------
# First-choice hill climbing
# ----------------------------

MAX_TRIES_PER_STEP = 60
STUCK_LIMIT = 400
timelimitsec = 30
stuck = 0

iteration = 0
while (time.time() - start < timelimitsec):
    shapePos, curS, curC, grid, placedShapes, done = export_state()
    if done:
        break

    cur_score = score_state(grid, placedShapes)
    iteration += 1
    if iteration % 200 == 0:
        _, _, _, g_dbg, ps_dbg, done_dbg = export_state()
        print("iter", iteration, "| shapes", len(ps_dbg), "| empties", int(np.sum(g_dbg == -1)), "| done", done_dbg, flush=True)


    improved = False

    for _ in range(MAX_TRIES_PER_STEP):
        for _ in range(MAX_TRIES_PER_STEP):
            n = grid.shape[0]
            
            s_idx = pick_shape_idx(grid)
            shape_arr = game.shapes[s_idx]

    # choose a valid anchor position for this shape
            h, w = shape_arr.shape
            x = random.randint(0, n - w)
            y = random.randint(0, n - h)
        
        # --- CHANGED: pick shape with macro->micro bias ---
        s_idx = pick_shape_idx(grid)
        shape_arr = game.shapes[s_idx]

        if not game.canPlace(grid, shape_arr, (x, y)):
            continue

        cells = covered_cells(shape_arr, (x, y))

        # skip if it doesn't paint any empty cells
        if all(grid[cy, cx] != -1 for (cx, cy) in cells):
            continue

        # color choice: still local heuristic
        c_idx = best_color_for_placement(grid, cells)

        move_brush_to(x, y)
        set_shape(s_idx)
        set_color(c_idx)

        prev_len = len(placedShapes)
        shapePos2, curS2, curC2, grid2, placedShapes2, done2 = game.execute("place")

        if len(placedShapes2) == prev_len:
            continue

        new_score = score_state(grid2, placedShapes2)

        if new_score < cur_score:
            improved = True
            break
        else:
            game.execute("undo")

    if improved:
        stuck = 0
    else:
        stuck += 1
        if stuck >= STUCK_LIMIT:
            restart_by_undoing_all()
            stuck = 0
    shapePos, curS, curC, grid, placedShapes, done = export_state()
    print("Finished. done =", done, "shapes =", len(placedShapes), "empties =", int(np.sum(grid == -1)))




'''

YOUR CODE HERE


'''





########################################

# Do not modify any of the code below. 

########################################

end=time.time()

np.savetxt('grid.txt', grid, fmt="%d")
with open("shapes.txt", "w") as outfile:
    outfile.write(str(placedShapes))
with open("time.txt", "w") as outfile:
    outfile.write(str(end-start))
