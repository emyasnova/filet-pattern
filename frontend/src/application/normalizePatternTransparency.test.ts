import { describe, expect, it } from 'vitest';

import { normalizePatternTransparency } from './normalizePatternTransparency';

describe('normalizePatternTransparency', () => {
  it('makes the outside background transparent and keeps enclosed holes white', () => {
    expect(
      normalizePatternTransparency([
        [0, 1, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
      ]),
    ).toEqual([
      [null, 1, null, null, null],
      [1, 1, 1, 1, null],
      [null, 1, 0, 1, null],
      [null, 1, 1, 1, null],
      [null, null, null, null, null],
    ]);
  });
});
