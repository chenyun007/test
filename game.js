const ROWS = 14;
const COLS = 10;
const EMPTY = '·';

const INITIAL_BOARD = [
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
];

/** @type {string[][]} */
let board = [];
let moveCount = 0;

/** @type {{row: number, col: number} | null} */
let selected = null;
/** @type {Set<string>} */
let validMoveTargets = new Set();
/** @type {Set<string>} */
let eliminationCandidates = new Set();
let awaitingEliminationFrom = null; // {row, col} after a move
let dragging = null; // {from:{r,c}, current:{r,c}}
let hoverCellKey = null;

const elBoard = document.getElementById('board');
const elMoveCount = document.getElementById('moveCount');
const elPieceCount = document.getElementById('pieceCount');
const elMessage = document.getElementById('message');
const elReset = document.getElementById('resetBtn');
const elShowPairs = document.getElementById('showPairsBtn');

function cloneBoard(src) {
    return src.map(row => row.slice());
}

function resetGame() {
    board = cloneBoard(INITIAL_BOARD);
    moveCount = 0;
    selected = null;
    validMoveTargets.clear();
    eliminationCandidates.clear();
    awaitingEliminationFrom = null;
    render();
    setMessage('');
}

function setMessage(text, type = 'info') {
    elMessage.textContent = text;
    elMessage.style.color = type === 'error' ? '#ef4444' : type === 'ok' ? '#34d399' : '#9ca3af';
}

function pieceCount() {
    let count = 0;
    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            if (board[r][c] !== EMPTY) count++;
        }
    }
    return count;
}

function isEmpty(row, col) {
    return board[row][col] === EMPTY;
}

function inBounds(row, col) {
    return row >= 0 && row < ROWS && col >= 0 && col < COLS;
}

function canConnect(r1, c1, r2, c2) {
    // must be two distinct cells
    if (r1 === r2 && c1 === c2) return false;
    if (r1 === r2) {
        const start = Math.min(c1, c2) + 1;
        const end = Math.max(c1, c2);
        for (let cc = start; cc < end; cc++) {
            if (!isEmpty(r1, cc)) return false;
        }
        return true;
    }
    if (c1 === c2) {
        const start = Math.min(r1, r2) + 1;
        const end = Math.max(r1, r2);
        for (let rr = start; rr < end; rr++) {
            if (!isEmpty(rr, c1)) return false;
        }
        return true;
    }
    return false;
}

function getLetter(piece) {
    if (!piece || piece === EMPTY) return '';
    return piece.replace(/\d+.*/, '');
}

function render() {
    elBoard.innerHTML = '';
    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            const cell = document.createElement('div');
            const piece = board[r][c];
            const key = `${r},${c}`;

            cell.className = 'cell ' + (piece === EMPTY ? 'cell--empty' : 'cell--piece');
            if (piece !== EMPTY) {
                const letter = getLetter(piece);
                cell.dataset.letter = letter;
                const codeSpan = document.createElement('span');
                codeSpan.className = 'cell__code';
                codeSpan.textContent = piece;
                cell.appendChild(codeSpan);
            } else {
                cell.textContent = EMPTY;
            }

            if (selected && selected.row === r && selected.col === c) {
                cell.classList.add('cell--selected');
            }
            if (validMoveTargets.has(key)) {
                cell.classList.add('cell--valid-move');
            }
            if (eliminationCandidates.has(key)) {
                cell.classList.add('cell--candidate');
            }
            if (hoverCellKey === key) {
                cell.classList.add('cell--hover-target');
            }

            cell.addEventListener('click', () => onCellClick(r, c));
            cell.addEventListener('pointerdown', (e) => onPointerDown(e, r, c));
            cell.addEventListener('pointerenter', () => onPointerEnter(r, c));
            cell.addEventListener('pointerup', () => onPointerUp(r, c));
            elBoard.appendChild(cell);
        }
    }
    elMoveCount.textContent = String(moveCount);
    elPieceCount.textContent = String(pieceCount());
}

function clearHighlights() {
    validMoveTargets.clear();
    eliminationCandidates.clear();
}

