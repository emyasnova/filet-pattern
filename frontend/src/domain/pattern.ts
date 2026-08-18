import type { PatternCell } from './cell';

export interface PatternCategory {
  slug: string;
  name: string;
}

export interface PatternTag {
  id: string;
  name: string;
}

export interface Pattern {
  id: string;
  name: string;
  category: string;
  tags: string[];
  width: number;
  height: number;
  cells: PatternCell[][];
  createdAt: string;
}
