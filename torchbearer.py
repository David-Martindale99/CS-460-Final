"""
torchbearer.py  Navigation engine for the Torchbearer dungeon problem.

**Student Name:** David Martindale
**Student ID:** 134034196

Problem summary
---------------
Find a minimum-fuel walk in a weighted directed graph that starts at `spawn`,
visits every node in `relics` at least once, and ends at `exit_node`.

Approach
--------
1. Precompute cheapest pairwise distances between all locations the planner
   cares about (spawn + every relic) using Dijkstra's algorithm.
2. Use branch-and-bound DFS over all permutations of relic visit orders.
   A best-so-far bound and an admissible lower bound prune branches early.

Variable names used in Parts 5a/6:
    current_loc            node currently occupied
    relics_remaining       set of relics not yet collected
    relics_visited_order   list recording collection order (for the answer)
    cost_so_far            accumulated fuel spent to reach current_loc
    best                   mutable [best_cost, best_order] container

Submit this file as: torchbearer.py
"""

import heapq


# =======
# PART 1
# =======

def explain_problem():
    """
    Returns
    -------
    str
        Part 1 README answers as a string.
    """
    return (
        "Why a single shortest-path run from S is not enough: "
        "Dijkstra from S gives cheapest distances TO every node but cannot "
        "decide which order to visit the relic chambers, the ordering "
        "decision is entirely outside what one shortest-path run encodes.\n\n"
        "What decision remains after all inter-location costs are known: "
        "The order in which the Torchbearer visits the relic chambers; "
        "different orderings have different total fuel costs even when every "
        "individual leg uses the cheapest available path.\n\n"
        "Why this requires a search over orders: "
        "Because there is no local greedy criterion that guarantees the "
        "globally cheapest permutation, the optimal order can only be "
        "found by exploring (and pruning) the space of all orderings."
    )


# ========
# PART 2
# ========

def select_sources(spawn, relics, exit_node):
    """
    Return the set of nodes from which Dijkstra must be run.

    We need cheapest paths FROM spawn and FROM every relic (to reach the
    next relic or the exit).  The exit itself is never a departure point,
    so it is excluded unless it coincidentally equals spawn or a relic.

    Parameters
    ----------
    spawn : node
    relics : list[node]
    exit_node : node

    Returns
    -------
    list[node]
        Unique source nodes; order does not matter.
    """
    # Use a set to eliminate duplicates (e.g. if spawn == a relic).
    sources = set([spawn] + list(relics))
    return list(sources)


def run_dijkstra(graph, source):
    """
    Standard Dijkstra with a binary min-heap.

    Parameters
    ----------
    graph : dict[node, list[tuple[node, int]]]
        Adjacency list.  graph[u] = [(v, cost), ...].
        All edge costs are nonnegative integers.
    source : node

    Returns
    -------
    dict[node, float]
        dist[v] = minimum fuel cost from source to v.
        Unreachable nodes map to float('inf').
    """
    # Initialise every node to infinity; source costs 0.
    dist = {node: float('inf') for node in graph}
    dist[source] = 0

    # Min-heap: (tentative_distance, node)
    heap = [(0, source)]

    while heap:
        d, u = heapq.heappop(heap)

        # Skip stale heap entries (a shorter path was already finalised).
        if d > dist[u]:
            continue

        for v, weight in graph[u]:
            relaxed = dist[u] + weight
            if relaxed < dist[v]:
                dist[v] = relaxed
                heapq.heappush(heap, (relaxed, v))

    return dist


def precompute_distances(graph, spawn, relics, exit_node):
    """
    Run Dijkstra once from each required source and store all results.

    Parameters
    ----------
    graph : dict[node, list[tuple[node, int]]]
    spawn : node
    relics : list[node]
    exit_node : node

    Returns
    -------
    dict[node, dict[node, float]]
        dist_table[u][v] = cheapest fuel cost from u to v.
        Keyed by every source node (spawn + relics).
    """
    sources = select_sources(spawn, relics, exit_node)
    dist_table = {}
    for src in sources:
        dist_table[src] = run_dijkstra(graph, src)
    return dist_table


# =========
# PART 3
# =========

def dijkstra_invariant_check():
    """
    Returns
    -------
    str
        Part 3 README answers as a string.
    """
    return (
        "Part 3a  What the invariant means:\n"
        "Finalized nodes (in S): dist[v] is provably the true shortest-path "
        "distance from the source; it will never decrease again.\n"
        "Non-finalized nodes (not in S): dist[u] is the cheapest known path "
        "from the source to u whose every intermediate hop already belongs to S "
        " it is the best estimate given what has been settled so far.\n\n"

        "Part 3b  Why each phase holds:\n"
        "Initialization: before any iteration, S is empty and dist[source]=0 "
        "while all others are infinity; the shortest path of length 0 from the "
        "source to itself is trivially correct, and no internal vertices exist.\n"
        "Maintenance: the node u extracted from the heap has the smallest "
        "dist[u] among all unfinalized nodes; because every edge weight is "
        "nonnegative, no path that goes through an unfinalized node can ever "
        "produce a shorter route to u, so dist[u] is already final.\n"
        "Termination: when the heap is empty every node is in S, so every "
        "dist[v] is the true shortest-path distance from the source.\n\n"

        "Part 3c  Why this matters for the route planner:\n"
        "If any precomputed distance is wrong the planner will choose a relic "
        "visit order that appears cheap but actually costs more fuel, so "
        "correct Dijkstra output is a hard prerequisite for a correct plan."
    )


