# Berserker Chess — Variant Design & Engine Roadmap

## 1. Core Ruleset & Edge Cases

### Standard Berserker Chess (Immediate Bonus)
* **Core Mechanic:** Capturing an enemy piece grants **1 bonus move** immediately on the same turn.
* **Non-Stacking Cap:** Bonus moves do not stack—a player can take **at most 2 moves per turn** (Move 1: Capture $\rightarrow$ Move 2: Any legal move).
* **Check Rule (Forfeit Clause):** If Move 1 (the capture) puts the opponent's King in check, **the bonus move is immediately forfeited** and the turn ends. This preserves checkmate as the win condition rather than turning the game into "capture the King."
* **Piece Flexibility:** Any friendly piece (not just the capturing piece) can make the bonus move.
* **Special Captures:** *En passant* captures and promotion-captures both count as captures and trigger the bonus move (unless they deliver check).

### Variant 2: Banked Berserker Chess (Stored Tempo)
* **Core Mechanic:** Capturing an enemy piece adds **+1 Move Token** to that player's bank (`white_bank` / `black_bank`).
* **Spending Limit:** A player can hold unlimited tokens in their bank, but may spend **at most 1 banked move per turn** (capping any turn at 2 moves max).
* **Refund Rule (Optional Design Choice):** Decide whether capturing on a banked bonus move earns a new token (allowing multi-turn momentum chains) or if tokens can only be earned on the first action of a turn.
* **Check Rule:** Delivering check on Move 1 immediately ends the turn; the player cannot spend a banked move to capture the King.

---

## 2. Tactical & Strategic Dynamics
* **No Neutral Trades:** Initiating an equal trade gives the opponent a free tempo—they recapture (Move 1) and immediately develop, castle, or launch an attack (Move 2). Conversely, initiating a capture lets you retreat the attacker to safety on Move 2.
* **Poisoned Pawns Disappear:** Defended pieces are no longer safe just because they have a single defender; an attacker can capture and retreat on the same turn. Defenders must rely on pins, discovered attacks, and over-protection.
* **Increased Piece Mobility Value:** Knights and Queens gain massive value due to hit-and-run fork/retreat patterns.
* **Banking Endgame Threat:** In *Banked Berserker*, hoarding tokens in a cluttered middlegame lets a player unleash consecutive double-moves in an open endgame, creating severe Zugzwang pressure.

---

## 3. Five-Phase Engine & RL Development Plan

### Phase 1: Game Environment (`BerserkerBoard`)
* **Stack:** Python + `python-chess` (subclass `chess.Board`).
* **State Tracking:** Add `bonus_move_active: bool` and a `bonus_history` stack so `board.pop()` cleanly reverts state during tree searches.
* **For Banked Variant:** Track `white_bank: int`, `black_bank: int`, and `used_bank_this_turn: bool`. Add `chess.Move.null()` ("End Turn / Save Bank") to `legal_moves` whenever `bank > 0` and the player has already made their first move.

### Phase 2: Classical Baseline & Balance Sanity Check
* **Engine:** Depth-4 Alpha-Beta Pruning + **Quiescence Search** (mandatory so the search never terminates mid-turn with a pending bonus move).
* **Eval Function:** Standard material (`P=100, N=320, B=330, R=500, Q=900`) + standard Piece-Square Tables (PSTs).
* **Experiment:** Run 500–1,000 automated self-play games with a randomized 2-move opening book.
* **Viability Targets:**
  * White win rate between **50%–60%** (if >70%, nerf White's Turn 1 initiative).
  * Average game length between **25–50 moves**.

### Phase 3: Learned Static Evaluation (Discovering True Piece Values)
* **Goal:** Quantify how much piece values and hanging-piece penalties shift under Berserker rules.
* **Features ($\phi(s)$):** Piece counts, piece-square occupancy, count of undefended friendly pieces, available capture threats, and `white_bank - black_bank` (for Variant 2).
* **Training:** Generate 5,000+ self-play games and train a PyTorch linear/MLP model using **TD-Leaf ($\lambda$)** or **Sigmoid Cross-Entropy Loss** against final game outcomes ($y \in \{0, 0.5, 1\}$).
* **Benchmark:** Pit **Alpha-Beta + Learned Weights** vs. **Alpha-Beta + Traditional Weights** over 200 games.

### Phase 4: AlphaZero-Style RL + MCTS (`BerserkerNet`)
* **Input Tensor ($8 \times 8 \times 16$):**
  * Channels 0–11: Piece bitboards (6 White, 6 Black).
  * Channel 12: Active turn color.
  * Channel 13: `bonus_move_active` flag (all `1`s or `0`s).
  * Channels 14–15: Normalized `white_bank` and `black_bank` (for Variant 2).
* **Architecture:** 10-block ResNet (128 filters) with dual Policy ($p$) and Value ($v$) heads.
* **MCTS Modification:** When backpropagating values up the tree, **do not negate the value** across parent-child edges where `board.turn` stayed the same due to a bonus move.

### Phase 5: The Grand Tournament (The Pit)
Run a 300-game round-robin tournament comparing three paradigms:
1. **The Traditionalist:** Alpha-Beta + Standard Chess Eval.
2. **The Tuned Tactician:** Alpha-Beta + RL-Learned Eval Weights.
3. **Neural Instinct:** MCTS + ResNet (`BerserkerNet`).

---

## 4. Hardware Architecture & Setup (Windows Laptop + Arch Linux Desktop)

* **Windows Laptop (Core Ultra i5, 16GB RAM):** Use as primary dev environment (VS Code + Remote-SSH) for Phase 1 logic, unit tests, and PGN game viewing.
* **Arch Linux Desktop (Ryzen 7, 32GB RAM, AMD RX 7800 XT 16GB VRAM):** Use as headless compute server:
  * **Actors (Ryzen 7):** 8–12 parallel Python `multiprocessing` workers generating MCTS self-play games.
  * **Learner (RX 7800 XT):** Batched GPU inference and ResNet backpropagation (supports batch sizes of 512–1024 easily in 16GB VRAM).

### Arch Linux ROCm Setup Commands (RX 7800 XT / `gfx1101`)
```bash
# 1. Install ROCm runtime packages
sudo pacman -S hip-runtime-amd rocminfo

# 2. Symlink amdgpu.ids for precompiled PyTorch ROCm wheels
sudo mkdir -p /opt/amdgpu/share/libdrm
sudo ln -s /usr/share/libdrm/amdgpu.ids /opt/amdgpu/share/libdrm/amdgpu.ids

# 3. Create venv and install PyTorch with ROCm support
python -m venv .venv && source .venv/bin/activate
pip install torch torchvision --index-url [https://download.pytorch.org/whl/rocm6.4](https://download.pytorch.org/whl/rocm6.4)

# 4. Verify GPU visibility (maps to 'cuda' device in PyTorch)
python -c "import torch; print(torch.cuda.get_device_name(0))"