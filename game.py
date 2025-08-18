from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Optional color support
try:
    from colorama import init as color_init, Fore, Style
    color_init()
except Exception:
    def color_init():
        return None
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = _NoColor()
    Style = _NoColor()


# Game constants
ROWS = 14
COLS = 10
EMPTY = '·'
MAX_MOVES = 200

INITIAL_BOARD = [
    ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1'],
    ['A2', 'B2', 'C2', 'D2', 'I1', 'C2', 'D1', 'H1', 'A1', 'H1'],
    ['A3', 'E1', 'B3', 'B2', 'C3', 'G1', 'D3', 'E3', 'F3', 'G3'],
    ['A4', 'B4', 'C4', 'D1', 'D4', 'D3', 'G3', 'C1', 'B4', 'E4'],
    ['F1', 'C3', 'C4', 'I1', 'E1', 'A5', 'G3', 'F1', 'H1', 'A3'],
    ['G3', 'C1', 'B1', 'D4', 'B1', 'B4', 'A1', 'A4', 'E3', 'E1'],
    ['A6', 'B6', 'C2', 'C6', 'D6', 'A2', 'D4', 'D4', 'A4', 'B6'],
    ['A7', 'A7', 'D2', 'D6', 'A2', 'B7', 'C2', 'B1', 'G1', 'F3'],
    ['G1', 'A8', 'J1', 'B3', 'A6', 'A3', 'E3', 'D6', 'B8', 'B8'],
    ['D3', 'B2', 'A9', 'F1', 'B9', 'A2', 'B2', 'E4', 'B9', 'C6'],
    ['A8', 'A10', 'A10', 'A3', 'A8', 'A3', 'E4', 'B9', 'F3', 'F3'],
    ['E3', 'A4', 'A6', 'A11', 'A11', 'A5', 'E4', 'D6', 'A9', 'C3'],
    ['B3', 'D2', 'B9', 'A3', 'B3', 'A5', 'C6', 'A8', 'D3', 'D1'],
    ['A6', 'B7', 'B4', 'C6', 'C3', 'D2', 'C1', 'A5', 'A1', 'I1']
]


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def is_valid(self) -> bool:
        return 0 <= self.row < ROWS and 0 <= self.col < COLS

    def neighbors4(self) -> List["Position"]:
        cand = [
            Position(self.row, self.col + 1),
            Position(self.row, self.col - 1),
            Position(self.row + 1, self.col),
            Position(self.row - 1, self.col),
        ]
        return [p for p in cand if p.is_valid()]

    def manhattan(self, other: "Position") -> int:
        return abs(self.row - other.row) + abs(self.col - other.col)

    def __str__(self) -> str:
        return f"({self.row+1}, {self.col+1})"


@dataclass
class Move:
    start: Position
    end: Position
    piece: str
    eliminated_pairs: List[Tuple[Position, Position]]
    pushed_pieces: List[Tuple[str, Position, Position]]
    score: float = 0.0

    @property
    def is_in_place(self) -> bool:
        return self.start == self.end

    def __str__(self) -> str:
        if self.is_in_place:
            return f"原地消除 {self.piece} 在 {self.start}"
        return f"移动 {self.piece} 从 {self.start} 到 {self.end}"


