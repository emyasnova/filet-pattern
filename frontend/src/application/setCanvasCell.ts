import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';

export function setCanvasCell(
  canvas: CanvasState,
  row: number,
  col: number,
  value: CanvasCell,
): CanvasState {
  if (row < 0 || row >= canvas.height || col < 0 || col >= canvas.width) {
    return canvas;
  }

  if (canvas.cells[row][col] === value) {
    return canvas;
  }

  const cells = [...canvas.cells];
  cells[row] = [...canvas.cells[row]];
  cells[row][col] = value;

  return {
    ...canvas,
    cells,
  };
}
