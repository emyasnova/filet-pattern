import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';
import { createMatrix } from '../domain/matrix';

export function resizeCanvas(
  canvas: CanvasState,
  width: number,
  height: number,
): CanvasState {
  const nextCells = createMatrix<CanvasCell>(width, height, () => 0);
  const copiedHeight = Math.min(canvas.height, height);
  const copiedWidth = Math.min(canvas.width, width);

  for (let row = 0; row < copiedHeight; row += 1) {
    for (let col = 0; col < copiedWidth; col += 1) {
      nextCells[row][col] = canvas.cells[row][col];
    }
  }

  return {
    width,
    height,
    cells: nextCells,
  };
}
