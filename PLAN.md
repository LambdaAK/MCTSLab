# MCTSLab — Project Plan

## Vision

A **central MCTS framework** in Python that any game can plug into via a small, well-defined interface. We implement **UCT** first, with room for other variants later. Games can be **deterministic or stochastic**. Initial games: **Tic-tac-toe**, **Connect Four**, **2048**. Tooling for **learning, portfolio, and research** (stats, logging, optional visualization).

---

## 1. Game interface (contract)

Every game implements the same interface so the MCTS engine stays game-agnostic.

- **State representation**: Immutable (or copyable) state object; the framework never mutates it.
- **Actions**: From a state, we can ask for legal actions (list or generator).
- **Transition**: Given state + action → new state(s).
  - **Deterministic**: one new state.
  - **Stochastic**: one or more (state, probability) pairs; MCTS will sample or expect over these.
- **Terminal & outcome**: Is the state terminal? If so, what is the outcome (e.g. win/loss/draw, or numeric reward) for each player?
- **Current player**: Who acts in this state (e.g. player index or “chance”)?
- **Copy / hash**: Copy state for tree nodes; optional hash for transposition (later).

Abstractly:

```text
• get_current_player(state) -> player_id | "chance"
• get_legal_actions(state) -> list of actions
• apply_action(state, action) -> state (deterministic) or list of (state, prob) (stochastic)
• is_terminal(state) -> bool
• get_outcome(state) -> outcome per player (e.g. dict or tuple; only when terminal)
```

We’ll define this as an abstract base class (ABC) or protocol in Python so each game implements it.

---

## 2. MCTS framework (core)

- **Location**: Single package, e.g. `mcts/`, at the repo root.
- **Algorithm**: UCT (UCB1 for trees).
  - Selection: walk from root using UCB1 until we hit a node that has unvisited children or is terminal.
  - Expansion: add one (or more) child node(s). For **stochastic** games, “chance” nodes can be expanded by sampling one outcome (or we support explicit chance nodes in the tree).
  - Simulation (rollout): from the new node, play to termination (e.g. random or uniform random actions).
  - Backpropagation: update visit counts and total reward along the path.
- **Stochastic support**: 
  - When the current player is “chance”, we either sample one outcome and create one child, or add a chance node and then children for each outcome (with visit/reward propagated accordingly). Plan: start with “sample one chance outcome per expansion” for simplicity; we can add full chance-node handling later if needed.
- **Extensibility**: 
  - UCT in one module/class; pluggable selection (e.g. UCB1 formula) so we can swap in PUCT or other variants later without rewriting the whole tree.

Deliverables:

- `mcts/game.py` — Game interface (ABC or Protocol).
- `mcts/uct.py` — UCT implementation (selection, expansion, rollout, backprop).
- `mcts/node.py` — Tree node (state, parent, action, children, visits, total reward, etc.).
- `mcts/rollout.py` — Default rollout policy (e.g. uniform random); pluggable later.

---

## 3. Games layer

Separate package or folder, e.g. `games/`, with one module per game. Each game implements the central interface.

| Game           | Deterministic? | Notes |
|----------------|----------------|--------|
| Tic-tac-toe   | Yes            | Small state space; good for testing and debugging. |
| Connect Four  | Yes            | Larger; good for measuring UCT strength. |
| 2048          | No (stochastic)| Tile spawn is random; “chance” player after each move. |

- **Tic-tac-toe**: 3×3 board; two players; terminal = win/draw; outcome = +1 / -1 / 0 (or equivalent).
- **Connect Four**: 7 columns; two players; terminal = win/draw/full; same outcome style.
- **2048**: Single player vs “environment”. Outcome = score or win/loss flag. Chance node = random spawn (position + value 2 or 4). We can define “current player” as “player” or “chance” and implement `apply_action` for chance to return (state, prob) list or sample.

Each game exposes:

- A **State** type (or class) that implements the interface.
- Optional: factory or helpers to create initial state and run a game from CLI or a small runner script.

---

## 4. Tooling

- **Stats**: Per run or per move: total simulations, tree size (nodes), max depth, visit distribution of root children.
- **Logging**: Optional debug logs (e.g. chosen action, visit counts, UCB values) to help with learning and debugging.
- **Visualization** (optional, can be phased):
  - Tree stats (e.g. visits per root action) in text or simple ASCII.
  - Later: simple 2D tree view or export for external tools.
- **Runner scripts**: 
  - “Play game X with MCTS bot” (human vs bot or bot vs bot), with configurable time/simulations per move.

---

## 5. Directory structure (target)

```text
MCTSLab/
├── README.md
├── PLAN.md
├── pyproject.toml or requirements.txt
├── mcts/                    # Core framework
│   ├── __init__.py
│   ├── game.py              # Game interface (ABC/Protocol)
│   ├── node.py              # Tree node
│   ├── uct.py               # UCT algorithm
│   └── rollout.py           # Default rollout policy
├── games/                   # Game implementations
│   ├── __init__.py
│   ├── tictactoe.py
│   ├── connect_four.py
│   └── 2048.py
├── runners/ or scripts/     # Optional: play bots, benchmarks
│   └── play_tictactoe.py
└── tests/
    ├── test_mcts.py
    ├── test_tictactoe.py
    └── ...
```

---

## 6. Implementation order

1. **Game interface**  
   Define the ABC/Protocol and docstrings (and maybe a tiny dummy game in tests).

2. **Tree node + UCT (deterministic)**  
   Implement node and UCT assuming deterministic transitions only. No chance nodes yet.

3. **Tic-tac-toe**  
   Implement the interface; plug into MCTS; verify bot plays sensibly (e.g. never loses).

4. **Connect Four**  
   Same interface; tune simulations/time per move for a reasonable bot.

5. **Stochastic in MCTS**  
   Extend UCT (or add a small “chance” layer) so that when `get_current_player(state) == "chance"`, we sample from `apply_action` and expand accordingly. Document behavior for 2048.

6. **2048**  
   Model state (board + next spawn or RNG seed), chance outcomes for spawn; implement interface; run MCTS bot.

7. **Tooling**  
   Add stats (e.g. on root node), logging, and optional tree summary; runner scripts for playing.

8. **Later**  
   More games; other MCTS variants (e.g. PUCT); parallelism; optional neural net (policy/value).

---

## 7. Open design choices (to decide during implementation)

- **State hashing**: For games with transpositions (e.g. Connect Four), we may want to merge nodes by state hash. Start simple (no merging), add later if needed.
- **Chance nodes**: Start with “sample one outcome per expansion”; consider explicit chance nodes if we need better variance control or analysis.
- **2048 outcome**: Define “win” (e.g. reach 2048) and/or use raw score as reward for MCTS.

This plan should be enough to start coding the framework and the first game. If you want, next step can be: set up the repo structure + game interface + a minimal UCT and Tic-tac-toe so you can run a game end-to-end.
