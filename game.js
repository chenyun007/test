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

let board = [];
let moveCount = 0;

let selected = null; // {row, col} | null
let validMoveTargets = new Set(); // Set<string: "r,c">
let eliminationCandidates = new Set(); // Set<string: "r,c">
let awaitingEliminationFrom = null; // {row, col} | null
let dragging = null; // {from:{row,col}, current:{row,col}} | null
let hoverCellKey = null; // "r,c" | null

const DEBUG = true;
function dbg(...args) { if (DEBUG && typeof console !== 'undefined') console.log('[DBG]', ...args); }

const elBoard = document.getElementById('board');
const elMoveCount = document.getElementById('moveCount');
const elPieceCount = document.getElementById('pieceCount');
const elMessage = document.getElementById('message');
const elReset = document.getElementById('resetBtn');
const elShowPairs = document.getElementById('showPairsBtn');
const elCancel = document.getElementById('cancelBtn');

function cloneBoard(src) { return src.map(row => row.slice()); }

function resetGame() {
  board = cloneBoard(INITIAL_BOARD);
  moveCount = 0;
  selected = null;
  validMoveTargets.clear();
  eliminationCandidates.clear();
  awaitingEliminationFrom = null;
  dragging = null;
  hoverCellKey = null;
  render();
  setMessage('');
}

function setMessage(text, type = 'info') {
  elMessage.textContent = text;
  elMessage.style.color = type === 'error' ? '#ef4444' : type === 'ok' ? '#34d399' : '#9ca3af';
}

function pieceCount() { let n=0; for (let r=0;r<ROWS;r++){ for (let c=0;c<COLS;c++){ if (board[r][c]!==EMPTY) n++; } } return n; }
function isEmpty(r,c){ return board[r][c]===EMPTY; }
function inBounds(r,c){ return r>=0&&r<ROWS&&c>=0&&c<COLS; }

function canConnect(r1,c1,r2,c2){ if(r1===r2&&c1===c2)return false; if(r1===r2){ for(let cc=Math.min(c1,c2)+1;cc<Math.max(c1,c2);cc++){ if(!isEmpty(r1,cc))return false; } return true;} if(c1===c2){ for(let rr=Math.min(r1,r2)+1;rr<Math.max(r1,r2);rr++){ if(!isEmpty(rr,c1))return false; } return true;} return false; }

function getLetter(piece){ if(!piece||piece===EMPTY) return ''; return piece.replace(/\d+.*/, ''); }

function render(){
  elBoard.innerHTML='';
  for(let r=0;r<ROWS;r++){
    for(let c=0;c<COLS;c++){
      const cell=document.createElement('div');
      const piece=board[r][c];
      const key=`${r},${c}`;
      cell.className='cell ' + (piece===EMPTY?'cell--empty':'cell--piece');
      if(piece!==EMPTY){ const letter=getLetter(piece); cell.dataset.letter=letter; const s=document.createElement('span'); s.className='cell__code'; s.textContent=piece; cell.appendChild(s); } else { cell.textContent=EMPTY; }
      if(selected && selected.row===r && selected.col===c) cell.classList.add('cell--selected');
      if(validMoveTargets.has(key)) cell.classList.add('cell--valid-move');
      if(eliminationCandidates.has(key)) cell.classList.add('cell--candidate');
      if(hoverCellKey===key) cell.classList.add('cell--hover-target');
      cell.addEventListener('click',()=>onCellClick(r,c));
      cell.addEventListener('pointerdown',(e)=>onPointerDown(e,r,c));
      cell.addEventListener('pointerenter',()=>onPointerEnter(r,c));
      cell.addEventListener('pointerup',()=>onPointerUp(r,c));
      elBoard.appendChild(cell);
    }
  }
  elMoveCount.textContent=String(moveCount);
  elPieceCount.textContent=String(pieceCount());
  dbg('render',{moveCount, pieceCount:pieceCount(), selected, awaitingEliminationFrom, validMoveTargets:[...validMoveTargets], eliminationCandidates:[...eliminationCandidates]});
}

function clearHighlights(){ validMoveTargets.clear(); eliminationCandidates.clear(); }
function cancelSelection(){ selected=null; awaitingEliminationFrom=null; clearHighlights(); hoverCellKey=null; dragging=null; setMessage(''); render(); dbg('cancelSelection'); }

function computeValidMoveTargets(from){
  validMoveTargets.clear(); const piece=board[from.row][from.col]; if(!piece||piece===EMPTY)return;
  function wouldCreateElimination(toR,toC){ const prev=board[toR][toC]; const p=board[from.row][from.col]; board[from.row][from.col]=EMPTY; board[toR][toC]=p; const opts=afterMoveEliminationOptions({row:toR,col:toC}); board[toR][toC]=prev; board[from.row][from.col]=p; return opts.length>0; }
  for(let c=0;c<COLS;c++){ if(c===from.col)continue; if(isEmpty(from.row,c)&&canConnect(from.row,from.col,from.row,c)&&wouldCreateElimination(from.row,c)) validMoveTargets.add(`${from.row},${c}`); }
  for(let r=0;r<ROWS;r++){ if(r===from.row)continue; if(isEmpty(r,from.col)&&canConnect(from.row,from.col,r,from.col)&&wouldCreateElimination(r,from.col)) validMoveTargets.add(`${r},${from.col}`); }
  dbg('computeValidMoveTargets', from, [...validMoveTargets]);
}

