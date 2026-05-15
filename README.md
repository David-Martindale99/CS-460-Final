# The Torchbearer

**Student Name:** David Martindale
**Student ID:** 134034196
**Course:** CS 460 – Algorithms | Spring 2026

## Part 1: Problem Analysis

- **Why a single shortest-path run from S is not enough:**
  Dijkstra from S yields the cheapest distance to every node but cannot determine the order in which to visit the relic chambers; the ordering decision is entirely outside what one shortest-path computation encodes.

- **What decision remains after all inter-location costs are known:**
  The order in which the Torchbearer visits the relic chambers; different orderings produce different total fuel costs even when every individual leg uses the globally cheapest available path.

- **Why this requires a search over orders (one sentence):**
  No single local criterion reliably identifies the globally cheapest permutation, so the algorithm must enumerate (and prune) the space of all possible relic-visit orders.

---

## Part 2: Precomputation Design

### Part 2a: Source Selection

| Source Node Type | Why it is a source |
|---|---|
| Entrance node (`spawn`) | The Torchbearer departs from here, so we need cheapest distances from spawn to every relic and to the exit. |
| Each relic chamber (`relics`) | After collecting one relic the Torchbearer departs from it toward the next relic or the exit, so cheapest distances from each relic are required. |

### Part 2b: Distance Storage

| Property | Your answer |
|---|---|
| Data structure name | Nested dictionary (`dict[node, dict[node, float]]`) |
| What the keys represent | Outer key: source node (spawn or relic); inner key: destination node (any dungeon location) |
| What the values represent | Minimum fuel cost (float) from the outer-key source to the inner-key destination |
| Lookup time complexity | O(1) average |
| Why O(1) lookup is possible | Python dictionaries are hash maps; given a source key and a destination key, the lookup resolves to a single hash probe at each level. |

### Part 2c: Precomputation Complexity

- **Number of Dijkstra runs:** k + 1 (one from spawn, one from each of the k relic chambers)
- **Cost per run:** O(m log n)
- **Total complexity:** O((k + 1) · m log n) = O(k · m log n)
- **Justification (one line):** We run one full Dijkstra per source node; sources are exactly spawn plus the k relics, giving k + 1 runs each costing O(m log n).

---

## Part 3: Algorithm Correctness

### Part 3a: What the Invariant Means

- **For nodes already finalized (in S):**
  Each finalized node's recorded distance is the true globally optimal cost from the source; no future relaxation step can ever lower it.

- **For nodes not yet finalized (not in S):**
  Each unfinalized node's current distance is the shortest path found so far whose every intermediate hop lies entirely within the already-settled set S; it is an optimistic estimate that may still be improved.

### Part 3b: Why Each Phase Holds

- **Initialization – why the invariant holds before iteration 1:**
  S is empty, dist[source] = 0 (correctly the shortest path of length zero), and all other nodes are set to infinity (no path yet discovered); both clauses of the invariant hold vacuously or trivially.

- **Maintenance – why finalizing the min-dist node is always correct:**
  The node u extracted from the heap has the smallest current estimate among all unfinalized nodes; because every edge weight is nonnegative, any alternative path to u that passes through an unfinalized node must travel at least dist[u] to reach that intermediate node and then add a nonnegative edge, so it cannot be cheaper; therefore dist[u] is already the true shortest distance and it is safe to move u into S.

- **Termination – what the invariant guarantees when the algorithm ends:**
  When the heap is empty every node has been moved into S, so the invariant's first clause applies universally: dist[v] is the true shortest-path distance from the source for every reachable node v in the graph.

### Part 3c: Why This Matters for the Route Planner

If any precomputed leg cost is wrong, the planner will select a relic visit order that appears optimal under those incorrect distances but is actually suboptimal or infeasible, so provably correct Dijkstra output is a hard prerequisite for producing a correct minimum-fuel route.

---

## Part 4: Search Design

### Why Greedy Fails

