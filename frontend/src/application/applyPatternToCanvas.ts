import type { CanvasState } from '../domain/canvas';
import type { Pattern } from '../domain/pattern';

export function applyPatternToCanvas(
  canvas: CanvasState,
  pattern: Pattern,
  startRow: number,
  startCol: number,
): CanvasState {
  const cells = [...canvas.cells];
  const changedRows = new Set<number>();

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

      if (patternCell !== null && cells[canvasRow][canvasCol] !== patternCell) {
        if (!changedRows.has(canvasRow)) {
          cells[canvasRow] = [...cells[canvasRow]];
          changedRows.add(canvasRow);
        }
        cells[canvasRow][canvasCol] = patternCell;
      }
    }
  }

  return changedRows.size === 0 ? canvas : {
    ...canvas,
    cells,
  };
}
