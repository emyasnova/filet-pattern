import type { CanvasCell } from './cell';

export interface CanvasState {
  width: number;
  height: number;
  cells: CanvasCell[][];
}
