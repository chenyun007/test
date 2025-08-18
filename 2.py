import random
from copy import deepcopy
try:
    from colorama import init, Fore, Back, Style
except Exception:  # Fallback if colorama is not installed
    def init():
        return None
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = _NoColor()
    Back = _NoColor()
    Style = _NoColor()
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass

# 初始化colorama
init()

# 游戏常量
ROWS = 14
COLS = 10
EMPTY = '·'
MAX_MOVES = 70

# 初始棋盘布局
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

@dataclass
class Position:
    row: int
    col: int 

    def __hash__(self):
        return hash((self.row, self.col))

    def __eq__(self, other):
        if not isinstance(other, Position):
            return NotImplemented
        return self.row == other.row and self.col == other.col

    def is_valid(self) -> bool:
        return 0 <= self.row < ROWS and 0 <= self.col < COLS

    def distance_to(self, other: 'Position') -> int:
        return abs(self.row - other.row) + abs(self.col - other.col)

    def get_neighbors(self) -> List['Position']:
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_pos = Position(self.row + dr, self.col + dc)
            if new_pos.is_valid():
                neighbors.append(new_pos)
        return neighbors

    def __str__(self):
        return f"({self.row+1}, {self.col+1})"

class Move:
    def __init__(self, start: Position, end: Position, piece: str):
        self.start = start
        self.end = end
        self.piece = piece
        self.pushed_pieces: List[Tuple[str, Position, Position]] = []
        self.eliminated_pairs: List[Tuple[Position, Position]] = []
        self.score: float = 0.0
        self.move_path: List[Position] = []

    @property
    def is_in_place(self) -> bool:
        return self.start.row == self.end.row and self.start.col == self.end.col

    def __str__(self):
        if self.is_in_place:
            return f"原地消除 {self.piece} 在 {self.start}"
        return f"移动 {self.piece} 从 {self.start} 到 {self.end}"

    def get_detailed_description(self) -> str:
        if self.is_in_place:
            return f"原地消除 {self.piece} 在 {self.start}"
        
        desc = f"移动 {self.piece} 从 {self.start} 到 {self.end}"
        
        if self.pushed_pieces:
            desc += "\n推动的棋子："
            for piece, from_pos, to_pos in self.pushed_pieces:
                desc += f"\n  {piece}: {from_pos} → {to_pos}"
        
        if self.eliminated_pairs:
            desc += "\n消除的棋子对："
            for pos1, pos2 in self.eliminated_pairs:
                desc += f"\n  {pos1} 和 {pos2}"
        
        return desc

