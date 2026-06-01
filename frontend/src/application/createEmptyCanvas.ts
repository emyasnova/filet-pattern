import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';
import { createMatrix } from '../domain/matrix';

export const DEFAULT_CANVAS_WIDTH = 100;
export const DEFAULT_CANVAS_HEIGHT = 100;

export function createEmptyCanvas(
  width = DEFAULT_CANVAS_WIDTH,
  height = DEFAULT_CANVAS_HEIGHT,
): CanvasState {
  return {
    width,
    height,
    cells: createMatrix<CanvasCell>(width, height, () => 0),
  };
}
