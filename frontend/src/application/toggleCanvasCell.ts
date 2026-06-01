import type { CanvasState } from '../domain/canvas';

export function toggleCanvasCell(
  canvas: CanvasState,
  row: number,
  col: number,
): CanvasState {
  if (row < 0 || row >= canvas.height || col < 0 || col >= canvas.width) {
    return canvas;
  }

  const cells = [...canvas.cells];
  cells[row] = [...canvas.cells[row]];
  cells[row][col] = cells[row][col] === 1 ? 0 : 1;

  return {
    ...canvas,
    cells,
  };
}
