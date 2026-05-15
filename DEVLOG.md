# Development Log – The Torchbearer

**Student Name:** David Martindale
**Student ID:** 134034196

## Entry 1 – 05/08/2026: Initial Plan

Before writing any code I read the spec carefully to understand the two-phase structure: first precompute cheapest pairwise distances, then search over relic visit orders. I plan to implement `run_dijkstra` first since everything else depends on it being correct, then wire up `precompute_distances`, and finally tackle the branch-and-bound search in `_explore`. The trickiest part will be designing an admissible lower bound for pruning, I want something cheap to compute but tight enough to actually cut branches. I'll validate each piece against the provided tests before moving on.

---

## Entry 2 – 05/10/2026: Bug with distance table keys and unreachable nodes

I hit a KeyError in `_explore` when trying to look up `dist_table[current_loc][exit_node]` for the base case. The problem was that `exit_node` was in the graph but Dijkstra had stored distances under every graph node, `exit_node` showed up as an inner key (destination) but I had not verified it was always present. The fix was straightforward: Dijkstra already initialises `dist` with every key in `graph`, so `exit_node` is always an inner key as long as it exists in the graph. I switched from a guarded `.get()` to direct dictionary access after confirming this invariant, which also removed a silent bug where I was defaulting to `float('inf')` in cases where the key should legitimately exist. I also discovered I was not skipping the branch when `travel_cost == float('inf')` inside the recursive case, causing needless recursion on unreachable nodes, added that early `continue` guard.

---

## Entry 3 – 05/12/2026: Tightening the lower bound

My initial lower bound was just `cost_so_far + min_dist_to_any_remaining_relic`, which was admissible but too loose, it left most branches alive and the pruning did almost nothing on larger inputs. I extended it to add `min_dist_from_any_relic_to_exit`, which accounts for the mandatory final leg to the exit. This cut the search tree noticeably on the four-relic manual test I constructed. I also added a cheap early-exit inside the loop (`if new_cost >= best[0]: continue`) before even recursing, which eliminates branches where we already overspend just arriving at the next relic. Both additions together make the pruning meaningfully effective without complicating the correctness argument.

---

## Entry 4 – 05/12/2026: Bug with duplicate source nodes corrupting dist_table

I noticed Test 1 was returning the right cost but occasionally a wrong relic order on repeated runs. Traced it to `select_sources`: when a relic node happened to equal `spawn` (I was testing a graph where the entrance is also a relic chamber), the function was returning it twice in the list. `precompute_distances` then ran Dijkstra twice from that node, the second run silently overwriting the first, no error, just wasted work. In this particular edge case the overwrite was harmless, but it masked, a real correctness hole: had I added any per-source state accumulation, the duplicate would have caused double-counting. Fixed by constructing the source list through a `set` before returning it, which deduplicates regardless of how the caller passes arguments.

---

## Entry 5 – 05/13/2026: Bug with backtracking - relics_visited_order not being restored

While testing a five-relic graph by hand I noticed the winning `best[1]` list sometimes contained six or seven entries instead of five. The bug was in the backtrack step: I had written `relics_visited_order.pop()` after the recursive call, but in an earlier draft I had also been passing `list(relics_visited_order)` as the argument rather than the live list, so the `.pop()` was operating on the copy, not the shared list, and the original kept growing with every recursive call. The fix was to always pass the same mutable list through every level and rely solely on `.append()` before and `.pop()` after each recursive call to keep it in sync. After the fix, `best[1]` always contained exactly k entries and matched the expected order on all manual test cases.

---

## Entry 6 – 05/14/2026: Post-Implementation Reflection

The implementation is complete and all five provided tests pass. With more time I would explore two improvements: (1) replacing the DFS branch-and-bound with a proper A\* or dynamic-programming-over-bitmask approach (classic TSP DP), which would reduce worst-case complexity from O(k! · k) to O(2^k · k^2) and handle larger relic sets gracefully; (2) adding memoization keyed on `(current_loc, frozenset(relics_remaining))` to avoid recomputing the same subproblem when two different orderings arrive at the same location with the same relics left. The current solution is correct and well-pruned for small k (≤ 10 or so), but the exponential worst case would matter for larger inputs.

---

## Final Entry – 05/14/2026: Time Estimate

Is this estimation supposed to be how many hours I think I have worked after the fact? Or a pre-estimation besed on how long i think a junior programmer (me) would take?
I have oppted for the former. An estimate on how long each part took me, in hindsight.

| Part | Estimated Hours |
|---|---|
| Part 1: Problem Analysis | 0.5 |
| Part 2: Precomputation Design | 1.0 |
| Part 3: Algorithm Correctness | 1.5 |
| Part 4: Search Design | 1.0 |
| Part 5: State and Search Space | 1.0 |
| Part 6: Pruning | 1.5 |
| Part 7: Implementation | 3.0 |
| README and DEVLOG writing | 1.5 |
| **Total** | **11.0** |

