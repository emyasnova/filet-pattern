import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';

import { normalizePatternTransparency } from '../../../application/normalizePatternTransparency';
import type { PatternCell } from '../../../domain/cell';
import { CANVAS_CELL_SIZE, getZoomScrollOffset, type CanvasViewport } from '../CanvasGrid/canvasGeometry';
import './PatternGridEditor.css';

interface PatternGridEditorProps {
  cells: PatternCell[][];
  zoom: number;
  onZoomChange: (zoom: number) => void;
  onChange: (cells: PatternCell[][]) => void;
}

type Brush = 0 | 1;

export function PatternGridEditor({ cells, zoom, onZoomChange, onChange }: PatternGridEditorProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const pendingZoomRef = useRef<{
    viewport: CanvasViewport;
    anchor: { x: number; y: number };
    previousCellSize: number;
  } | null>(null);
  const [isPainting, setIsPainting] = useState(false);
  const cellSize = CANVAS_CELL_SIZE * zoom / 100;
  const width = cells[0]?.length ?? 0;
  const height = cells.length;
  const brushRef = useRef<Brush | null>(null);
  const paintedCellsRef = useRef<PatternCell[][] | null>(null);

  const changeZoom = useCallback((nextZoom: number, anchor?: { x: number; y: number }) => {
    const viewport = viewportRef.current;
    if (!viewport || brushRef.current !== null) return;
    const next = Math.max(25, Math.min(300, nextZoom));
    if (next === zoom) return;
    pendingZoomRef.current = {
      viewport: {
        scrollLeft: viewport.scrollLeft, scrollTop: viewport.scrollTop,
        width: viewport.clientWidth, height: viewport.clientHeight,
      },
      anchor: anchor ?? { x: viewport.clientWidth / 2, y: viewport.clientHeight / 2 },
      previousCellSize: cellSize,
    };
    onZoomChange(next);
  }, [cellSize, onZoomChange, zoom]);

  useLayoutEffect(() => {
    const viewport = viewportRef.current;
    const pending = pendingZoomRef.current;
    if (!viewport || !pending) return;
    const offset = getZoomScrollOffset(
      { ...pending.viewport, width: viewport.clientWidth, height: viewport.clientHeight },
      pending.anchor, pending.previousCellSize, cellSize, width, height,
    );
    viewport.scrollLeft = offset.scrollLeft;
    viewport.scrollTop = offset.scrollTop;
    pendingZoomRef.current = null;
  }, [cellSize, height, width]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const handleWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      if (!event.deltaY) return;
      const rect = viewport.getBoundingClientRect();
      changeZoom(zoom + (event.deltaY < 0 ? 25 : -25), {
        x: event.clientX - rect.left - viewport.clientLeft,
        y: event.clientY - rect.top - viewport.clientTop,
      });
    };
    viewport.addEventListener('wheel', handleWheel, { passive: false });
    return () => viewport.removeEventListener('wheel', handleWheel);
  }, [changeZoom, zoom]);

  const paint = (row: number, column: number) => {
    const brush = brushRef.current;
    const paintedCells = paintedCellsRef.current;
    if (brush === null || !paintedCells || paintedCells[row]?.[column] === brush) return;

    const next = paintedCells.map((currentRow) => [...currentRow]);
    next[row][column] = brush;
    paintedCellsRef.current = next;
    onChange(next);
  };

  const startPainting = (row: number, column: number) => {
    setIsPainting(true);
    brushRef.current = cells[row]?.[column] === 1 ? 0 : 1;
    paintedCellsRef.current = cells.map((currentRow) => [...currentRow]);
    paint(row, column);
  };

  const finishPainting = () => {
    if (brushRef.current === null || !paintedCellsRef.current) return;

    onChange(normalizePatternTransparency(paintedCellsRef.current));
    brushRef.current = null;
    paintedCellsRef.current = null;
    setIsPainting(false);
  };

  return (
    <div className="pattern-grid-editor">
      <div className="pattern-preview-zoom" role="group" aria-label="Масштаб предпросмотра паттерна">
        <button type="button" aria-label="Уменьшить масштаб" disabled={isPainting || zoom === 25} onClick={() => changeZoom(zoom - 25)}>−</button>
        <output aria-live="polite" aria-label="Текущий масштаб">{zoom}%</output>
        <button type="button" aria-label="Увеличить масштаб" disabled={isPainting || zoom === 300} onClick={() => changeZoom(zoom + 25)}>+</button>
        <button type="button" disabled={isPainting || zoom === 100} onClick={() => changeZoom(100)}>Сбросить на 100%</button>
        <span>Ctrl/Cmd + колесо — масштаб</span>
      </div>
      <div
        className="pattern-grid-viewport"
        ref={viewportRef}
        onPointerCancel={finishPainting}
        onPointerLeave={finishPainting}
        onPointerUp={finishPainting}
      >
        <div
          className="pattern-edit-grid"
          style={{
            gridTemplateColumns: `repeat(${cells[0]?.length ?? 0}, ${cellSize}px)`,
          }}
        >
          {cells.flatMap((row, rowIndex) =>
            row.map((cell, columnIndex) => (
              <button
                type="button"
                className={`pattern-edit-cell pattern-edit-cell--${cell === null ? 'null' : cell}`}
                key={`${rowIndex}-${columnIndex}`}
                style={{ width: cellSize, height: cellSize }}
                aria-label={`Строка ${rowIndex + 1}, столбец ${columnIndex + 1}`}
                onPointerDown={(event) => {
                  if (event.button !== 0) return;
                  event.preventDefault();
                  startPainting(rowIndex, columnIndex);
                }}
                onPointerEnter={() => {
                  paint(rowIndex, columnIndex);
                }}
              />
            )),
          )}
        </div>
      </div>
    </div>
  );
}
