import { describe, expect, it } from 'vitest';

import type { Pattern } from './pattern';
import {
  flipPatternHorizontal,
  flipPatternVertical,
  rotatePatternClockwise,
} from './transformations';

describe('pattern transformations', () => {
  const pattern: Pattern = {
    id: 'sample',
    category: 'uncategorized',
    tags: [],
    width: 3,
    height: 2,
    cells: [
      [1, 0, null],
      [0, 1, 1],
    ],
  };

  it('rotates a pattern 90 degrees clockwise', () => {
    const result = rotatePatternClockwise(pattern);

    expect(result.width).toBe(2);
    expect(result.height).toBe(3);
    expect(result.cells).toEqual([
      [0, 1],
      [1, 0],
      [1, null],
    ]);
  });

  it('flips a pattern horizontally', () => {
    const result = flipPatternHorizontal(pattern);

    expect(result.width).toBe(3);
    expect(result.height).toBe(2);
    expect(result.cells).toEqual([
      [null, 0, 1],
      [1, 1, 0],
    ]);
  });

  it('flips a pattern vertically', () => {
    const result = flipPatternVertical(pattern);

    expect(result.width).toBe(3);
    expect(result.height).toBe(2);
    expect(result.cells).toEqual([
      [0, 1, 1],
      [1, 0, null],
    ]);
  });

  it('does not mutate the source pattern', () => {
    rotatePatternClockwise(pattern);
    flipPatternHorizontal(pattern);
    flipPatternVertical(pattern);

    expect(pattern.cells).toEqual([
      [1, 0, null],
      [0, 1, 1],
    ]);
  });
});