function computeEliminationCandidates(from){
  eliminationCandidates.clear(); const piece=board[from.row][from.col]; if(!piece||piece===EMPTY)return;
  for(let c=0;c<COLS;c++){ if(c===from.col)continue; if(board[from.row][c]===piece&&canConnect(from.row,from.col,from.row,c)) eliminationCandidates.add(`${from.row},${c}`); }
  for(let r=0;r<ROWS;r++){ if(r===from.row)continue; if(board[r][from.col]===piece&&canConnect(from.row,from.col,r,from.col)) eliminationCandidates.add(`${r},${from.col}`); }
  dbg('computeEliminationCandidates', from, [...eliminationCandidates]);
}

function afterMoveEliminationOptions(at){
  eliminationCandidates.clear(); const piece=board[at.row][at.col]; if(!piece||piece===EMPTY) return []; const opts=[];
  for(let c=0;c<COLS;c++){ if(c===at.col)continue; if(board[at.row][c]===piece&&canConnect(at.row,at.col,at.row,c)){ eliminationCandidates.add(`${at.row},${c}`); opts.push({row:at.row,col:c}); } }
  for(let r=0;r<ROWS;r++){ if(r===at.row)continue; if(board[r][at.col]===piece&&canConnect(at.row,at.col,r,at.col)){ eliminationCandidates.add(`${r},${at.col}`); opts.push({row:r,col:at.col}); } }
  dbg('afterMoveEliminationOptions', at, opts);
  return opts;
}

function doEliminate(a,b){
  dbg('doEliminate called', a, b);
  if(!inBounds(a.row,a.col)||!inBounds(b.row,b.col)) return false;
  if(a.row===b.row && a.col===b.col) return false;
  const p1=board[a.row][a.col], p2=board[b.row][b.col];
  if(p1===EMPTY || p1!==p2) return false;
  if(!canConnect(a.row,a.col,b.row,b.col)) return false;
  dbg('eliminating', p1, a, b);
  board[a.row][a.col]=EMPTY; board[b.row][b.col]=EMPTY;
  moveCount+=1; setMessage(`消除：${p1} 在 (${a.row+1}, ${a.col+1}) 与 (${b.row+1}, ${b.col+1})`,'ok');
  selected=null; clearHighlights(); awaitingEliminationFrom=null; render(); return true;
}

function tryMove(from,to){
  dbg('tryMove', from, to);
  if(!isEmpty(to.row,to.col)) return false; if(!canConnect(from.row,from.col,to.row,to.col)) return false;
  const p=board[from.row][from.col]; const prev=cloneBoard(board); board[from.row][from.col]=EMPTY; board[to.row][to.col]=p;
  const opts=afterMoveEliminationOptions(to); if(opts.length===0){ board=prev; setMessage('该移动不会产生消除，无法移动。','error'); dbg('tryMove rollback: no elimination options'); return false; }
  setMessage('请选择要消除的另一个棋子。','info'); awaitingEliminationFrom={row:to.row,col:to.col}; selected={row:to.row,col:to.col}; validMoveTargets.clear(); render();
  if(opts.length===1){ doEliminate({row:to.row,col:to.col}, opts[0]); }
  return true;
}

function onCellClick(r,c){
  dbg('onCellClick', {r,c, piece:board[r][c], selected, awaitingEliminationFrom});
  if(awaitingEliminationFrom){ const key=`${r},${c}`; if(eliminationCandidates.has(key)){ dbg('awaitingEliminationFrom hit', key); doEliminate(awaitingEliminationFrom,{row:r,col:c}); return; } dbg('awaitingEliminationFrom miss', key, [...eliminationCandidates]); setMessage('请点击绿色高亮的棋子完成消除。','error'); return; }
  const piece=board[r][c];
  if(!selected){ if(piece===EMPTY) return; selected={row:r,col:c}; computeValidMoveTargets(selected); computeEliminationCandidates(selected); setMessage('选择一个蓝色空格移动，或点击绿色高亮的同款棋子直接消除。'); render(); dbg('selected', selected); return; }
  const from=selected; const selPiece=board[from.row][from.col];
  if(from.row===r && from.col===c){ selected=null; clearHighlights(); setMessage(''); render(); return; }
  const key=`${r},${c}`; if(eliminationCandidates.has(key) && piece!==EMPTY){ dbg('click on green candidate', key); doEliminate(from,{row:r,col:c}); return; }
  if(piece!==EMPTY && piece===selPiece && canConnect(from.row,from.col,r,c)){ dbg('direct eliminate by rule'); doEliminate(from,{row:r,col:c}); return; }
  if(piece!==EMPTY){ if(piece!==selPiece){ setMessage('这两个格子的内容不同，不能消除。','error'); } else if(!(from.row===r || from.col===c)){ setMessage('不在同一行或同一列，不能消除。','error'); } else { setMessage('两者之间有阻挡，不能消除。','error'); } }
  if(piece===EMPTY && validMoveTargets.has(key)){ dbg('click on blue move target', key); tryMove(from,{row:r,col:c}); return; }
  if(piece!==EMPTY){ selected={row:r,col:c}; computeValidMoveTargets(selected); computeEliminationCandidates(selected); setMessage('选择一个蓝色空格移动，或点击绿色高亮的同款棋子直接消除。'); render(); dbg('reselected', selected); return; }
  setMessage('该位置不是有效的移动目标。只能沿行/列移动到蓝色高亮的空格。','error');
}