class Board:
    def __init__(self, initial: Optional[List[List[str]]] = None) -> None:
        if initial is None:
            self.state = [[cell for cell in row] for row in INITIAL_BOARD]
        else:
            self.state = [[cell for cell in row] for row in initial]

    # ---------- Basic utilities ----------
    def in_bounds(self, pos: Position) -> bool:
        return pos.is_valid()

    def get(self, pos: Position) -> str:
        if not pos.is_valid():
            return EMPTY
        return self.state[pos.row][pos.col]

    def set(self, pos: Position, piece: str) -> None:
        if pos.is_valid():
            self.state[pos.row][pos.col] = piece

    def is_empty(self, pos: Position) -> bool:
        return self.get(pos) == EMPTY

    def count_pieces(self) -> int:
        return sum(1 for r in range(ROWS) for c in range(COLS) if self.state[r][c] != EMPTY)

    # ---------- Rendering ----------
    def print(self, title: str = "当前棋盘状态") -> None:
        print(f"\n{title}:")
        print('      ', end='')
        for i in range(COLS):
            print(f'{i+1:^4}', end='')
        print('\n    ' + '=' * (COLS * 4 + 2))

        for i in range(ROWS):
            print(f'{i+1:2d} | ', end='')
            for j in range(COLS):
                pos = Position(i, j)
                cell = self.get(pos)
                if cell == EMPTY:
                    print(f'{EMPTY:^4}', end='')
                else:
                    print(f'{cell:^4}', end='')
            print(' |')
        print('    ' + '=' * (COLS * 4 + 2))
        print(f"棋子数量: {self.count_pieces()}")

    # ---------- Rules ----------
    def can_connect(self, a: Position, b: Position) -> bool:
        if a.row == b.row:
            left, right = sorted([a.col, b.col])
            for c in range(left + 1, right):
                if not self.is_empty(Position(a.row, c)):
                    return False
            return True
        if a.col == b.col:
            top, bottom = sorted([a.row, b.row])
            for r in range(top + 1, bottom):
                if not self.is_empty(Position(r, a.col)):
                    return False
            return True
        return False

    def can_eliminate(self, a: Position, b: Position) -> bool:
        if not a.is_valid() or not b.is_valid():
            return False
        pa, pb = self.get(a), self.get(b)
        if pa == EMPTY or pb == EMPTY or pa != pb:
            return False
        return self.can_connect(a, b)

    def find_elimination_pairs(self) -> List[Tuple[Position, Position]]:
        pairs: List[Tuple[Position, Position]] = []
        # Check rows
        for r in range(ROWS):
            last: Dict[str, Optional[int]] = {}
            for c in range(COLS):
                pos = Position(r, c)
                cell = self.state[r][c]
                if cell == EMPTY:
                    continue
                if cell in last:
                    prev_c = last[cell]
                    if prev_c is not None:
                        if self.can_connect(Position(r, prev_c), pos):
                            pairs.append((Position(r, prev_c), pos))
                last[cell] = c
        # Check cols
        for c in range(COLS):
            last: Dict[str, Optional[int]] = {}
            for r in range(ROWS):
                pos = Position(r, c)
                cell = self.state[r][c]
                if cell == EMPTY:
                    continue
                if cell in last:
                    prev_r = last[cell]
                    if prev_r is not None:
                        if self.can_connect(Position(prev_r, c), pos):
                            pairs.append((Position(prev_r, c), pos))
                last[cell] = r
        return pairs

    # ---------- Move execution with pushing ----------
    def _try_execute_push(self, start: Position, end: Position, piece: str) -> Optional[List[Tuple[str, Position, Position]]]:
        # Axis aligned only
        dr = end.row - start.row
        dc = end.col - start.col
        if dr != 0 and dc != 0:
            return None
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)

        # Path before end must be empty
        cur = Position(start.row + step_r, start.col + step_c)
        while cur != end:
            if not self.is_empty(cur):
                return None
            cur = Position(cur.row + step_r, cur.col + step_c)

        pushed: List[Tuple[str, Position, Position]] = []
        if self.is_empty(end):
            # Simple slide
            self.set(end, piece)
            self.set(start, EMPTY)
            return pushed

        # Pushing chain from end towards direction
        chain: List[Position] = []
        scan = end
        while scan.is_valid() and not self.is_empty(scan):
            chain.append(scan)
            scan = Position(scan.row + step_r, scan.col + step_c)

        if not scan.is_valid() or not self.is_empty(scan):
            return None

        # Move chain backwards
        for idx in range(len(chain) - 1, -1, -1):
            src = chain[idx]
            dst = Position(src.row + step_r, src.col + step_c)
            p = self.get(src)
            self.set(dst, p)
            self.set(src, EMPTY)
            pushed.append((p, src, dst))

        # Place mover
        self.set(end, piece)
        self.set(start, EMPTY)
        return pushed

    def execute_move(self, move: Move) -> bool:
        # If in-place: eliminate one available pair
        if move.is_in_place:
            pairs = self.find_elimination_pairs()
            if not pairs:
                return False
            eliminated = self._eliminate_best_pair(pairs)
            if eliminated is not None:
                move.eliminated_pairs = [eliminated]
                return True
            return False

        start, end, piece = move.start, move.end, move.piece
        snapshot = [row[:] for row in self.state]
        pushed = self._try_execute_push(start, end, piece)
        if pushed is None:
            # invalid path
            return False

        pairs = self.find_elimination_pairs()
        # Only accept if the moved piece participates in at least one elimination
        valid_pairs = []
        for a, b in pairs:
            if (a == end) or (b == end):
                valid_pairs.append((a, b))

        if not valid_pairs:
            # rollback
            self.state = snapshot
            return False

        # perform elimination
        eliminated = self._eliminate_best_pair(valid_pairs)
        if eliminated is not None:
            move.eliminated_pairs = [eliminated]
        move.pushed_pieces = pushed
        return True

    # ---------- Elimination helpers ----------
    def _empty_between_in_row(self, a: Position, b: Position) -> int:
        if a.row != b.row:
            return 0
        left, right = sorted([a.col, b.col])
        return sum(1 for c in range(left + 1, right) if self.state[a.row][c] == EMPTY)

    def _empty_between_in_col(self, a: Position, b: Position) -> int:
        if a.col != b.col:
            return 0
        top, bottom = sorted([a.row, b.row])
        return sum(1 for r in range(top + 1, bottom) if self.state[r][a.col] == EMPTY)

    def _eliminate_best_pair(self, pairs: List[Tuple[Position, Position]]) -> Optional[Tuple[Position, Position]]:
        def score_pair(p: Tuple[Position, Position]) -> float:
            a, b = p
            kind = self.get(a)
            freq = sum(1 for r in range(ROWS) for c in range(COLS) if self.state[r][c] == kind)
            val = 6.0 / max(freq, 1)
            if a.row == b.row:
                val += 0.6 * self._empty_between_in_row(a, b)
            if a.col == b.col:
                val += 0.6 * self._empty_between_in_col(a, b)
            return val

        best = max(pairs, key=score_pair)
        a, b = best
        if self.can_eliminate(a, b):
            self.set(a, EMPTY)
            self.set(b, EMPTY)
            return (a, b)
        return None
    # ---------- Move generation and search ----------
    def generate_moves_one_step(self) -> List[Move]:
        # Generate only moves that immediately cause an elimination
        results: List[Move] = []
        budget = 600
        for r in range(ROWS):
            for c in range(COLS):
                start = Position(r, c)
                piece = self.get(start)
                if piece == EMPTY:
                    continue
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    steps = 1
                    while True:
                        end = Position(r + dr * steps, c + dc * steps)
                        if not end.is_valid():
                            break
                        tmp = Board(self.state)
                        mv = Move(start, end, piece, [], [])
                        if tmp.execute_move(mv):
                            mv.score = self._score_move(mv, tmp)
                            results.append(mv)
                        budget -= 1
                        if budget <= 0:
                            return results
                        steps += 1
        return results

    def _score_move(self, mv: Move, after: "Board") -> float:
        score = 0.0
        # direct elimination
        score += 18.0
        # future pairs
        score += len(after.find_elimination_pairs()) * 4.0
        # mobility proxy removed to avoid nested heavy generation
        # center bias
        center_r, center_c = ROWS // 2, COLS // 2
        score -= (abs(mv.end.row - center_r) + abs(mv.end.col - center_c)) * 0.2
        # corridor
        score += self._max_empty_run(after) * 0.06
        # pushing penalty
        score -= len(mv.pushed_pieces) * 1.5
        return score

    @staticmethod
    def _max_empty_run(b: "Board") -> int:
        best = 0
        for r in range(ROWS):
            cur = 0
            for c in range(COLS):
                if b.state[r][c] == EMPTY:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
        for c in range(COLS):
            cur = 0
            for r in range(ROWS):
                if b.state[r][c] == EMPTY:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
        return best

    def beam_search(self, depth: int = 2, width: int = 8) -> List[Move]:
        first_moves = self.generate_moves_one_step()
        if not first_moves:
            return []
        first_moves.sort(key=lambda m: m.score, reverse=True)
        first_moves = first_moves[:min(len(first_moves), 20)]

        beam: List[Tuple[float, List[Move], Board]] = []
        seen = set()
        for mv in first_moves:
            tmp = Board(self.state)
            if tmp.execute_move(mv):
                h = str(tmp.state)
                if h in seen:
                    continue
                seen.add(h)
                beam.append((self._eval_board(tmp), [mv], tmp))
        beam.sort(key=lambda x: x[0], reverse=True)
        beam = beam[:width]

        best_seq = beam[0][1] if beam else []
        d = 1
        while d < depth and beam:
            next_beam: List[Tuple[float, List[Move], Board]] = []
            level_seen = set()
            expansions = 0
            for score_so_far, seq, b in beam:
                cand = b.generate_moves_one_step()
                cand.sort(key=lambda m: m.score, reverse=True)
                cand = cand[:min(len(cand), 12)]
                for nm in cand:
                    nb = Board(b.state)
                    if nb.execute_move(nm):
                        h = str(nb.state)
                        if h in level_seen:
                            continue
                        level_seen.add(h)
                        new_seq = seq + [nm]
                        new_score = score_so_far + self._eval_board(nb)
                        next_beam.append((new_score, new_seq, nb))
                        expansions += 1
                        if expansions >= width * 12:
                            break
                if expansions >= width * 12:
                    break
            if not next_beam:
                break
            next_beam.sort(key=lambda x: x[0], reverse=True)
            beam = next_beam[:width]
            best_seq = beam[0][1]
            d += 1
        return best_seq

    @staticmethod
    def _eval_board(b: "Board") -> float:
        score = 0.0
        score -= b.count_pieces() * 1.0
        score += len(b.find_elimination_pairs()) * 4.0
        score += Board._max_empty_run(b) * 0.08
        return score