# ==========
# PART 4
# ========

def explain_search():
    """
    Returns
    -------
    str
        Part 4 README answers as a string.
    """
    return (
        "Why greedy fails:\n"
        "Failure mode: always picking the nearest unvisited relic commits to a "
        "local choice that forces expensive legs later, missing globally cheaper "
        "orderings.\n"
        "Counter-example setup (spec illustration): S-B costs 1, S-C costs 2; "
        "from B the only cheap exits are D(1) and T(1); from C the only cheap "
        "exits are B(1) and T(1).\n"
        "What greedy picks: S-B (nearest) then B-D-C-T = total 4 fuel.\n"
        "What optimal picks: in this particular instance greedy happens to tie "
        "with the optimal; a clearer failure occurs when the nearest first "
        "choice cuts off a cheaper overall sequence"
        "at cost 2 gives S-C-B-D-T = 5 while S-B-D-C-T = 4.\n"
        "Why greedy loses: the locally cheapest next step can create a situation "
        "where all subsequent legs are expensive, yielding a higher total cost.\n\n"
        "What the algorithm must explore:\n"
        "The algorithm must systematically explore every possible order in which "
        "the relic chambers can be visited, pruning branches whose lower-bound "
        "cost already exceeds the best order found so far."
    )


# ===============
# PARTS 5 + 6
# ===============

def find_optimal_route(dist_table, spawn, relics, exit_node):
    """
    Entry point for the branch-and-bound relic-ordering search.

    Parameters
    ----------
    dist_table : dict[node, dict[node, float]]
        Precomputed pairwise distances (output of precompute_distances).
    spawn : node
    relics : list[node]
    exit_node : node

    Returns
    -------
    tuple[float, list[node]]
        (minimum_fuel_cost, ordered_relic_list)
        Returns (float('inf'), []) if no valid route exists.
    """
    # Edge case: no relics – go straight to exit.
    if not relics:
        cost = dist_table[spawn].get(exit_node, float('inf'))
        return (cost, [])

    # best[0] = best total fuel found so far; best[1] = corresponding relic order.
    best = [float('inf'), []]

    # relics_remaining is the mutable set threaded through the recursion.
    relics_remaining = set(relics)

    _explore(
        dist_table,
        current_loc=spawn,
        relics_remaining=relics_remaining,
        relics_visited_order=[],
        cost_so_far=0.0,
        exit_node=exit_node,
        best=best,
    )

    return (best[0], best[1])


def _explore(dist_table, current_loc, relics_remaining, relics_visited_order,
             cost_so_far, exit_node, best):
    """
    Recursive branch-and-bound DFS for find_optimal_route.

    At each call the Torchbearer is at `current_loc`, has already spent
    `cost_so_far` fuel, and must still collect every node in `relics_remaining`
    before heading to `exit_node`.

    Parameters
    ----------
    dist_table   : dict[node, dict[node, float]]
    current_loc  : node    where the Torchbearer currently stands
    relics_remaining : set[node]  relics not yet collected (mutable; backtracked)
    relics_visited_order : list[node]  collection order so far (mutable; backtracked)
    cost_so_far  : float   fuel spent reaching current_loc
    exit_node    : node
    best         : list    [best_cost, best_order], updated in-place

    Returns
    -------
    None  (updates best in place)
    """

    # ------------------------------------------------------------------
    # BASE CASE: all relics collected, pay the cost to reach the exit.
    # ------------------------------------------------------------------
    if not relics_remaining:
        final_cost = cost_so_far + dist_table[current_loc].get(exit_node, float('inf'))
        if final_cost < best[0]:
            best[0] = final_cost
            best[1] = list(relics_visited_order)   # snapshot the winning order
        return

    # ------------------------------------------------------------------
    # PRUNING, lower-bound check (Part 6a / 6b).
    # ------------------------------------------------------------------
    # Lower bound on extra fuel needed:
    #   • We must travel from current_loc to at least one more relic
    #     (costs at least the cheapest such edge).
    #   • After visiting all remaining relics we must still reach exit_node
    #     (costs at least the cheapest dist from any remaining relic to exit).
    min_to_next_relic = min(
        dist_table[current_loc].get(r, float('inf'))
        for r in relics_remaining
    )
    min_relic_to_exit = min(
        dist_table[r].get(exit_node, float('inf'))
        for r in relics_remaining
    )
    lower_bound = cost_so_far + min_to_next_relic + min_relic_to_exit

    # Safety argument: the lower_bound never overestimates the true cost of
    # any completion of the current partial route, it uses only cheapest-possible
    # legs and ignores the cost of visiting the remaining relics between them.
    # Therefore, if lower_bound >= best[0], every completion of this branch costs
    # at least as much as the best solution already recorded, so pruning it cannot
    # discard the optimal solution.
    if lower_bound >= best[0]:
        return

    # ------------------------------------------------------------------
    # RECURSIVE CASE: try every remaining relic as the next stop.
    # ------------------------------------------------------------------
    for relic in list(relics_remaining):   # copy avoids mutation-during-iteration
        travel_cost = dist_table[current_loc].get(relic, float('inf'))
        if travel_cost == float('inf'):
            continue   # unreachable – skip this branch entirely

        new_cost = cost_so_far + travel_cost

        # Early cut: even arriving at this relic already beats nothing,
        # but check before recursing to save stack depth.
        if new_cost >= best[0]:
            continue

        # ---- Recurse ----
        relics_remaining.remove(relic)          # mark collected
        relics_visited_order.append(relic)

        _explore(
            dist_table,
            current_loc=relic,
            relics_remaining=relics_remaining,
            relics_visited_order=relics_visited_order,
            cost_so_far=new_cost,
            exit_node=exit_node,
            best=best,
        )

        # ---- Backtrack ----
        relics_visited_order.pop()
        relics_remaining.add(relic)             # unmark collected