function computeValidMoveTargets(from) {
    validMoveTargets.clear();
    const piece = board[from.row][from.col];
    if (!piece || piece === EMPTY) return;

    // Same row
    for (let c = 0; c < COLS; c++) {
        if (c === from.col) continue;
        if (isEmpty(from.row, c) && canConnect(from.row, from.col, from.row, c)) {
            validMoveTargets.add(`${from.row},${c}`);
        }
    }
    // Same col
    for (let r = 0; r < ROWS; r++) {
        if (r === from.row) continue;
        if (isEmpty(r, from.col) && canConnect(from.row, from.col, r, from.col)) {
            validMoveTargets.add(`${r},${from.col}`);
        }
    }
}

function computeEliminationCandidates(from) {
    eliminationCandidates.clear();
    const piece = board[from.row][from.col];
    if (!piece || piece === EMPTY) return;

    // Same row
    for (let c = 0; c < COLS; c++) {
        if (c === from.col) continue;
        if (board[from.row][c] === piece && canConnect(from.row, from.col, from.row, c)) {
            eliminationCandidates.add(`${from.row},${c}`);
        }
    }
    // Same col
    for (let r = 0; r < ROWS; r++) {
        if (r === from.row) continue;
        if (board[r][from.col] === piece && canConnect(from.row, from.col, r, from.col)) {
            eliminationCandidates.add(`${r},${from.col}`);
        }
    }
}

function afterMoveEliminationOptions(at) {
    // Find candidates against the moved piece position
    eliminationCandidates.clear();
    const piece = board[at.row][at.col];
    if (!piece || piece === EMPTY) return [];
    const options = [];

    // Row
    for (let c = 0; c < COLS; c++) {
        if (c === at.col) continue;
        if (board[at.row][c] === piece && canConnect(at.row, at.col, at.row, c)) {
            eliminationCandidates.add(`${at.row},${c}`);
            options.push({ row: at.row, col: c });
        }
    }
    // Col
    for (let r = 0; r < ROWS; r++) {
        if (r === at.row) continue;
        if (board[r][at.col] === piece && canConnect(at.row, at.col, r, at.col)) {
            eliminationCandidates.add(`${r},${at.col}`);
            options.push({ row: r, col: at.col });
        }
    }
    return options;
}

function doEliminate(pos1, pos2) {
    if (!inBounds(pos1.row, pos1.col) || !inBounds(pos2.row, pos2.col)) return false;
    if (pos1.row === pos2.row && pos1.col === pos2.col) return false;
    const piece1 = board[pos1.row][pos1.col];
    const piece2 = board[pos2.row][pos2.col];
    if (piece1 === EMPTY || piece1 !== piece2) return false;
    if (!canConnect(pos1.row, pos1.col, pos2.row, pos2.col)) return false;
    board[pos1.row][pos1.col] = EMPTY;
    board[pos2.row][pos2.col] = EMPTY;
    moveCount += 1;
    setMessage(`消除：${piece1} 在 (${pos1.row + 1}, ${pos1.col + 1}) 与 (${pos2.row + 1}, ${pos2.col + 1})`, 'ok');
    selected = null;
    clearHighlights();
    awaitingEliminationFrom = null;
    render();
    return true;
}

function tryMove(from, to) {
    // Only allow straight-line moves to empty cells with clear path
    if (!isEmpty(to.row, to.col)) return false;
    if (!canConnect(from.row, from.col, to.row, to.col)) return false;

    const piece = board[from.row][from.col];
    // Tentatively move
    const prev = cloneBoard(board);
    board[from.row][from.col] = EMPTY;
    board[to.row][to.col] = piece;

    const choices = afterMoveEliminationOptions(to);
    if (choices.length === 0) {
        // Rollback if no elimination can occur
        board = prev;
        setMessage('该移动不会产生消除，无法移动。', 'error');
        return false;
    }

    // Commit move and wait for elimination choice
    setMessage('请选择要消除的另一个棋子。', 'info');
    awaitingEliminationFrom = { row: to.row, col: to.col };
    selected = { row: to.row, col: to.col };
    validMoveTargets.clear();
    render();

    // Auto-eliminate if only one choice
    if (choices.length === 1) {
        doEliminate({ row: to.row, col: to.col }, choices[0]);
    }
    return true;
}

