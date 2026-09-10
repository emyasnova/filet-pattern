import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { DragEvent, MouseEvent, PointerEvent } from 'react';

import type { CanvasCellUpdate } from '../../../application/paintCanvasCells';
import type { CanvasState } from '../../../domain/canvas';
import type { CanvasCell } from '../../../domain/cell';
import type { Pattern } from '../../../domain/pattern';
import type { CellPosition, SelectionRect } from '../../../domain/selection';
import { createSelectionRect, normalizeSelectionRect } from '../../../domain/selection';
import {
  CANVAS_CELL_SIZE,
  getCanvasCellAtPoint,
  getVisibleCellBounds,
  getZoomScrollOffset,
  type CanvasViewport,
} from './canvasGeometry';
import './CanvasGrid.css';

interface CanvasGridProps {
  canvas: CanvasState;
  draggedPattern: Pattern | null;
  isSelectionMode: boolean;
  onDropPattern: (pattern: Pattern, row: number, col: number) => void;
  onPaintCells: (updates: readonly CanvasCellUpdate[]) => void;
  onSelectRect: (selection: SelectionRect) => void;
  onSelectionContextMenu: (left: number, top: number) => void;
  selection: SelectionRect | null;
}

interface DrawingState {
  value: CanvasCell;
  updates: Map<string, CanvasCellUpdate>;
}

const EMPTY_VIEWPORT: CanvasViewport = { scrollLeft: 0, scrollTop: 0, width: 1, height: 1 };

