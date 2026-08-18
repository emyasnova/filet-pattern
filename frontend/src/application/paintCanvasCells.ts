import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';

export interface CanvasCellUpdate {
  row: number;
  col: number;
  value: CanvasCell;
}

export function paintCanvasCells(
  canvas: CanvasState,
  updates: readonly CanvasCellUpdate[],
): CanvasState {
  let cells: CanvasCell[][] | null = null;
  const changedRows = new Map<number, CanvasCell[]>();

  for (const update of updates) {
    if (
      update.row < 0 ||
      update.row >= canvas.height ||
      update.col < 0 ||
      update.col >= canvas.width
    ) {
      continue;
    }

    const sourceRow = changedRows.get(update.row) ?? canvas.cells[update.row];
    if (sourceRow[update.col] === update.value) continue;

    const nextRow = changedRows.has(update.row) ? sourceRow : [...sourceRow];
    nextRow[update.col] = update.value;
    changedRows.set(update.row, nextRow);
  }

  if (changedRows.size === 0) return canvas;
  cells = [...canvas.cells];
  changedRows.forEach((row, index) => {
    cells![index] = row;
  });
  return { ...canvas, cells };
}
