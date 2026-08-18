import type { CellPosition } from '../../../domain/selection';

export const CANVAS_CELL_SIZE = 18;

export interface CanvasViewport {
  scrollLeft: number;
  scrollTop: number;
  width: number;
  height: number;
}

export function getCanvasCellAtPoint(
  x: number,
  y: number,
  viewport: CanvasViewport,
  canvasWidth: number,
  canvasHeight: number,
): CellPosition | null {
  const col = Math.floor((x + viewport.scrollLeft) / CANVAS_CELL_SIZE);
  const row = Math.floor((y + viewport.scrollTop) / CANVAS_CELL_SIZE);
  if (row < 0 || row >= canvasHeight || col < 0 || col >= canvasWidth) return null;
  return { row, col };
}

export function getVisibleCellBounds(
  viewport: CanvasViewport,
  canvasWidth: number,
  canvasHeight: number,
) {
  return {
    left: Math.max(0, Math.floor(viewport.scrollLeft / CANVAS_CELL_SIZE)),
    top: Math.max(0, Math.floor(viewport.scrollTop / CANVAS_CELL_SIZE)),
    right: Math.min(
      canvasWidth - 1,
      Math.ceil((viewport.scrollLeft + viewport.width) / CANVAS_CELL_SIZE),
    ),
    bottom: Math.min(
      canvasHeight - 1,
      Math.ceil((viewport.scrollTop + viewport.height) / CANVAS_CELL_SIZE),
    ),
  };
}
