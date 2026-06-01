import type { CanvasState } from '../domain/canvas';
import type { Pattern } from '../domain/pattern';
import { cloneMatrix } from '../domain/matrix';

export function applyPatternToCanvas(
  canvas: CanvasState,
  pattern: Pattern,
  startRow: number,
  startCol: number,
): CanvasState {
  const cells = cloneMatrix(canvas.cells);

  for (let patternRow = 0; patternRow < pattern.height; patternRow += 1) {
    const canvasRow = startRow + patternRow;

    if (canvasRow < 0 || canvasRow >= canvas.height) {
      continue;
    }

    for (let patternCol = 0; patternCol < pattern.width; patternCol += 1) {
      const canvasCol = startCol + patternCol;

      if (canvasCol < 0 || canvasCol >= canvas.width) {
        continue;
      }

      const patternCell = pattern.cells[patternRow][patternCol];

      if (patternCell !== null) {
        cells[canvasRow][canvasCol] = patternCell;
      }
    }
  }

  return {
    ...canvas,
    cells,
  };
}
