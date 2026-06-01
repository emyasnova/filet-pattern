import type { CanvasCell } from './cell';

export interface CellPosition {
  row: number;
  col: number;
}

export interface SelectionRect {
  startRow: number;
  startCol: number;
  endRow: number;
  endCol: number;
}

export interface NormalizedSelectionRect {
  top: number;
  left: number;
  bottom: number;
  right: number;
}

export interface CanvasBlock {
  width: number;
  height: number;
  cells: CanvasCell[][];
}

export function createSelectionRect(
  start: CellPosition,
  end: CellPosition,
): SelectionRect {
  return {
    startRow: start.row,
    startCol: start.col,
    endRow: end.row,
    endCol: end.col,
  };
}

export function normalizeSelectionRect(
  selection: SelectionRect,
): NormalizedSelectionRect {
  return {
    top: Math.min(selection.startRow, selection.endRow),
    left: Math.min(selection.startCol, selection.endCol),
    bottom: Math.max(selection.startRow, selection.endRow),
    right: Math.max(selection.startCol, selection.endCol),
  };
}
