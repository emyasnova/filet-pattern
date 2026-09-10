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
  cellSize = CANVAS_CELL_SIZE,
): CellPosition | null {
  const col = Math.floor((x + viewport.scrollLeft) / cellSize);
  const row = Math.floor((y + viewport.scrollTop) / cellSize);
  if (row < 0 || row >= canvasHeight || col < 0 || col >= canvasWidth) return null;
  return { row, col };
}

export function getVisibleCellBounds(
  viewport: CanvasViewport,
  canvasWidth: number,
  canvasHeight: number,
  cellSize = CANVAS_CELL_SIZE,
) {
  return {
    left: Math.max(0, Math.floor(viewport.scrollLeft / cellSize)),
    top: Math.max(0, Math.floor(viewport.scrollTop / cellSize)),
    right: Math.min(
      canvasWidth - 1,
      Math.ceil((viewport.scrollLeft + viewport.width) / cellSize),
    ),
    bottom: Math.min(
      canvasHeight - 1,
      Math.ceil((viewport.scrollTop + viewport.height) / cellSize),
    ),
  };
}

/** Keep a viewport point over the same logical position when cell size changes. */
export function getZoomScrollOffset(
  viewport: CanvasViewport,
  anchor: { x: number; y: number },
  previousCellSize: number,
  nextCellSize: number,
  canvasWidth: number,
  canvasHeight: number,
) {
  const ratio = nextCellSize / previousCellSize;
  return {
    scrollLeft: Math.max(0, Math.min(
      (viewport.scrollLeft + anchor.x) * ratio - anchor.x,
      canvasWidth * nextCellSize - viewport.width,
    )),
    scrollTop: Math.max(0, Math.min(
      (viewport.scrollTop + anchor.y) * ratio - anchor.y,
      canvasHeight * nextCellSize - viewport.height,
    )),
  };
}
