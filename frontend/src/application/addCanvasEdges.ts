import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';

export function addCanvasRowsTop(canvas: CanvasState, count = 1): CanvasState {
  const normalizedCount = normalizeCount(count);

  if (normalizedCount === 0) {
    return canvas;
  }

  const emptyRows = Array.from({ length: normalizedCount }, () =>
    createEmptyRow(canvas.width),
  );

  return {
    width: canvas.width,
    height: canvas.height + normalizedCount,
    cells: [...emptyRows, ...canvas.cells.map((row) => [...row])],
  };
}

export function addCanvasColumnsLeft(canvas: CanvasState, count = 1): CanvasState {
  const normalizedCount = normalizeCount(count);

  if (normalizedCount === 0) {
    return canvas;
  }

  return {
    width: canvas.width + normalizedCount,
    height: canvas.height,
    cells: canvas.cells.map((row) => [
      ...createEmptyRow(normalizedCount),
      ...row,
    ]),
  };
}

function normalizeCount(count: number): number {
  if (!Number.isFinite(count) || count <= 0) {
    return 0;
  }

  return Math.floor(count);
}

function createEmptyRow(width: number): CanvasCell[] {
  return Array.from({ length: width }, (): CanvasCell => 0);
}