export function CanvasGrid({
  canvas,
  draggedPattern,
  isSelectionMode,
  onDropPattern,
  onPaintCells,
  onSelectRect,
  onSelectionContextMenu,
  selection,
}: CanvasGridProps) {
  const frameRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawingRef = useRef<DrawingState | null>(null);
  const previewFrameRef = useRef<number | null>(null);
  const pendingPreviewRef = useRef<CellPosition | null>(null);
  const [viewport, setViewport] = useState<CanvasViewport>(EMPTY_VIEWPORT);
  const [previewPosition, setPreviewPosition] = useState<CellPosition | null>(null);
  const [selectionStart, setSelectionStart] = useState<CellPosition | null>(null);
  const [draftSelection, setDraftSelection] = useState<SelectionRect | null>(null);
  const [drawingVersion, setDrawingVersion] = useState(0);

  const [zoom, setZoom] = useState(100);
  const pendingZoomRef = useRef<{
    viewport: CanvasViewport;
    anchor: { x: number; y: number };
    previousCellSize: number;
  } | null>(null);
  const cellSize = CANVAS_CELL_SIZE * zoom / 100;
  const zoomDisabled = Boolean(drawingRef.current || selectionStart || draggedPattern);

  const activeSelection = useMemo(
    () => (draftSelection ?? selection ? normalizeSelectionRect((draftSelection ?? selection)!) : null),
    [draftSelection, selection],
  );

  const measureViewport = useCallback(() => {
    const frame = frameRef.current;
    if (!frame) return;
    setViewport({
      scrollLeft: frame.scrollLeft,
      scrollTop: frame.scrollTop,
      width: frame.clientWidth,
      height: frame.clientHeight,
    });
  }, []);

  const changeZoom = useCallback((nextZoom: number, anchor?: { x: number; y: number }) => {
    const frame = frameRef.current;
    if (!frame || drawingRef.current || selectionStart || draggedPattern) return;
    const next = Math.max(25, Math.min(300, nextZoom));
    if (next === zoom) return;
    pendingZoomRef.current = {
      viewport: {
        scrollLeft: frame.scrollLeft,
        scrollTop: frame.scrollTop,
        width: frame.clientWidth,
        height: frame.clientHeight,
      },
      anchor: anchor ?? { x: frame.clientWidth / 2, y: frame.clientHeight / 2 },
      previousCellSize: cellSize,
    };
    setZoom(next);
  }, [cellSize, draggedPattern, selectionStart, zoom]);

  useLayoutEffect(() => {
    const frame = frameRef.current;
    const pending = pendingZoomRef.current;
    if (!frame) return;
    if (pending) {
      const offset = getZoomScrollOffset(
        { ...pending.viewport, width: frame.clientWidth, height: frame.clientHeight },
        pending.anchor, pending.previousCellSize, cellSize, canvas.width, canvas.height,
      );
      frame.scrollLeft = offset.scrollLeft;
      frame.scrollTop = offset.scrollTop;
      pendingZoomRef.current = null;
    }
    measureViewport();
  }, [canvas.width, canvas.height, cellSize, measureViewport]);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const handleWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      if (event.deltaY === 0) return;
      const rect = frame.getBoundingClientRect();
      changeZoom(zoom + (event.deltaY < 0 ? 25 : -25), {
        x: event.clientX - rect.left - frame.clientLeft,
        y: event.clientY - rect.top - frame.clientTop,
      });
    };
    frame.addEventListener('wheel', handleWheel, { passive: false });
    return () => frame.removeEventListener('wheel', handleWheel);
  }, [changeZoom, zoom]);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    measureViewport();
    const observer = new ResizeObserver(measureViewport);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [measureViewport]);

  useEffect(() => () => {
    if (previewFrameRef.current !== null) cancelAnimationFrame(previewFrameRef.current);
  }, []);

  useLayoutEffect(() => {
    const element = canvasRef.current;
    if (!element) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const cssWidth = Math.max(1, Math.min(viewport.width, canvas.width * cellSize));
    const cssHeight = Math.max(1, Math.min(viewport.height, canvas.height * cellSize));
    element.style.width = `${cssWidth}px`;
    element.style.height = `${cssHeight}px`;
    element.width = Math.ceil(cssWidth * ratio);
    element.height = Math.ceil(cssHeight * ratio);
    const context = element.getContext('2d');
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    drawCanvas(context, canvas, viewport, activeSelection, previewPosition, draggedPattern, drawingRef.current, cellSize);
  }, [activeSelection, canvas, draggedPattern, drawingVersion, previewPosition, viewport, cellSize]);

  const pointFromEvent = (clientX: number, clientY: number) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return null;
    return getCanvasCellAtPoint(
      clientX - rect.left,
      clientY - rect.top,
      viewport,
      canvas.width,
      canvas.height,
      cellSize,
    );
  };

  const addPaintCell = (position: CellPosition) => {
    const drawing = drawingRef.current;
    if (!drawing) return;
    const key = `${position.row}:${position.col}`;
    if (drawing.updates.has(key)) return;
    drawing.updates.set(key, { ...position, value: drawing.value });
    setDrawingVersion((version) => version + 1);
  };

  const handlePointerDown = (event: PointerEvent<HTMLCanvasElement>) => {
    if (event.button !== 0) return;
    const position = pointFromEvent(event.clientX, event.clientY);
    if (!position) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    if (isSelectionMode) {
      const next = createSelectionRect(position, position);
      setSelectionStart(position);
      setDraftSelection(next);
      onSelectRect(next);
      return;
    }
    drawingRef.current = {
      value: canvas.cells[position.row][position.col] === 1 ? 0 : 1,
      updates: new Map(),
    };
    addPaintCell(position);
  };

  const handlePointerMove = (event: PointerEvent<HTMLCanvasElement>) => {
    const position = pointFromEvent(event.clientX, event.clientY);
    if (!position) return;
    if (drawingRef.current) {
      addPaintCell(position);
    } else if (selectionStart) {
      const next = createSelectionRect(selectionStart, position);
      setDraftSelection(next);
      onSelectRect(next);
    }
  };

  const handlePointerUp = (event: PointerEvent<HTMLCanvasElement>) => {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    if (drawingRef.current) {
      const updates = [...drawingRef.current.updates.values()];
      drawingRef.current = null;
      setDrawingVersion((version) => version + 1);
      onPaintCells(updates);
    }
    setSelectionStart(null);
    setDraftSelection(null);
  };

  const schedulePreview = (position: CellPosition | null) => {
    pendingPreviewRef.current = position;
    if (previewFrameRef.current !== null) return;
    previewFrameRef.current = requestAnimationFrame(() => {
      previewFrameRef.current = null;
      setPreviewPosition(pendingPreviewRef.current);
    });
  };

  const handleDragOver = (event: DragEvent<HTMLCanvasElement>) => {
    if (!draggedPattern) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    schedulePreview(pointFromEvent(event.clientX, event.clientY));
  };

  const handleDrop = (event: DragEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    const position = pointFromEvent(event.clientX, event.clientY);
    schedulePreview(null);
    if (draggedPattern && position) onDropPattern(draggedPattern, position.row, position.col);
  };

  const handleContextMenu = (event: MouseEvent<HTMLCanvasElement>) => {
    if (!activeSelection) return;
    const position = pointFromEvent(event.clientX, event.clientY);
    if (!position || position.row < activeSelection.top || position.row > activeSelection.bottom || position.col < activeSelection.left || position.col > activeSelection.right) return;
    event.preventDefault();
    onSelectionContextMenu(event.clientX, event.clientY);
  };

  return (
    <>
      <div className="canvas-zoom-controls" role="group" aria-label="Масштаб рабочей области">
        <button type="button" aria-label="Уменьшить масштаб" disabled={zoomDisabled || zoom === 25} onClick={() => changeZoom(zoom - 25)}>−</button>
        <output aria-live="polite" aria-label="Текущий масштаб">{zoom}%</output>
        <button type="button" aria-label="Увеличить масштаб" disabled={zoomDisabled || zoom === 300} onClick={() => changeZoom(zoom + 25)}>+</button>
        <button type="button" disabled={zoomDisabled || zoom === 100} onClick={() => changeZoom(100)}>Сбросить на 100%</button>
        <span>Ctrl/Cmd + колесо — масштаб</span>
      </div>
      <div className="canvas-grid-frame" ref={frameRef} onScroll={measureViewport}>
        <div
          className="canvas-grid-surface"
          style={{ width: canvas.width * cellSize, height: canvas.height * cellSize }}
        >
          <canvas
            ref={canvasRef}
            className={isSelectionMode ? 'canvas-grid selection-mode' : 'canvas-grid'}
            role="grid"
            aria-label={`Рабочая область ${canvas.width} x ${canvas.height}`}
            onContextMenu={handleContextMenu}
            onDragOver={handleDragOver}
            onDragLeave={() => schedulePreview(null)}
            onDrop={handleDrop}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerCancel={handlePointerUp}
            onPointerUp={handlePointerUp}
          />
        </div>
      </div>
    </>
  );
}

