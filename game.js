let hoverCellKey = null; // "r,c" | null

const DEBUG = true;
function dbg(...args) { if (DEBUG && typeof console !== 'undefined') console.log('[DBG]', ...args); }

const elBoard = document.getElementById('board');
const elMoveCount = document.getElementById('moveCount');
const elPieceCount = document.getElementById('pieceCount');
const elMessage = document.getElementById('message');
const elReset = document.getElementById('resetBtn');
const elShowPairs = document.getElementById('showPairsBtn');