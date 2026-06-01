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
      name: undefined,
      width: 2,
      height: 2,
      cells: [
        [0, 1],
        [null, 0],
      ],
    });
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