function onCellClick(r, c) {
    // If awaiting elimination, clicking a candidate performs elimination
    if (awaitingEliminationFrom) {
        const key = `${r},${c}`;
        if (eliminationCandidates.has(key)) {
            doEliminate(awaitingEliminationFrom, { row: r, col: c });
            return;
        }
    }

    const piece = board[r][c];

    // If no selection yet
    if (!selected) {
        if (piece === EMPTY) return;
        selected = { row: r, col: c };
        computeValidMoveTargets(selected);
        computeEliminationCandidates(selected);
        setMessage('选择一个空格移动，或点击可直连的相同棋子进行消除。');
        render();
        return;
    }

    const from = selected;
    const selPiece = board[from.row][from.col];

    // Clicking same cell toggles off
    if (from.row === r && from.col === c) {
        selected = null;
        clearHighlights();
        setMessage('');
        render();
        return;
    }

    // Try direct elimination if clicking a same-piece with clear path
    if (piece !== EMPTY && piece === selPiece && canConnect(from.row, from.col, r, c)) {
        doEliminate(from, { row: r, col: c });
        return;
    }

    // Try move if clicking an empty valid target
    const key = `${r},${c}`;
    if (piece === EMPTY && validMoveTargets.has(key)) {
        tryMove(from, { row: r, col: c });
        return;
    }

    // Otherwise, reselect if clicked another piece
    if (piece !== EMPTY) {
        selected = { row: r, col: c };
        computeValidMoveTargets(selected);
        computeEliminationCandidates(selected);
        setMessage('选择一个空格移动，或点击可直连的相同棋子进行消除。');
        render();
        return;
    }

    // Clicked an invalid empty cell
    setMessage('只能沿行/列移动至空格，且路径必须无阻挡。', 'error');
}

function onPointerDown(e, r, c) {
    if (awaitingEliminationFrom) return; // prevent dragging during elimination choice
    const piece = board[r][c];
    if (piece === EMPTY) return;
    dragging = { from: { row: r, col: c }, current: { row: r, col: c } };
    selected = { row: r, col: c };
    computeValidMoveTargets(selected);
    computeEliminationCandidates(selected);
    (e.currentTarget).setPointerCapture(e.pointerId);
}

function onPointerEnter(r, c) {
    if (!dragging) return;
    hoverCellKey = `${r},${c}`;
    render();
}

function onPointerUp(r, c) {
    if (!dragging) return;
    const from = dragging.from;
    dragging = null;
    let dropRow = r;
    let dropCol = c;
    if (hoverCellKey) {
        const [hr, hc] = hoverCellKey.split(',').map(Number);
        dropRow = hr; dropCol = hc;
    }
    const key = `${dropRow},${dropCol}`;
    hoverCellKey = null;

    // Prefer elimination if releasing on same-piece with clear path
    const piece = board[dropRow][dropCol];
    const fromPiece = board[from.row][from.col];
    if (piece !== EMPTY && piece === fromPiece && canConnect(from.row, from.col, dropRow, dropCol)) {
        doEliminate(from, { row: dropRow, col: dropCol });
        return;
    }
    // Otherwise try move if empty valid target
    if (isEmpty(dropRow, dropCol) && validMoveTargets.has(key)) {
        tryMove(from, { row: dropRow, col: dropCol });
        return;
    }
    // No-op
    render();
}

function showAnyPairs() {
    // Highlight one set of pairs available anywhere to hint the player
    clearHighlights();
    for (let r1 = 0; r1 < ROWS; r1++) {
        for (let c1 = 0; c1 < COLS; c1++) {
            const p = board[r1][c1];
            if (p === EMPTY) continue;
            for (let c2 = c1 + 1; c2 < COLS; c2++) {
                if (board[r1][c2] === p && canConnect(r1, c1, r1, c2)) {
                    eliminationCandidates.add(`${r1},${c1}`);
                    eliminationCandidates.add(`${r1},${c2}`);
                    render();
                    setMessage('存在可消除对（绿色高亮）。选择其中任意两个即可消除。');
                    return;
                }
            }
            for (let r2 = r1 + 1; r2 < ROWS; r2++) {
                if (board[r2][c1] === p && canConnect(r1, c1, r2, c1)) {
                    eliminationCandidates.add(`${r1},${c1}`);
                    eliminationCandidates.add(`${r2},${c1}`);
                    render();
                    setMessage('存在可消除对（绿色高亮）。选择其中任意两个即可消除。');
                    return;
                }
            }
        }
    }
    setMessage('当前没有可直接消除的配对。');
}

elReset.addEventListener('click', resetGame);
elShowPairs.addEventListener('click', showAnyPairs);

// Init
resetGame();