def run() -> None:
    board = Board()
    move_count = 0

    print("="*60)
    print("消除类游戏")
    print("="*60)
    print("\n游戏规则:")
    print("1. 棋子可以在行列两个方向上移动，只要没有其他的东西挡住")
    print("2. 移动时，可以将相邻的棋子一起移动")
    print("3. 移动的目的是逐步消除单元格内容。同行或同列上，两个单元格的内容相同，且他们之间没有其它物体挡住即可消除")
    print("4. 每次只能消除两个，但是有可能有两个选择。这时可以选择其中一个，如同行或同列来进行消除")
    print("5. 两个棋子满足消除的条件可能是初始化时就满足，也可能是消除其它棋子之后满足，也可能是移动之后才满足。但是如果移动棋子不满足消除条件，那么这个移动就不能进行")
    print("\n" + "="*60)

    print("\n初始棋盘状态：")
    board.print(title="初始棋盘")
    print(f"\n初始棋子数量：{board.count_pieces()}")
    print("\n" + "="*60 + "\n")

    while True:
        if board.count_pieces() % 2 != 0:
            print(f"错误：当前棋子数量为奇数 ({board.count_pieces()})！")
            break

        pairs = board.find_elimination_pairs()
        if pairs:
            move_count += 1
            print(f"\n第 {move_count} 步：")
            # 选择最优对消进行展示（不永久修改棋盘）
            snapshot = [row[:] for row in board.state]
            eliminated_preview = board._eliminate_best_pair(pairs.copy())
            if eliminated_preview is None:
                print("消除失败！")
                print("\n" + "="*60 + "\n")
                continue
            # 回滚到预览前的快照
            board.state = snapshot
            a, b = eliminated_preview
            kind = board.get(a)
            mv = Move(a, a, kind, [], [])
            if board.execute_move(mv):
                print(f"消除: {kind} 在 {a} 和 {b}")
                print(f"\n剩余棋子数量：{board.count_pieces()}")
            else:
                print("消除失败！")
            print("\n" + "="*60 + "\n")
            continue

        # Search for a move sequence; execute the first move of best sequence
        seq = board.beam_search(depth=3, width=10)
        if not seq:
            print("没有找到有效的移动，游戏结束！")
            break
        mv = seq[0]
        move_count += 1
        print(f"\n第 {move_count} 步：")
        print(f"移动: {mv}")
        if not board.execute_move(mv):
            print("移动失败，游戏结束！")
            break
        print(f"移动并消除完成，剩余棋子数量：{board.count_pieces()}")
        print("\n" + "="*60 + "\n")

        if move_count >= MAX_MOVES:
            print("达到最大移动次数，游戏结束！")
            break

    remaining = board.count_pieces()
    print("\n" + "="*60)
    print("游戏结束！")
    print("="*60)
    print(f"总共移动了 {move_count} 步")
    print(f"剩余 {remaining} 个棋子")
    print("\n最终棋盘状态：")
    board.print(title="最终棋盘状态")