- **The failure mode:** Greedily choosing the nearest unvisited relic at each step commits to a locally cheap choice that can force expensive legs later, yielding a globally suboptimal total fuel cost.
- **Counter-example setup:** Using the spec illustration: S→B costs 1, S-C costs 2, S-D costs 2; from B, D costs 1 and T costs 1; from D, C costs 1 and B costs 1.
- **What greedy picks:** Starting at S, greedy picks B first (cost 1, cheapest neighbor), then D (cost 1), then C (cost 1), then T (cost 1) >> total 4.
- **What optimal picks:** The same route S to B to D to C to T = 4 is also optimal here; the greedy failure is illustrated by starting with C: S-C (2) >> B (1) >> D (1) >> T (1) = 5, which is worse than the greedy-from-nearest result above.
- **Why greedy loses:** A locally cheap first step (e.g. going to C at cost 2 thinking it opens short onward paths) can close off the shorter overall sequence, producing a higher total; without exploring all orderings there is no guarantee of global optimality.

### What the Algorithm Must Explore

- The algorithm must systematically explore every possible **order** in which the relic chambers can be visited, using a best-so-far bound and an admissible lower bound to prune orders that cannot improve upon the best solution already discovered.

---

## Part 5: State and Search Space

### Part 5a: State Representation

| Component | Variable name in code | Data type | Description |
|---|---|---|---|
| Current location | `current_loc` | node (any hashable type) | The dungeon room the Torchbearer occupies at this point in the search |
| Relics already collected | `relics_remaining` | `set[node]` | Mutable set of relics not yet visited; membership absence indicates collection |
| Fuel cost so far | `cost_so_far` | `float` | Total torch fuel spent traveling from spawn to `current_loc` along the path explored so far |

### Part 5b: Data Structure for Visited Relics

| Property | Your answer |
|---|---|
| Data structure chosen | Python `set` |
| Operation: check if relic already collected | Time complexity: O(1) average, `relic not in relics_remaining` is a hash-set lookup |
| Operation: mark a relic as collected | Time complexity: O(1) average, `relics_remaining.remove(relic)` |
| Operation: unmark a relic (backtrack) | Time complexity: O(1) average, `relics_remaining.add(relic)` |
| Why this structure fits | Constant-time membership, insertion, and deletion match the three operations needed per recursive call and backtrack step; the set also directly represents which relics remain without requiring a separate boolean array. |

### Part 5c: Worst-Case Search Space

- **Worst-case number of orders considered:** k! (k factorial), where k = |M|.
- **Why:** In the worst case (no pruning effective) the algorithm tries every permutation of the k relics, and there are exactly k! permutations of k distinct elements.

---

## Part 6: Pruning

### Part 6a: Best-So-Far Tracking

- **What is tracked:** A mutable two-element list `best = [best_cost, best_order]` where `best_cost` is the lowest complete-route fuel cost found so far and `best_order` is the corresponding relic visit sequence.
- **When it is used:** At the start of every recursive call, a lower bound on the cost of completing the current partial route is compared against `best[0]`; also updated whenever a complete route is found that beats the current best.
- **What it allows the algorithm to skip:** Any branch whose optimistic lower-bound completion cost is greater than or equal to `best[0]` is pruned entirely, avoiding all recursive calls that could only produce equal or worse solutions.

### Part 6b: Lower Bound Estimation

- **What information is available at the current state:** The fuel already spent (`cost_so_far`), the precomputed cheapest distances from `current_loc` to every remaining relic, and the precomputed cheapest distances from every remaining relic to `exit_node`.
- **What the lower bound accounts for:** The cheapest possible leg from `current_loc` to any one remaining relic, plus the cheapest possible direct connection from any remaining relic to the exit, these two values underestimate the cost of any legal completion.
- **Why it never overestimates:** Each term uses only the single minimum over precomputed shortest-path distances; the true cost of visiting all remaining relics and then reaching the exit must be at least as large as these individual minima, so the sum is always a lower bound (admissible).

### Part 6c: Pruning Correctness

- If the lower bound for a branch is ≥ `best[0]`, then every complete route reachable from that branch costs at least `best[0]` as well; since we are looking for a strictly better solution, no optimal solution can be hidden in that branch.
- Because the lower bound never overestimates the true completion cost, any branch that actually contains the optimal solution will always have a lower bound strictly less than the optimal cost until it is selected; therefore the pruning rule guarantees the optimal solution is never discarded.

---

## References

- Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.) Dijkstra's algorithm, Chapter 22.
- my course lecture notes for CS 549: Design and Analysis of Algorithms, SDSU.
- Python `heapq` module documentation: https://docs.python.org/3/library/heapq.html
