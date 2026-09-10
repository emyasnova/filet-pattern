import { describe, expect, it } from 'vitest';

import { getCanvasCellAtPoint, getVisibleCellBounds, getZoomScrollOffset } from './canvasGeometry';

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

describe('zoomed canvas geometry', () => {
  it.each([4.5, 18, 54])('maps cells and visible bounds at cell size %s', (cellSize) => {
    const viewport = {
      scrollLeft: 10 * cellSize, scrollTop: 2 * cellSize,
      width: 4 * cellSize, height: 3 * cellSize,
    };
    expect(getCanvasCellAtPoint(cellSize * 1.9, cellSize * 0.9, viewport, 100, 100, cellSize))
      .toEqual({ row: 2, col: 11 });
    expect(getCanvasCellAtPoint(cellSize, cellSize, viewport, 100, 100, cellSize))
      .toEqual({ row: 3, col: 11 });
    expect(getVisibleCellBounds(viewport, 100, 100, cellSize))
      .toEqual({ left: 10, top: 2, right: 14, bottom: 5 });
    expect(getCanvasCellAtPoint(90 * cellSize, 0, viewport, 100, 100, cellSize)).toBeNull();
    expect(getCanvasCellAtPoint(-11 * cellSize, 0, viewport, 100, 100, cellSize)).toBeNull();
  });

  it.each([4.5, 54])('preserves the logical position under the anchor at cell size %s', (cellSize) => {
    const viewport = { scrollLeft: 900, scrollTop: 900, width: 180, height: 180 };
    const anchor = { x: 72, y: 90 };
    const offset = getZoomScrollOffset(viewport, anchor, 18, cellSize, 100, 100);
    expect((offset.scrollLeft + anchor.x) / cellSize).toBe((viewport.scrollLeft + anchor.x) / 18);
    expect((offset.scrollTop + anchor.y) / cellSize).toBe((viewport.scrollTop + anchor.y) / 18);
  });

  it('clamps scrolling when zooming out near the bottom-right edge', () => {
    expect(getZoomScrollOffset(
      { scrollLeft: 1620, scrollTop: 1620, width: 180, height: 180 },
      { x: 0, y: 0 }, 18, 4.5, 100, 100,
    )).toEqual({ scrollLeft: 270, scrollTop: 270 });
  });

  it('resets scroll offsets when the whole canvas fits inside the viewport', () => {
    expect(getZoomScrollOffset(
      { scrollLeft: 90, scrollTop: 90, width: 600, height: 600 },
      { x: 300, y: 300 }, 18, 4.5, 100, 100,
    )).toEqual({ scrollLeft: 0, scrollTop: 0 });
    expect(getVisibleCellBounds(
      { scrollLeft: 0, scrollTop: 0, width: 600, height: 600 }, 100, 100, 4.5,
    )).toEqual({ left: 0, top: 0, right: 99, bottom: 99 });
  });

  it('clamps negative offsets when zooming out at the top-left corner', () => {
    expect(getZoomScrollOffset(
      { scrollLeft: 0, scrollTop: 0, width: 180, height: 180 },
      { x: 90, y: 90 }, 18, 4.5, 100, 100,
    )).toEqual({ scrollLeft: 0, scrollTop: 0 });
  });
});
