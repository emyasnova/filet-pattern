import { describe, expect, it } from 'vitest';

import { getCanvasCellAtPoint, getVisibleCellBounds } from './canvasGeometry';

describe('canvas geometry', () => {
  it('maps viewport coordinates to cells with scroll offsets', () => {
    const viewport = { scrollLeft: 180, scrollTop: 36, width: 360, height: 180 };
    expect(getCanvasCellAtPoint(0, 0, viewport, 300, 300)).toEqual({ row: 2, col: 10 });
    expect(getCanvasCellAtPoint(35, 17, viewport, 300, 300)).toEqual({ row: 2, col: 11 });
  });

  it('rejects points outside the logical canvas', () => {
    const viewport = { scrollLeft: 0, scrollTop: 0, width: 100, height: 100 };
    expect(getCanvasCellAtPoint(100, 100, viewport, 2, 2)).toBeNull();
  });

  it('clips visible bounds to the logical canvas', () => {
    expect(
      getVisibleCellBounds(
        { scrollLeft: 18, scrollTop: 36, width: 36, height: 36 },
        3,
        4,
      ),
    ).toEqual({ left: 1, top: 2, right: 2, bottom: 3 });
  });
});
