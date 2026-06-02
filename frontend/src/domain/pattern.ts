import type { PatternCell } from './cell';

export type PatternCategory =
  | 'alphabet'
  | 'frame'
  | 'object'
  | 'ornament'
  | 'uncategorized';

export interface Pattern {
  id: string;
  char?: string;
  category: PatternCategory;
  name?: string;
  tags: string[];
  width: number;
  height: number;
  cells: PatternCell[][];
}
