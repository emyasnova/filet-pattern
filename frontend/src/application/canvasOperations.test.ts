import { describe, expect, it } from 'vitest';

import { applyPatternToCanvas } from './applyPatternToCanvas';
import {
  clearCanvasBlock,
  copyCanvasBlock,
  cutCanvasBlock,
  flipCanvasBlockHorizontal,
  flipCanvasBlockVertical,
  fillCanvasBlock,
  pasteCanvasBlock,
  rotateCanvasBlockClockwise,
} from './canvasBlockOperations';
import { createEmptyCanvas } from './createEmptyCanvas';
import { resizeCanvas } from './resizeCanvas';
import { toggleCanvasCell } from './toggleCanvasCell';
import type { CanvasState } from '../domain/canvas';
import type { Pattern } from '../domain/pattern';

describe('canvas operations', () => {
  it('creates an empty canvas with default size', () => {
    const canvas = createEmptyCanvas();

    expect(canvas.width).toBe(100);
    expect(canvas.height).toBe(100);
    expect(canvas.cells).toHaveLength(100);
    expect(canvas.cells[0]).toHaveLength(100);
    expect(canvas.cells[0][0]).toBe(0);
  });

  it('toggles a canvas cell without mutating the source canvas', () => {
    const canvas = createEmptyCanvas(2, 2);
    const filled = toggleCanvasCell(canvas, 0, 1);
    const cleared = toggleCanvasCell(filled, 0, 1);

    expect(canvas.cells).toEqual([
      [0, 0],
      [0, 0],
    ]);
    expect(filled.cells).toEqual([
      [0, 1],
      [0, 0],
    ]);
    expect(cleared.cells).toEqual([
      [0, 0],
      [0, 0],
    ]);
  });

  it('resizes a canvas preserving existing cells and filling new cells with 0', () => {
    const canvas: CanvasState = {
      width: 2,
      height: 2,
      cells: [
        [1, 0],
        [0, 1],
      ],
    };

    const larger = resizeCanvas(canvas, 3, 3);
    const smaller = resizeCanvas(canvas, 1, 2);

    expect(larger.cells).toEqual([
      [1, 0, 0],
      [0, 1, 0],
      [0, 0, 0],
    ]);
    expect(smaller.cells).toEqual([[1], [0]]);
    expect(canvas.cells).toEqual([
      [1, 0],
      [0, 1],
    ]);
  });

  it('applies a pattern and leaves canvas cells unchanged for null pattern cells', () => {
    const canvas: CanvasState = {
      width: 3,
      height: 3,
      cells: [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
      ],
    };
    const pattern: Pattern = {
      id: 'sample',
      width: 2,
      height: 2,
      cells: [
        [0, null],
        [1, 0],
      ],
    };

    const result = applyPatternToCanvas(canvas, pattern, 1, 1);

    expect(result.cells).toEqual([
      [1, 1, 1],
      [1, 0, 1],
      [1, 1, 0],
    ]);
    expect(canvas.cells).toEqual([
      [1, 1, 1],
      [1, 1, 1],
      [1, 1, 1],
    ]);
  });

  it('clips a pattern at canvas boundaries', () => {
    const pattern: Pattern = {
      id: 'sample',
      width: 2,
      height: 2,
      cells: [
        [1, 1],
        [1, 1],
      ],
    };

    const result = applyPatternToCanvas(createEmptyCanvas(2, 2), pattern, 1, 1);

    expect(result.cells).toEqual([
      [0, 0],
      [0, 1],
    ]);
  });

  it('copies, clears, fills, cuts, and pastes canvas blocks without mutating source', () => {
    const canvas: CanvasState = {
      width: 4,
      height: 3,
      cells: [
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 1, 0, 0],
      ],
    };
    const selection = {
      startRow: 0,
      startCol: 1,
      endRow: 1,
      endCol: 2,
    };

    const block = copyCanvasBlock(canvas, selection);
    const cleared = clearCanvasBlock(canvas, selection);
    const filled = fillCanvasBlock(canvas, selection);
    const cut = cutCanvasBlock(canvas, selection);
    const pasted = block
      ? pasteCanvasBlock(createEmptyCanvas(3, 3), block, 1, 1)
      : null;

    expect(block?.cells).toEqual([
      [0, 1],
      [1, 0],
    ]);
    expect(cleared.cells).toEqual([
      [1, 0, 0, 0],
      [0, 0, 0, 1],
      [1, 1, 0, 0],
    ]);
    expect(filled.cells).toEqual([
      [1, 1, 1, 0],
      [0, 1, 1, 1],
      [1, 1, 0, 0],
    ]);
    expect(cut.block?.cells).toEqual(block?.cells);
    expect(cut.canvas.cells).toEqual(cleared.cells);
    expect(pasted?.cells).toEqual([
      [0, 0, 0],
      [0, 0, 1],
      [0, 1, 0],
    ]);
    expect(canvas.cells).toEqual([
      [1, 0, 1, 0],
      [0, 1, 0, 1],
      [1, 1, 0, 0],
    ]);
  });

  it('rotates and flips selected canvas blocks', () => {
    const canvas: CanvasState = {
      width: 4,
      height: 4,
      cells: [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 0],
      ],
    };
    const selection = {
      startRow: 0,
      startCol: 0,
      endRow: 1,
      endCol: 2,
    };

    const rotated = rotateCanvasBlockClockwise(canvas, selection);
    const flippedHorizontal = flipCanvasBlockHorizontal(canvas, selection);
    const flippedVertical = flipCanvasBlockVertical(canvas, selection);

    expect(rotated.canvas.cells).toEqual([
      [0, 1, 0, 0],
      [1, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
    ]);
    expect(rotated.selection).toEqual({
      startRow: 0,
      startCol: 0,
      endRow: 2,
      endCol: 1,
    });
    expect(flippedHorizontal.canvas.cells).toEqual([
      [0, 0, 1, 0],
      [0, 1, 0, 0],
      [1, 1, 0, 0],
      [0, 0, 0, 0],
    ]);
    expect(flippedVertical.canvas.cells).toEqual([
      [0, 1, 0, 0],
      [1, 0, 0, 0],
      [1, 1, 0, 0],
      [0, 0, 0, 0],
    ]);
  });
});