function onPointerDown(e,r,c){
  if(awaitingEliminationFrom) return;
  const piece=board[r][c];
  if(piece===EMPTY) return;
  // If there is already a selection, start dragging from the selected cell
  // so releasing on a candidate can eliminate using the existing selection
  if(selected){
    dragging={from:{row:selected.row,col:selected.col}, current:{row:selected.row,col:selected.col}};
  } else {
    selected={row:r,col:c};
    computeValidMoveTargets(selected);
    computeEliminationCandidates(selected);
    dragging={from:{row:r,col:c}, current:{row:r,col:c}};
  }
  dbg('pointerdown',{r,c,piece, selected});
}
function onPointerEnter(r,c){ if(!dragging) return; hoverCellKey=`${r},${c}`; render(); dbg('pointerenter',{r,c}); }
function onPointerUp(r,c){
  if(!dragging) return;
  const dragFrom=dragging.from;
  dragging=null;
  let dropRow=r, dropCol=c;
  if(hoverCellKey){ const [hr,hc]=hoverCellKey.split(',').map(Number); dropRow=hr; dropCol=hc; }
  const key=`${dropRow},${dropCol}`;
  hoverCellKey=null;
  const piece=board[dropRow][dropCol];
  // Prefer using selected as the source if available (supports select-then-tap)
  const source = selected ? { row: selected.row, col: selected.col } : dragFrom;
  const sourcePiece = board[source.row][source.col];
  // If dropping on a green candidate, eliminate using the selected/source
  if(eliminationCandidates.has(key) && piece !== EMPTY){
    dbg('pointerup eliminate via candidate',{from:source,to:{row:dropRow,col:dropCol}});
    doEliminate(source,{row:dropRow,col:dropCol});
    return;
  }
  // Otherwise, if same-piece straight path, eliminate
  if(piece!==EMPTY && piece===sourcePiece && canConnect(source.row,source.col,dropRow,dropCol)){
    dbg('pointerup eliminate',{from:source,to:{row:dropRow,col:dropCol}});
    doEliminate(source,{row:dropRow,col:dropCol});
    return;
  }
  // Otherwise try move if empty valid target (based on selected/source)
  if(isEmpty(dropRow,dropCol) && validMoveTargets.has(key)){
    dbg('pointerup move',{from:source,to:{row:dropRow,col:dropCol}});
    tryMove(source,{row:dropRow,col:dropCol});
    return;
  }
  render();
  dbg('pointerup noop',{from:source,dropRow,dropCol});
}

function showAnyPairs(){ clearHighlights(); for(let r1=0;r1<ROWS;r1++){ for(let c1=0;c1<COLS;c1++){ const p=board[r1][c1]; if(p===EMPTY) continue; for(let c2=c1+1;c2<COLS;c2++){ if(board[r1][c2]===p && canConnect(r1,c1,r1,c2)){ eliminationCandidates.add(`${r1},${c1}`); eliminationCandidates.add(`${r1},${c2}`); render(); setMessage('存在可消除对（绿色高亮）。选择其中任意两个即可消除。'); dbg('showAnyPairs row pair',{r1,c1,c2,p}); return; } } for(let r2=r1+1;r2<ROWS;r2++){ if(board[r2][c1]===p && canConnect(r1,c1,r2,c1)){ eliminationCandidates.add(`${r1},${c1}`); eliminationCandidates.add(`${r2},${c1}`); render(); setMessage('存在可消除对（绿色高亮）。选择其中任意两个即可消除。'); dbg('showAnyPairs col pair',{r1,r2,c1,p}); return; } } } } setMessage('当前没有可直接消除的配对。'); dbg('showAnyPairs none'); }

elReset.addEventListener('click', resetGame);
elShowPairs.addEventListener('click', showAnyPairs);
elCancel.addEventListener('click', cancelSelection);

// ESC 取消、右键取消
window.addEventListener('keydown', (e)=>{ if(e.key==='Escape'){ cancelSelection(); }});
elBoard.addEventListener('contextmenu', (e)=>{ e.preventDefault(); cancelSelection(); });

resetGame();