import { describe, expect, it } from 'vitest';

import { validatePattern } from './validatePattern';

describe('validatePattern', () => {
  it('accepts a valid pattern', () => {
    const result = validatePattern(
      {
        char: 'B',
        width: 2,
        height: 2,
        cells: [
          [0, 1],
          [null, 0],
        ],
      },
      'B.json',
    );

    expect(result.errors).toEqual([]);
    expect(result.pattern).toEqual({
      id: 'B.json',
      char: 'B',
      category: 'uncategorized',
      name: undefined,
      tags: [],
      width: 2,
      height: 2,
      cells: [
        [null, 1],
        [null, null],
      ],
    });
  });

  it('accepts optional category and tags metadata', () => {
    const result = validatePattern(
      {
        char: 'F',
        category: 'ornament',
        tags: ['flower', 'цветок', 'flower', ' '],
        width: 1,
        height: 1,
        cells: [[1]],
      },
      'flower.json',
    );

    expect(result.errors).toEqual([]);
    expect(result.pattern?.category).toBe('ornament');
    expect(result.pattern?.tags).toEqual(['flower', 'цветок']);
  });

  it('rejects invalid category and tags metadata', () => {
    const result = validatePattern(
      {
        category: 'unknown',
        tags: ['flower', 1],
        width: 1,
        height: 1,
        cells: [[1]],
      },
      'bad-meta.json',
    );

    expect(result.pattern).toBeUndefined();
    expect(result.errors).toContain(
      'category must be one of alphabet, frame, object, or ornament.',
    );
    expect(result.errors).toContain('tags[1] must be a string.');
  });

  it('normalizes external empty cells to null and preserves inner zeros', () => {
    const result = validatePattern(
      {
        width: 5,
        height: 5,
        cells: [
          [0, 0, 0, 0, 0],
          [0, 1, 1, 1, 0],
          [0, 1, 0, 1, 0],
          [0, 1, 1, 1, 0],
          [0, 0, 0, 0, 0],
        ],
      },
      'sample.json',
    );

    expect(result.errors).toEqual([]);
    expect(result.pattern?.cells).toEqual([
      [null, null, null, null, null],
      [null, 1, 1, 1, null],
      [null, 1, 0, 1, null],
      [null, 1, 1, 1, null],
      [null, null, null, null, null],
    ]);
  });

  it('rejects invalid dimensions and cell values', () => {
    const result = validatePattern(
      {
        width: 2,
        height: 2,
        cells: [[0, 2]],
      },
      'bad.json',
    );

    expect(result.pattern).toBeUndefined();
    expect(result.errors).toContain('cells row count must equal height 2.');
    expect(result.errors).toContain('cells[0][1] must be 0, 1, or null.');
  });
});
