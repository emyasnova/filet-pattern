import { describe, expect, it } from 'vitest';

import type { PatternCell } from '../domain/cell';
import { normalizePatternTransparency } from './normalizePatternTransparency';
import { getPatternNameFromFile, invertPatternCells } from './patternCreation';

describe('getPatternNameFromFile', () => {
  it('removes only the final image extension', () => {
    expect(getPatternNameFromFile('rose.png')).toBe('rose');
    expect(getPatternNameFromFile('rose.v2.jpeg')).toBe('rose.v2');
  });
});

describe('invertPatternCells', () => {
  it('inverts both white and transparent cells and preserves enclosed white cells', () => {
    const cells: PatternCell[][] = [
      [null, 0, null],
      [0, 1, 0],
      [null, 0, null],
    ];
    expect(invertPatternCells(cells)).toEqual([
      [1, 1, 1],
      [1, 0, 1],
      [1, 1, 1],
    ]);
  });

  it('makes the new outside background transparent without changing the source', () => {
    const cells: PatternCell[][] = [[1, 1, 1], [1, 0, 1], [1, 1, 1]];
    const original = cells.map((row) => [...row]);
    expect(invertPatternCells(cells)).toEqual([
      [null, null, null], [null, 1, null], [null, null, null],
    ]);
    expect(cells).toEqual(original);
  });

  it('restores the normalized pattern after two inversions', () => {
    const cells: PatternCell[][] = [[null, 0, 1, 0], [1, 1, 0, 1]];
    expect(invertPatternCells(invertPatternCells(cells)))
      .toEqual(normalizePatternTransparency(cells));
  });

  it('supports empty patterns', () => {
    expect(invertPatternCells([])).toEqual([]);
  });
});