function drawCanvas(
  context: CanvasRenderingContext2D,
  canvas: CanvasState,
  viewport: CanvasViewport,
  selection: ReturnType<typeof normalizeSelectionRect> | null,
  preview: CellPosition | null,
  pattern: Pattern | null,
  drawing: DrawingState | null,
  cellSize: number,
) {
  context.clearRect(0, 0, viewport.width, viewport.height);
  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, viewport.width, viewport.height);
  const bounds = getVisibleCellBounds(viewport, canvas.width, canvas.height, cellSize);
  const draft = drawing?.updates;

  for (let row = bounds.top; row <= bounds.bottom; row += 1) {
    for (let col = bounds.left; col <= bounds.right; col += 1) {
      const x = col * cellSize - viewport.scrollLeft;
      const y = row * cellSize - viewport.scrollTop;
      const value = draft?.get(`${row}:${col}`)?.value ?? canvas.cells[row][col];
      context.fillStyle = value === 1 ? '#111111' : '#ffffff';
      context.fillRect(x, y, cellSize, cellSize);
      context.strokeStyle = '#d6dbe3';
      context.lineWidth = 1;
      context.strokeRect(x + 0.5, y + 0.5, cellSize, cellSize);
      if ((col + 1) % 10 === 0) {
        context.strokeStyle = '#727986';
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(x + cellSize, y);
        context.lineTo(x + cellSize, y + cellSize);
        context.stroke();
      }
      if ((row + 1) % 10 === 0) {
        context.strokeStyle = '#727986';
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(x, y + cellSize);
        context.lineTo(x + cellSize, y + cellSize);
        context.stroke();
      }
      if (selection && row >= selection.top && row <= selection.bottom && col >= selection.left && col <= selection.right) {
        context.strokeStyle = '#2f6fed';
        context.lineWidth = 2;
        context.strokeRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
      }
    }
  }

  if (!preview || !pattern) return;
  for (let row = bounds.top; row <= bounds.bottom; row += 1) {
    const patternRow = row - preview.row;
    if (patternRow < 0 || patternRow >= pattern.height) continue;
    for (let col = bounds.left; col <= bounds.right; col += 1) {
      const patternCol = col - preview.col;
      if (patternCol < 0 || patternCol >= pattern.width) continue;
      const value = pattern.cells[patternRow][patternCol];
      if (value === null) continue;
      const x = col * cellSize - viewport.scrollLeft;
      const y = row * cellSize - viewport.scrollTop;
      context.fillStyle = value === 1 ? 'rgba(17,17,17,.45)' : 'rgba(255,255,255,.65)';
      context.fillRect(x, y, cellSize, cellSize);
      context.strokeStyle = 'rgba(47,111,237,.8)';
      context.lineWidth = 2;
      context.strokeRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
    }
  }
}
