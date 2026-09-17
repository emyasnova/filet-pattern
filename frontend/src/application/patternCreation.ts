import type { PatternCell } from '../domain/cell';
import { normalizePatternTransparency } from './normalizePatternTransparency';

export function getPatternNameFromFile(fileName: string): string {
  return fileName.replace(/\.[^.]+$/, '');
}

/** Invert the visible black/white pattern, including its transparent background. */
export function invertPatternCells(cells: PatternCell[][]): PatternCell[][] {
  return normalizePatternTransparency(
    cells.map((row) => row.map((cell): PatternCell => cell === 1 ? 0 : 1)),
  );
}
