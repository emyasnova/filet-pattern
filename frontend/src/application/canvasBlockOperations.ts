import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';
import type { CanvasBlock, SelectionRect } from '../domain/selection';
import {
  cloneMatrix,
  flipMatrixHorizontal,
  flipMatrixVertical,
  rotateMatrixClockwise,
} from '../domain/matrix';
import { normalizeSelectionRect } from '../domain/selection';

interface CanvasBlockTransformResult {
  canvas: CanvasState;
  selection: SelectionRect | null;
}

export function copyCanvasBlock(
  canvas: CanvasState,
  selection: SelectionRect,
): CanvasBlock | null {
  const clipped = clipSelection(canvas, selection);

  if (!clipped) {
    return null;
  }

  const cells = canvas.cells
    .slice(clipped.top, clipped.bottom + 1)
    .map((row) => row.slice(clipped.left, clipped.right + 1));

  return {
    width: clipped.right - clipped.left + 1,
    height: clipped.bottom - clipped.top + 1,
    cells,
  };
}

export function clearCanvasBlock(
  canvas: CanvasState,
  selection: SelectionRect,
): CanvasState {
  return fillCanvasBlock(canvas, selection, 0);
}

export function fillCanvasBlock(
  canvas: CanvasState,
  selection: SelectionRect,
  value: CanvasCell = 1,
): CanvasState {
  const clipped = clipSelection(canvas, selection);

  if (!clipped) {
    return canvas;
  }

  const cells = cloneMatrix(canvas.cells);

  for (let row = clipped.top; row <= clipped.bottom; row += 1) {
    for (let col = clipped.left; col <= clipped.right; col += 1) {
      cells[row][col] = value;
    }
  }

  return {
    ...canvas,
    cells,
  };
}

export function cutCanvasBlock(
  canvas: CanvasState,
  selection: SelectionRect,
): { canvas: CanvasState; block: CanvasBlock | null } {
  const block = copyCanvasBlock(canvas, selection);

  if (!block) {
    return { canvas, block: null };
  }

  return {
    canvas: clearCanvasBlock(canvas, selection),
    block,
  };
}

export function pasteCanvasBlock(
  canvas: CanvasState,
  block: CanvasBlock,
  row: number,
  col: number,
): CanvasState {
  const cells = cloneMatrix(canvas.cells);
  let hasChanges = false;

  for (let blockRow = 0; blockRow < block.height; blockRow += 1) {
    const canvasRow = row + blockRow;

    if (canvasRow < 0 || canvasRow >= canvas.height) {
      continue;
    }

    for (let blockCol = 0; blockCol < block.width; blockCol += 1) {
      const canvasCol = col + blockCol;

      if (canvasCol < 0 || canvasCol >= canvas.width) {
        continue;
      }

      cells[canvasRow][canvasCol] = block.cells[blockRow][blockCol];
      hasChanges = true;
    }
  }

  if (!hasChanges) {
    return canvas;
  }

  return {
    ...canvas,
    cells,
  };
}

export function rotateCanvasBlockClockwise(
  canvas: CanvasState,
  selection: SelectionRect,
): CanvasBlockTransformResult {
  return transformCanvasBlock(canvas, selection, (block) => ({
    width: block.height,
    height: block.width,
    cells: rotateMatrixClockwise(block.cells),
  }));
}

export function flipCanvasBlockHorizontal(
  canvas: CanvasState,
  selection: SelectionRect,
): CanvasBlockTransformResult {
  return transformCanvasBlock(canvas, selection, (block) => ({
    ...block,
    cells: flipMatrixHorizontal(block.cells),
  }));
}

export function flipCanvasBlockVertical(
  canvas: CanvasState,
  selection: SelectionRect,
): CanvasBlockTransformResult {
  return transformCanvasBlock(canvas, selection, (block) => ({
    ...block,
    cells: flipMatrixVertical(block.cells),
  }));
}

function transformCanvasBlock(
  canvas: CanvasState,
  selection: SelectionRect,
  transform: (block: CanvasBlock) => CanvasBlock,
): CanvasBlockTransformResult {
  const block = copyCanvasBlock(canvas, selection);

  if (!block) {
    return { canvas, selection: null };
  }

  const origin = clipSelection(canvas, selection);

  if (!origin) {
    return { canvas, selection: null };
  }

  const transformedBlock = transform(block);
  const clearedCanvas = clearCanvasBlock(canvas, selection);
  const nextCanvas = pasteCanvasBlock(
    clearedCanvas,
    transformedBlock,
    origin.top,
    origin.left,
  );
  const nextSelection = createPastedSelection(
    nextCanvas,
    transformedBlock,
    origin.top,
    origin.left,
  );

  return {
    canvas: nextCanvas,
    selection: nextSelection,
  };
}

function createPastedSelection(
  canvas: CanvasState,
  block: CanvasBlock,
  row: number,
  col: number,
): SelectionRect | null {
  const top = Math.max(0, row);
  const left = Math.max(0, col);
  const bottom = Math.min(canvas.height - 1, row + block.height - 1);
  const right = Math.min(canvas.width - 1, col + block.width - 1);

  if (top > bottom || left > right) {
    return null;
  }

  return {
    startRow: top,
    startCol: left,
    endRow: bottom,
    endCol: right,
  };
}

function clipSelection(
  canvas: CanvasState,
  selection: SelectionRect,
): ReturnType<typeof normalizeSelectionRect> | null {
  const normalized = normalizeSelectionRect(selection);
  const top = Math.max(0, normalized.top);
  const left = Math.max(0, normalized.left);
  const bottom = Math.min(canvas.height - 1, normalized.bottom);
  const right = Math.min(canvas.width - 1, normalized.right);

  if (top > bottom || left > right) {
    return null;
  }

  return {
    top,
    left,
    bottom,
    right,
  };
}
