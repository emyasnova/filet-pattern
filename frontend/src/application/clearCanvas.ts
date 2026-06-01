import type { CanvasState } from '../domain/canvas';
import { createEmptyCanvas } from './createEmptyCanvas';

export function clearCanvas(canvas: CanvasState): CanvasState {
  return createEmptyCanvas(canvas.width, canvas.height);
}