# ===========
# PIPELINE
# ===========

def solve(graph, spawn, relics, exit_node):
    """
    Full pipeline: precompute distances, then find the optimal relic order.

    Parameters
    ----------
    graph      : dict[node, list[tuple[node, int]]]
    spawn      : node
    relics     : list[node]
    exit_node  : node

    Returns
    -------
    tuple[float, list[node]]
        (minimum_fuel_cost, ordered_relic_list)
        Returns (float('inf'), []) if no valid route exists.
    """
    dist_table = precompute_distances(graph, spawn, relics, exit_node)
    return find_optimal_route(dist_table, spawn, relics, exit_node)


# =============================================================================
# PROVIDED TESTS (do not modify)
# Graders will run additional tests beyond these.
# =============================================================================

def _run_tests():
    print("Running provided tests...")

    # Test 1: Spec illustration. Optimal cost = 4.
    graph_1 = {
        'S': [('B', 1), ('C', 2), ('D', 2)],
        'B': [('D', 1), ('T', 1)],
        'C': [('B', 1), ('T', 1)],
        'D': [('B', 1), ('C', 1)],
        'T': []
    }
    cost, order = solve(graph_1, 'S', ['B', 'C', 'D'], 'T')
    assert cost == 4, f"Test 1 FAILED: expected 4, got {cost}"
    print(f"  Test 1 passed  cost={cost}  order={order}")

    # Test 2: Single relic. Optimal cost = 5.
    graph_2 = {
        'S': [('R', 3)],
        'R': [('T', 2)],
        'T': []
    }
    cost, order = solve(graph_2, 'S', ['R'], 'T')
    assert cost == 5, f"Test 2 FAILED: expected 5, got {cost}"
    print(f"  Test 2 passed  cost={cost}  order={order}")

    # Test 3: No valid path to exit. Must return (inf, []).
    graph_3 = {
        'S': [('R', 1)],
        'R': [],
        'T': []
    }
    cost, order = solve(graph_3, 'S', ['R'], 'T')
    assert cost == float('inf'), f"Test 3 FAILED: expected inf, got {cost}"
    print(f"  Test 3 passed  cost={cost}")

    # Test 4: Relics reachable only through intermediate rooms.
    # Optimal cost = 6.
    graph_4 = {
        'S': [('X', 1)],
        'X': [('R1', 2), ('R2', 5)],
        'R1': [('Y', 1)],
        'Y': [('R2', 1)],
        'R2': [('T', 1)],
        'T': []
    }
    cost, order = solve(graph_4, 'S', ['R1', 'R2'], 'T')
    assert cost == 6, f"Test 4 FAILED: expected 6, got {cost}"
    print(f"  Test 4 passed  cost={cost}  order={order}")

    # Test 5: Explanation functions must return non-placeholder strings.
    for fn in [explain_problem, dijkstra_invariant_check, explain_search]:
        result = fn()
        assert isinstance(result, str) and result != "TODO" and len(result) > 20, \
            f"Test 5 FAILED: {fn.__name__} returned placeholder or empty string"
    print("  Test 5 passed  explanation functions are non-empty")

    print("\nAll provided tests passed.")


if __name__ == "__main__":
    _run_tests()