class Board:
    def __init__(self, initial_state=None):
        self.state = [[EMPTY] * COLS for _ in range(ROWS)]
        self.piece_groups = {}
        self.empty_clusters = []
        self.move_history = []
        
        if initial_state:
            self.state = [[cell for cell in row] for row in initial_state]
        else:
            self.initialize_board()
        
        self._update_piece_groups()
        self._update_empty_clusters()
        
    def initialize_board(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.state[row][col] = INITIAL_BOARD[row][col]
        
    def _update_piece_groups(self):
        self.piece_groups.clear()
        visited = set()

        def dfs(pos: Position, piece: str, group: List[Position]):
            if pos in visited:
                return
            visited.add(pos)
            group.append(pos)
            for next_pos in pos.get_neighbors():
                if (next_pos not in visited and 
                    next_pos.is_valid() and 
                    self.get_piece(next_pos) == piece):
                    dfs(next_pos, piece, group)

        for row in range(ROWS):
            for col in range(COLS):
                pos = Position(row, col)
                if pos not in visited and not self.is_empty(pos):
                    piece = self.get_piece(pos)
                    group = []
                    dfs(pos, piece, group)
                    if piece not in self.piece_groups:
                        self.piece_groups[piece] = []
                    self.piece_groups[piece].extend(group)

    def _update_empty_clusters(self):
        self.empty_clusters.clear()
        visited = set()

        def dfs(pos: Position, cluster: List[Position]):
            if pos in visited:
                return
            visited.add(pos)
            cluster.append(pos)
            for next_pos in pos.get_neighbors():
                if (next_pos not in visited and 
                    next_pos.is_valid() and 
                    self.is_empty(next_pos)):
                    dfs(next_pos, cluster)

        for row in range(ROWS):
            for col in range(COLS):
                pos = Position(row, col)
                if pos not in visited and self.is_empty(pos):
                    cluster = []
                    dfs(pos, cluster)
                    self.empty_clusters.append(cluster)

    def get_piece(self, pos: Position) -> str:
        if not pos.is_valid():
            return EMPTY
        return self.state[pos.row][pos.col]

    def set_piece(self, pos: Position, piece: str) -> None:
        if pos.is_valid():
            self.state[pos.row][pos.col] = piece

    def is_empty(self, pos: Position) -> bool:
        return self.get_piece(pos) == EMPTY

    def count_pieces(self) -> int:
        return sum(1 for row in self.state for cell in row if cell != EMPTY)

    def print_board(self, highlight_positions: Dict[Position, str] = None, title: str = "当前棋盘状态"):
        if highlight_positions is None:
            highlight_positions = {}

        print(f"\n{title}:")
        print('      ', end='')
        for i in range(COLS):
            print(f'{i+1:^4}', end='')
        print('\n    ' + '=' * (COLS * 4 + 2))
        
        for i in range(ROWS):
            print(f'{i+1:2d} | ', end='')
            for j in range(COLS):
                pos = Position(i, j)
                cell = self.get_piece(pos)
                if cell == EMPTY:
                    print(f'{EMPTY:^4}', end='')
                else:
                    if pos in highlight_positions:
                        color = highlight_positions[pos]
                        print(f'{color}{Fore.WHITE}{cell:^4}{Style.RESET_ALL}', end='')
                    else:
                        print(f'{cell:^4}', end='')
            print(' |')
        print('    ' + '=' * (COLS * 4 + 2))
        print(f"棋子数量: {self.count_pieces()}")

    def can_connect(self, pos1: Position, pos2: Position) -> bool:
        if pos1.row == pos2.row:  # 同行
            start, end = min(pos1.col, pos2.col), max(pos1.col, pos2.col)
            return all(self.is_empty(Position(pos1.row, col)) for col in range(start + 1, end))
        elif pos1.col == pos2.col:  # 同列
            start, end = min(pos1.row, pos2.row), max(pos1.row, pos2.row)
            return all(self.is_empty(Position(row, pos1.col)) for row in range(start + 1, end))
        return False

    def can_eliminate(self, pos1: Position, pos2: Position) -> bool:
        if not (pos1.is_valid() and pos2.is_valid()):
            return False

        piece1 = self.get_piece(pos1)
        piece2 = self.get_piece(pos2)

        if piece1 == EMPTY or piece2 == EMPTY or piece1 != piece2:
            return False

        return self.can_connect(pos1, pos2)

    def find_elimination_pairs(self) -> List[Tuple[Position, Position]]:
        elimination_pairs = []
        
        for piece, positions in self.piece_groups.items():
            if len(positions) < 2:
                continue
            for i, pos1 in enumerate(positions):
                for pos2 in positions[i+1:]:
                    if self.can_eliminate(pos1, pos2):
                        elimination_pairs.append((pos1, pos2))
        
        return elimination_pairs

    def execute_move(self, move: Move) -> bool:
        if move.is_in_place:
            pairs = self.find_elimination_pairs()
            if pairs:
                move.eliminated_pairs = [pairs[0]]
                eliminated_count = self.eliminate_pairs([pairs[0]])
                self.move_history.append(move)
                return eliminated_count > 0
            return False
        else:
            # 保存原始状态，若移动后不能产生消除则回滚
            original_state = [row[:] for row in self.state]
            original_groups = {k: v[:] for k, v in self.piece_groups.items()}
            original_empty = [cluster[:] for cluster in self.empty_clusters]

            self._execute_move_with_pushing(move)

            pairs = self.find_elimination_pairs()
            valid_pairs = []
            for pair in pairs:
                pos1, pos2 = pair
                if (pos1.row == move.end.row and pos1.col == move.end.col) or \
                   (pos2.row == move.end.row and pos2.col == move.end.col):
                    valid_pairs.append(pair)

            if valid_pairs:
                move.eliminated_pairs = [valid_pairs[0]]
                self.eliminate_pairs([valid_pairs[0]])
                self.move_history.append(move)
                return True
            else:
                # 回滚
                self.state = original_state
                self.piece_groups = original_groups
                self.empty_clusters = original_empty
                move.eliminated_pairs = []
                return False

    def _execute_move_with_pushing(self, move: Move) -> None:
        move.pushed_pieces.clear()
        move.move_path.clear()

        dr = move.end.row - move.start.row
        dc = move.end.col - move.start.col

        if dr != 0:
            dr = dr // abs(dr)
        if dc != 0:
            dc = dc // abs(dc)

        # 仅允许直线移动
        if dr != 0 and dc != 0:
            return

        # 路径（不含终点）必须为空
        path_pos = Position(move.start.row + dr, move.start.col + dc)
        while path_pos != move.end:
            if not self.is_empty(path_pos):
                return
            move.move_path.append(path_pos)
            path_pos = Position(path_pos.row + dr, path_pos.col + dc)
        move.move_path.append(move.end)

        start_piece = move.piece
        end_piece = self.get_piece(move.end)

        if end_piece == EMPTY:
            # 普通滑动
            self.set_piece(move.end, start_piece)
            self.set_piece(move.start, EMPTY)
        else:
            # 相邻推挤：从终点开始沿移动方向寻找第一个空位
            chain_positions = []
            check_pos = move.end
            while check_pos.is_valid() and not self.is_empty(check_pos):
                chain_positions.append(check_pos)
                check_pos = Position(check_pos.row + dr, check_pos.col + dc)

            # 无空位则无法推挤
            if not check_pos.is_valid() or not self.is_empty(check_pos):
                return

            # 从链尾开始依次向前移动一格
            for idx in range(len(chain_positions) - 1, -1, -1):
                from_pos = chain_positions[idx]
                to_pos = Position(from_pos.row + dr, from_pos.col + dc)
                piece_to_push = self.get_piece(from_pos)
                self.set_piece(to_pos, piece_to_push)
                self.set_piece(from_pos, EMPTY)
                move.pushed_pieces.append((piece_to_push, from_pos, to_pos))

            # 将起始棋子放入终点
            self.set_piece(move.end, start_piece)
            self.set_piece(move.start, EMPTY)

        self._update_piece_groups()
        self._update_empty_clusters()

    def _chain_push_from_position(self, start_pos: Position, dr: int, dc: int, move: Move):
        for check_dr, check_dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            if (check_dr == dr and check_dc == dc) or (check_dr == -dr and check_dc == -dc):
                continue
                
            neighbor_pos = Position(start_pos.row + check_dr, start_pos.col + check_dc)
            
            if neighbor_pos.is_valid() and not self.is_empty(neighbor_pos):
                if self._is_in_move_direction(neighbor_pos, start_pos, dr, dc):
                    self._push_piece_chain(neighbor_pos, dr, dc, move)

    def _is_in_move_direction(self, pos: Position, start_pos: Position, dr: int, dc: int) -> bool:
        # 当水平移动时，推动应作用于与起点同列的相邻棋子（上下方向）
        if dr == 0:  # 水平移动
            return pos.col == start_pos.col
        # 当垂直移动时，推动应作用于与起点同行的相邻棋子（左右方向）
        elif dc == 0:  # 垂直移动
            return pos.row == start_pos.row
        return False

    def _push_piece_chain(self, start_pos: Position, dr: int, dc: int, move: Move):
        current_pos = start_pos
        pushed_chain = []
        
        while current_pos.is_valid() and not self.is_empty(current_pos):
            pushed_chain.append(current_pos)
            current_pos = Position(current_pos.row + dr, current_pos.col + dc)
        
        if not current_pos.is_valid() or not self.is_empty(current_pos):
            return
        
        for i in range(len(pushed_chain) - 1, -1, -1):
            from_pos = pushed_chain[i]
            to_pos = Position(from_pos.row + dr, from_pos.col + dc)
            
            piece = self.get_piece(from_pos)
            move.pushed_pieces.append((piece, from_pos, to_pos))
            
            self.set_piece(to_pos, piece)
            self.set_piece(from_pos, EMPTY)

    def eliminate_pairs(self, pairs: List[Tuple[Position, Position]]) -> int:
        # 优先选择对后续更有利的那一对（如同类多/打通通道）
        if not pairs:
            return 0

        def pair_value(p: Tuple[Position, Position]) -> float:
            p1, p2 = p
            piece = self.get_piece(p1)
            # 少量种类优先清除（避免残子）
            freq = sum(1 for r in range(ROWS) for c in range(COLS) if self.state[r][c] == piece)
            value = 5.0 / max(freq, 1)
            # 行列通道潜力
            if p1.row == p2.row:
                value += 0.5 * (self._empty_between_in_row(p1, p2))
            if p1.col == p2.col:
                value += 0.5 * (self._empty_between_in_col(p1, p2))
            return value

        best_pair = max(pairs, key=pair_value)
        pos1, pos2 = best_pair
        eliminated_count = 0
        if self.can_eliminate(pos1, pos2):
            self.set_piece(pos1, EMPTY)
            self.set_piece(pos2, EMPTY)
            eliminated_count += 2

        if eliminated_count > 0:
            self._update_piece_groups()
            self._update_empty_clusters()

        return eliminated_count

    def _empty_between_in_row(self, p1: Position, p2: Position) -> int:
        if p1.row != p2.row:
            return 0
        left, right = sorted([p1.col, p2.col])
        return sum(1 for c in range(left + 1, right) if self.state[p1.row][c] == EMPTY)

    def _empty_between_in_col(self, p1: Position, p2: Position) -> int:
        if p1.col != p2.col:
            return 0
        top, bottom = sorted([p1.row, p2.row])
        return sum(1 for r in range(top + 1, bottom) if self.state[r][p1.col] == EMPTY)

    def find_valid_moves(self) -> List[Move]:
        # 优先使用束搜索，寻找对后续更有利的立即消除型移动
        beam_moves = self._beam_search_moves(max_depth=3, beam_width=10)
        if beam_moves:
            return [beam_moves[0]]

        # 回退到单步贪心（只返回立即消除的移动）
        candidate_moves = self._generate_immediate_elimination_moves()
        if candidate_moves:
            candidate_moves.sort(key=lambda m: m.score, reverse=True)
            return candidate_moves[:3]
        return []

    def _generate_immediate_elimination_moves(self) -> List[Move]:
        moves: List[Move] = []
        simulation_budget = 4000  # 上限，防止爆算（适当放宽）
        for piece, positions in self.piece_groups.items():
            for start_pos in positions:
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    steps = 1
                    while True:
                        end_row = start_pos.row + dr * steps
                        end_col = start_pos.col + dc * steps
                        end_pos = Position(end_row, end_col)

                        if not end_pos.is_valid():
                            break

                        temp_board = Board([row[:] for row in self.state])
                        temp_move = Move(start_pos, end_pos, piece)
                        if temp_board.execute_move(temp_move):
                            if temp_move.eliminated_pairs:
                                temp_move.score = self._evaluate_move_value(temp_move, temp_board)
                                moves.append(temp_move)
                        simulation_budget -= 1
                        if simulation_budget <= 0:
                            return moves
                        steps += 1
        return moves

    def _evaluate_board(self) -> float:
        # 局面评分：更少的棋子、更多潜在可消、更高机动性、更长空走廊
        score = 0.0
        remaining = self.count_pieces()
        score -= remaining * 1.0
        pairs = self.find_elimination_pairs()
        score += len(pairs) * 4.5
        mobility = len(self._generate_immediate_elimination_moves())
        score += mobility * 1.0
        score += self._max_empty_run() * 0.1
        # 中心性轻微约束
        center_row, center_col = ROWS // 2, COLS // 2
        for r in range(ROWS):
            for c in range(COLS):
                if self.state[r][c] != EMPTY:
                    score -= (abs(r - center_row) + abs(c - center_col)) * 0.03
        return score

    def _max_empty_run(self) -> int:
        # 统计行列中最长连续空位长度，用于鼓励打开走廊
        best = 0
        # 行
        for r in range(ROWS):
            cur = 0
            for c in range(COLS):
                if self.state[r][c] == EMPTY:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
        # 列
        for c in range(COLS):
            cur = 0
            for r in range(ROWS):
                if self.state[r][c] == EMPTY:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
        return best

    def _beam_search_moves(self, max_depth: int = 2, beam_width: int = 8) -> List[Move]:
        # 节点为(累计评分, move序列, 棋盘)
        initial_candidates = self._generate_immediate_elimination_moves()
        if not initial_candidates:
            return []

        # 限制初始候选数量（适当放宽）
        initial_candidates.sort(key=lambda m: m.score, reverse=True)
        initial_candidates = initial_candidates[:40]

        beam = []
        visited = set()
        for mv in initial_candidates:
            temp_board = Board([row[:] for row in self.state])
            if temp_board.execute_move(mv):
                state_hash = str(temp_board.state)
                if state_hash in visited:
                    continue
                visited.add(state_hash)
                beam.append((temp_board._evaluate_board(), [mv], temp_board))

        beam.sort(key=lambda x: x[0], reverse=True)
        beam = beam[:beam_width]

        best_sequence: List[Move] = beam[0][1] if beam else []

        depth = 1
        while depth < max_depth and beam:
            next_beam = []
            expansions = 0
            level_visited = set()
            for score_so_far, seq, b in beam:
                next_moves = b._generate_immediate_elimination_moves()
                # 仅扩展前若干高分移动（适当放宽）
                next_moves.sort(key=lambda m: m.score, reverse=True)
                next_moves = next_moves[:24]
                for nm in next_moves:
                    nb = Board([row[:] for row in b.state])
                    if nb.execute_move(nm):
                        state_hash = str(nb.state)
                        if state_hash in level_visited:
                            continue
                        level_visited.add(state_hash)
                        new_seq = seq + [nm]
                        new_score = score_so_far + nb._evaluate_board()
                        next_beam.append((new_score, new_seq, nb))
                        expansions += 1
                        if expansions >= beam_width * 24:
                            break
                if expansions >= beam_width * 24:
                    break
            if not next_beam:
                break
            next_beam.sort(key=lambda x: x[0], reverse=True)
            beam = next_beam[:beam_width]
            best_sequence = beam[0][1]
            depth += 1

        return best_sequence

    def _find_traditional_moves(self) -> List[Move]:
        all_moves = []
        for piece, positions in self.piece_groups.items():
            for start_pos in positions:
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    steps = 1
                    while True:
                        end_row = start_pos.row + dr * steps
                        end_col = start_pos.col + dc * steps
                        end_pos = Position(end_row, end_col)
                        
                        if not end_pos.is_valid() or not self.is_empty(end_pos):
                            break
                            
                        temp_board = Board([row[:] for row in self.state])
                        temp_board.set_piece(start_pos, EMPTY)
                        temp_board.set_piece(end_pos, piece)
                        temp_board._update_piece_groups()
                        
                        all_pairs = temp_board.find_elimination_pairs()
                        valid_pairs = []
                        for pair in all_pairs:
                            pos1, pos2 = pair
                            if (pos1.row == end_pos.row and pos1.col == end_pos.col) or \
                               (pos2.row == end_pos.row and pos2.col == end_pos.col):
                                valid_pairs.append(pair)
                        
                        if valid_pairs:
                            move = Move(start_pos, end_pos, piece)
                            move.eliminated_pairs = [valid_pairs[0]]
                            move.score = self._evaluate_move_value(move, temp_board)
                            all_moves.append(move)
                        
                        steps += 1

        if all_moves:
            all_moves.sort(key=lambda m: m.score, reverse=True)
            return all_moves[:3]

        return []

    def _evaluate_move_value(self, move: Move, temp_board: 'Board') -> float:
        score = 0.0
        score += 5.0

        # 直接消除收益
        if move.eliminated_pairs:
            score += len(move.eliminated_pairs) * 18.0
            # 稀有类型加成（以当前局面频次衡量）
            pos1, pos2 = move.eliminated_pairs[0]
            piece_kind = self.get_piece(move.start) if not move.is_in_place else self.get_piece(pos1)
            freq = sum(1 for r in range(ROWS) for c in range(COLS) if self.state[r][c] == piece_kind)
            if freq > 0:
                score += 6.0 / freq

        # 距离与推动成本
        if not move.is_in_place:
            distance = move.start.distance_to(move.end)
            score -= distance * 0.8
        score -= len(move.pushed_pieces) * 2.5

        # 新局面可消潜力与机动性
        new_pairs = temp_board.find_elimination_pairs()
        score += len(new_pairs) * 4.0
        mobility = len(temp_board._generate_immediate_elimination_moves())
        score += mobility * 1.2

        # 中心性与空走廊奖励
        center_row, center_col = ROWS // 2, COLS // 2
        center_distance = abs(move.end.row - center_row) + abs(move.end.col - center_col)
        score -= center_distance * 0.4
        score += temp_board._max_empty_run() * 0.08

        return score

    def _find_simple_moves(self) -> List[Move]:
        """更简单的移动检测方法，确保能找到基本移动"""
        all_moves = []
        
        # 遍历所有棋子
        for row in range(ROWS):
            for col in range(COLS):
                pos = Position(row, col)
                piece = self.get_piece(pos)
                if piece == EMPTY:
                    continue
                
                # 检查四个方向的移动
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    steps = 1
                    while True:
                        end_row = row + dr * steps
                        end_col = col + dc * steps
                        end_pos = Position(end_row, end_col)
                        
                        if not end_pos.is_valid() or not self.is_empty(end_pos):
                            break
                        
                        # 创建临时棋盘测试移动
                        temp_board = Board([row[:] for row in self.state])
                        temp_board.set_piece(pos, EMPTY)
                        temp_board.set_piece(end_pos, piece)
                        temp_board._update_piece_groups()
                        
                        # 检查是否有消除
                        elimination_pairs = temp_board.find_elimination_pairs()
                        if elimination_pairs:
                            move = Move(pos, end_pos, piece)
                            move.eliminated_pairs = [elimination_pairs[0]]
                            move.score = self._evaluate_move_value(move, temp_board)
                            all_moves.append(move)


                        
                        steps += 1
        
        if all_moves:
            all_moves.sort(key=lambda m: m.score, reverse=True)
            return all_moves[:3]
        
        return []

class TargetOrientedDFS:
    def __init__(self, board: Board):
        self.board = board
        self.stack = []
        self.visited_states = set()
        self.best_solution = []
        self.best_score = -1
        self.max_depth = 30
        
    def solve(self) -> List[Move]:
        print("开始目标导向深度优先搜索...")
        
        elimination_targets = self._get_elimination_targets()
        elimination_targets.sort(key=lambda x: self._evaluate_target_priority(x), reverse=True)
        
        for target in elimination_targets:
            print(f"尝试消除目标: {target}")
            solution = self._solve_for_target(target)
            if solution and len(solution) > len(self.best_solution):
                self.best_solution = solution
                print(f"找到更好的解决方案，长度: {len(solution)}")
        
        print(f"搜索完成，最佳解决方案长度: {len(self.best_solution)}")
        return self.best_solution
    
    def _get_elimination_targets(self) -> List[Tuple[Position, Position]]:
        targets = []
        direct_pairs = self.board.find_elimination_pairs()
        targets.extend(direct_pairs)
        
        for piece, positions in self.board.piece_groups.items():
            if len(positions) >= 2:
                for i, pos1 in enumerate(positions):
                    for pos2 in positions[i+1:]:
                        if self._can_create_elimination(pos1, pos2):
                            targets.append((pos1, pos2))
        
        return targets
    
    def _can_create_elimination(self, pos1: Position, pos2: Position) -> bool:
        piece = self.board.get_piece(pos1)
        
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            steps = 1
            while True:
                end_row = pos1.row + dr * steps
                end_col = pos1.col + dc * steps
                end_pos = Position(end_row, end_col)
                
                if not end_pos.is_valid() or not self.board.is_empty(end_pos):
                    break
                
                if self._can_eliminate_after_move(pos1, end_pos, pos2):
                    return True
                
                steps += 1
        
        return False
    
    def _can_eliminate_after_move(self, from_pos: Position, to_pos: Position, target_pos: Position) -> bool:
        piece = self.board.get_piece(from_pos)
        
        temp_board = Board([row[:] for row in self.board.state])
        temp_board.set_piece(from_pos, EMPTY)
        temp_board.set_piece(to_pos, piece)
        temp_board._update_piece_groups()
        
        return temp_board.can_eliminate(to_pos, target_pos)
    
    def _evaluate_target_priority(self, target: Tuple[Position, Position]) -> float:
        pos1, pos2 = target
        piece = self.board.get_piece(pos1)
        score = 0.0
        
        score += 10.0
        
        center_row, center_col = ROWS // 2, COLS // 2
        center_distance1 = abs(pos1.row - center_row) + abs(pos1.col - center_col)
        center_distance2 = abs(pos2.row - center_row) + abs(pos2.col - center_col)
        score -= (center_distance1 + center_distance2) * 0.5
        
        temp_board = Board([row[:] for row in self.board.state])
        temp_board.set_piece(pos1, EMPTY)
        temp_board.set_piece(pos2, EMPTY)
        temp_board._update_piece_groups()
        
        new_pairs = temp_board.find_elimination_pairs()
        score += len(new_pairs) * 5.0
        
        return score
    
    def _solve_for_target(self, target: Tuple[Position, Position]) -> List[Move]:
        pos1, pos2 = target
        piece = self.board.get_piece(pos1)
        
        self.stack = [(target, [], self.board.state.copy())]
        self.visited_states.clear()
        
        while self.stack:
            current_target, current_path, current_state = self.stack.pop()
            
            if len(current_path) >= self.max_depth:
                continue
            
            state_hash = self._get_state_hash(current_state)
            if state_hash in self.visited_states:
                continue
            self.visited_states.add(state_hash)
            
            temp_board = Board(current_state)
            
            if temp_board.can_eliminate(pos1, pos2):
                move = Move(pos1, pos1, piece)
                move.eliminated_pairs = [(pos1, pos2)]
                solution = current_path + [move]
                
                if len(solution) > len(self.best_solution):
                    self.best_solution = solution
                continue
            
            moves = self._find_moves_for_target(temp_board, target)
            
            if not moves:
                continue
            
            moves.sort(key=lambda m: self._evaluate_move_priority(m, temp_board), reverse=True)
            
            for move in moves:
                new_board = Board([row[:] for row in current_state])
                if new_board.execute_move(move):
                    new_path = current_path + [move]
                    self.stack.append((target, new_path, new_board.state))
        
        return self.best_solution
    
    def _find_moves_for_target(self, board: Board, target: Tuple[Position, Position]) -> List[Move]:
        moves = []
        pos1, pos2 = target
        target_piece = board.get_piece(pos1)
        
        for piece, positions in board.piece_groups.items():
            for start_pos in positions:
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    steps = 1
                    while True:
                        end_row = start_pos.row + dr * steps
                        end_col = start_pos.col + dc * steps
                        end_pos = Position(end_row, end_col)
                        
                        if not end_pos.is_valid() or not board.is_empty(end_pos):
                            break
                        
                        if self._move_helps_target(board, start_pos, end_pos, target):
                            move = Move(start_pos, end_pos, piece)
                            moves.append(move)
                        
                        steps += 1
        
        return moves
    
    def _move_helps_target(self, board: Board, from_pos: Position, to_pos: Position, target: Tuple[Position, Position]) -> bool:
        temp_board = Board([row[:] for row in board.state])
        temp_board.set_piece(from_pos, EMPTY)
        temp_board.set_piece(to_pos, board.get_piece(from_pos))
        temp_board._update_piece_groups()
        
        pos1, pos2 = target
        return temp_board.can_eliminate(pos1, pos2)
    
    def _evaluate_move_priority(self, move: Move, board: Board) -> float:
        score = 0.0
        score += 5.0
        
        distance = move.start.distance_to(move.end)
        score -= distance * 1.0
        
        center_row, center_col = ROWS // 2, COLS // 2
        center_distance = abs(move.end.row - center_row) + abs(move.end.col - center_col)
        score -= center_distance * 0.5
        
        temp_board = Board([row[:] for row in board.state])
        if temp_board.execute_move(move):
            new_pairs = temp_board.find_elimination_pairs()
            score += len(new_pairs) * 3.0
        
        return score
    
    def _get_state_hash(self, state: List[List[str]]) -> str:
        return str(state)

def play_game():
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
    board.print_board(title="初始棋盘")
    print(f"\n初始棋子数量：{board.count_pieces()}")
    print("\n" + "="*60 + "\n")

    while True:
        current_pieces = board.count_pieces()
        if current_pieces % 2 != 0:
            print(f"错误：当前棋子数量为奇数 ({current_pieces})！")
            break

        elimination_pairs = board.find_elimination_pairs()
        
        if elimination_pairs:
            pos1, pos2 = elimination_pairs[0]
            move_count += 1
            print(f"\n第 {move_count} 步：")
            
            piece = board.get_piece(pos1)
            move = Move(pos1, pos1, piece)
            move.eliminated_pairs = [(pos1, pos2)]
            
            before_state = [row[:] for row in board.state]
            
            success = board.execute_move(move)
            
            if success:
                print(f"消除: {piece} 在 {pos1} 和 {pos2}")
                print(f"\n剩余棋子数量：{board.count_pieces()}")
            else:
                print("消除失败！")
            
            print("\n" + "="*60 + "\n")
        else:
            valid_moves = board.find_valid_moves()
            if not valid_moves:
                print("没有找到有效的移动，游戏结束！")
                break

            # 尝试候选移动，执行第一个真正带来消除的移动
            executed = False
            for move in valid_moves:
                move_count += 1
                print(f"\n第 {move_count} 步：")
                print(f"移动: {move}")
                print()
                if board.execute_move(move):
                    print(f"移动并消除完成，剩余棋子数量：{board.count_pieces()}")
                    print("\n" + "="*60 + "\n")
                    executed = True
                    break
            if not executed:
                print("候选移动均未产生消除，游戏结束！")
                break

        if move_count >= MAX_MOVES:
            print("达到最大移动次数，游戏结束！")
            break

    remaining_pieces = board.count_pieces()
    print("\n" + "="*60)
    print("游戏结束！")
    print("="*60)
    print(f"总共移动了 {move_count} 步")
    print(f"剩余 {remaining_pieces} 个棋子")
    print("\n最终棋盘状态：")
    board.print_board(title="最终棋盘状态")

if __name__ == '__main__':
    play_game()
