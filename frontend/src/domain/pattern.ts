import type { PatternCell } from './cell';

export interface Pattern {
  id: string;
  char?: string;
  name?: string;
  width: number;
  height: number;
  cells: PatternCell[][];
}
