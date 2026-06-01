import { useCallback, useState } from 'react';

import type { CanvasState } from '../../domain/canvas';
import type { Pattern } from '../../domain/pattern';
import type { CanvasBlock, SelectionRect } from '../../domain/selection';
import { applyPatternToCanvas } from '../../application/applyPatternToCanvas';
import {
  clearCanvasBlock,
  fillCanvasBlock,
  pasteCanvasBlock,
} from '../../application/canvasBlockOperations';
import { clearCanvas } from '../../application/clearCanvas';
import { createEmptyCanvas } from '../../application/createEmptyCanvas';
import { resizeCanvas } from '../../application/resizeCanvas';
import { toggleCanvasCell } from '../../application/toggleCanvasCell';

interface UseCanvasState {
  applyPattern: (pattern: Pattern, row: number, col: number) => void;
  canvas: CanvasState;
  clear: () => void;
  clearBlock: (selection: SelectionRect) => void;
  fillBlock: (selection: SelectionRect) => void;
  pasteBlock: (block: CanvasBlock, row: number, col: number) => void;
  replaceCanvas: (canvas: CanvasState) => void;
  resize: (width: number, height: number) => void;
  toggleCell: (row: number, col: number) => void;
}

export function useCanvasState(): UseCanvasState {
  const [canvas, setCanvas] = useState(() => createEmptyCanvas());

  const applyPattern = useCallback((pattern: Pattern, row: number, col: number) => {
    setCanvas((current) => applyPatternToCanvas(current, pattern, row, col));
  }, []);

  const clear = useCallback(() => {
    setCanvas((current) => clearCanvas(current));
  }, []);

  const clearBlock = useCallback((selection: SelectionRect) => {
    setCanvas((current) => clearCanvasBlock(current, selection));
  }, []);

  const fillBlock = useCallback((selection: SelectionRect) => {
    setCanvas((current) => fillCanvasBlock(current, selection));
  }, []);

  const pasteBlock = useCallback((block: CanvasBlock, row: number, col: number) => {
    setCanvas((current) => pasteCanvasBlock(current, block, row, col));
  }, []);

  const toggleCell = useCallback((row: number, col: number) => {
    setCanvas((current) => toggleCanvasCell(current, row, col));
  }, []);

  const resize = useCallback((width: number, height: number) => {
    setCanvas((current) => resizeCanvas(current, width, height));
  }, []);

  const replaceCanvas = useCallback((nextCanvas: CanvasState) => {
    setCanvas(nextCanvas);
  }, []);

  return {
    applyPattern,
    canvas,
    clear,
    clearBlock,
    fillBlock,
    pasteBlock,
    replaceCanvas,
    resize,
    toggleCell,
  };
}
