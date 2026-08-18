import { describe, expect, it } from 'vitest';

import { getPatternNameFromFile } from './patternCreation';

describe('getPatternNameFromFile', () => {
  it('removes only the final image extension', () => {
    expect(getPatternNameFromFile('rose.png')).toBe('rose');
    expect(getPatternNameFromFile('rose.v2.jpeg')).toBe('rose.v2');
  });
});
