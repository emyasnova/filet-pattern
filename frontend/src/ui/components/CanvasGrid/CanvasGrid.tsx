import { memo, useCallback, useMemo, useState } from 'react';
import type { DragEvent, MouseEvent, PointerEvent } from 'react';

import type { CanvasState } from '../../../domain/canvas';
import type { CanvasCell } from '../../../domain/cell';
import type { Pattern } from '../../../domain/pattern';
import type {
  CellPosition,
  NormalizedSelectionRect,
  SelectionRect,
} from '../../../domain/selection';
import { createSelectionRect, normalizeSelectionRect } from '../../../domain/selection';
import './CanvasGrid.css';

interface CanvasGridProps {
  canvas: CanvasState;
  draggedPattern: Pattern | null;
  isSelectionMode: boolean;
  onDropPattern: (pattern: Pattern, row: number, col: number) => void;
  onSelectRect: (selection: SelectionRect) => void;
  onSelectionContextMenu: (left: number, top: number) => void;
  onSetCell: (row: number, col: number, value: CanvasCell) => void;
  onToggleCell: (row: number, col: number) => void;
  selection: SelectionRect | null;
}

interface CanvasRowProps {
  row: number;
  cells: CanvasCell[];
  selection: NormalizedSelectionRect | null;
}

interface PreviewPosition {
  row: number;
  col: number;
}

interface DrawingState {
  value: CanvasCell;
  lastCellKey: string;
}

const CanvasRow = memo(function CanvasRow({ row, cells, selection }: CanvasRowProps) {
  const rowClassName = ['canvas-row', (row + 1) % 10 === 0 ? 'block-bottom' : '']
    .filter(Boolean)
    .join(' ');

  return (
    <div className={rowClassName} role="row">
      {cells.map((cell, col) => {
        const isFilled = cell === 1;
        const isSelected = Boolean(
          selection &&
            row >= selection.top &&
            row <= selection.bottom &&
            col >= selection.left &&
            col <= selection.right,
        );
        const className = [
          'canvas-cell',
          isFilled ? 'filled' : '',
          isSelected ? 'selected' : '',
          (col + 1) % 10 === 0 ? 'block-right' : '',
        ]
          .filter(Boolean)
          .join(' ');

        return (
          <div
            className={className}
            data-col={col}
            data-row={row}
            key={col}
            role="gridcell"
            aria-label={`Клетка ${row + 1}, ${col + 1}`}
            aria-selected={isFilled}
          />
        );
      })}
    </div>
  );
});

export function CanvasGrid({
  canvas,
  draggedPattern,
  isSelectionMode,
  onDropPattern,
  onSelectRect,
  onSelectionContextMenu,
  onSetCell,
  onToggleCell,
  selection,
}: CanvasGridProps) {
  const [drawingState, setDrawingState] = useState<DrawingState | null>(null);
  const [previewPosition, setPreviewPosition] = useState<PreviewPosition | null>(null);
  const [selectionStart, setSelectionStart] = useState<CellPosition | null>(null);
  const [draftSelection, setDraftSelection] = useState<SelectionRect | null>(null);

  const activeSelection = draftSelection ?? selection;
  const effectiveSelection = useMemo(
    () => (activeSelection ? normalizeSelectionRect(activeSelection) : null),
    [activeSelection],
  );

  const handlePointerDown = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (event.button !== 0) {
        return;
      }

      const position = getCellPosition(event.target);

      if (!position) {
        return;
      }

      if (isSelectionMode) {
        event.preventDefault();
        event.currentTarget.setPointerCapture(event.pointerId);

        const nextSelection = createSelectionRect(position, position);
        setSelectionStart(position);
        setDraftSelection(nextSelection);
        onSelectRect(nextSelection);
        return;
      }

      event.preventDefault();
      event.currentTarget.setPointerCapture(event.pointerId);

      const nextValue: CanvasCell = canvas.cells[position.row][position.col] === 1 ? 0 : 1;
      setDrawingState({
        value: nextValue,
        lastCellKey: getCellKey(position),
      });
      onToggleCell(position.row, position.col);
    },
    [canvas.cells, isSelectionMode, onSelectRect, onToggleCell],
  );

  const handlePointerMove = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (drawingState) {
        const target = document.elementFromPoint(event.clientX, event.clientY);

        if (!target || !event.currentTarget.contains(target)) {
          return;
        }

        const position = getCellPosition(target);

        if (!position) {
          return;
        }

        const cellKey = getCellKey(position);

        if (cellKey === drawingState.lastCellKey) {
          return;
        }

        setDrawingState({
          ...drawingState,
          lastCellKey: cellKey,
        });
        onSetCell(position.row, position.col, drawingState.value);
        return;
      }

      if (!selectionStart) {
        return;
      }

      const target = document.elementFromPoint(event.clientX, event.clientY);

      if (!target || !event.currentTarget.contains(target)) {
        return;
      }

      const position = getCellPosition(target);

      if (!position) {
        return;
      }

      const nextSelection = createSelectionRect(selectionStart, position);
      setDraftSelection(nextSelection);
      onSelectRect(nextSelection);
    },
    [drawingState, onSelectRect, onSetCell, selectionStart],
  );

  const handlePointerUp = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (drawingState) {
        if (event.currentTarget.hasPointerCapture(event.pointerId)) {
          event.currentTarget.releasePointerCapture(event.pointerId);
        }

        setDrawingState(null);
        return;
      }

      if (!selectionStart) {
        return;
      }

      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }

      setSelectionStart(null);
      setDraftSelection(null);
    },
    [drawingState, selectionStart],
  );

  const handleDragOver = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      if (!draggedPattern) {
        return;
      }

      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';

      const cell = (event.target as HTMLElement).closest<HTMLElement>('.canvas-cell');

      if (!cell) {
        setPreviewPosition(null);
        return;
      }

      const row = Number(cell.dataset.row);
      const col = Number(cell.dataset.col);

      if (!Number.isInteger(row) || !Number.isInteger(col)) {
        setPreviewPosition(null);
        return;
      }

      setPreviewPosition((current) => {
        if (current?.row === row && current.col === col) {
          return current;
        }

        return { row, col };
      });
    },
    [draggedPattern],
  );

  const handleDragLeave = useCallback((event: DragEvent<HTMLDivElement>) => {
    const nextTarget = event.relatedTarget;

    if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) {
      return;
    }

    setPreviewPosition(null);
  }, []);

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setPreviewPosition(null);

      if (!draggedPattern) {
        return;
      }

      const cell = (event.target as HTMLElement).closest<HTMLElement>('.canvas-cell');

      if (!cell) {
        return;
      }

      const row = Number(cell.dataset.row);
      const col = Number(cell.dataset.col);

      if (!Number.isInteger(row) || !Number.isInteger(col)) {
        return;
      }

      onDropPattern(draggedPattern, row, col);
    },
    [draggedPattern, onDropPattern],
  );

  const handleContextMenu = useCallback(
    (event: MouseEvent<HTMLDivElement>) => {
      if (!effectiveSelection) {
        return;
      }

      const position = getCellPosition(event.target);

      if (
        !position ||
        position.row < effectiveSelection.top ||
        position.row > effectiveSelection.bottom ||
        position.col < effectiveSelection.left ||
        position.col > effectiveSelection.right
      ) {
        return;
      }

      event.preventDefault();
      onSelectionContextMenu(event.clientX, event.clientY);
    },
    [effectiveSelection, onSelectionContextMenu],
  );

  const previewCells = useMemo(() => {
    if (!draggedPattern || !previewPosition) {
      return [];
    }

    const cells: Array<{
      cell: CanvasCell;
      key: string;
      rowOffset: number;
      colOffset: number;
    }> = [];

    for (let patternRow = 0; patternRow < draggedPattern.height; patternRow += 1) {
      const canvasRow = previewPosition.row + patternRow;

      if (canvasRow < 0 || canvasRow >= canvas.height) {
        continue;
      }

      for (let patternCol = 0; patternCol < draggedPattern.width; patternCol += 1) {
        const canvasCol = previewPosition.col + patternCol;

        if (canvasCol < 0 || canvasCol >= canvas.width) {
          continue;
        }

        const cell = draggedPattern.cells[patternRow][patternCol];

        if (cell === null) {
          continue;
        }

        cells.push({
          cell,
          key: `${patternRow}-${patternCol}`,
          rowOffset: patternRow,
          colOffset: patternCol,
        });
      }
    }

    return cells;
  }, [canvas.height, canvas.width, draggedPattern, previewPosition]);

  return (
    <div className="canvas-grid-frame">
      <div
        className={['canvas-grid', isSelectionMode ? 'selection-mode' : '']
          .filter(Boolean)
          .join(' ')}
        role="grid"
        aria-label={`Рабочая область ${canvas.width} x ${canvas.height}`}
        onContextMenu={handleContextMenu}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerCancel={handlePointerUp}
        onPointerUp={handlePointerUp}
      >
        {canvas.cells.map((row, rowIndex) => (
          <CanvasRow
            cells={row}
            key={rowIndex}
            row={rowIndex}
            selection={effectiveSelection}
          />
        ))}

        {draggedPattern && previewPosition && previewCells.length > 0 ? (
          <div className="canvas-drop-preview" aria-hidden="true">
            {previewCells.map((previewCell) => (
              <span
                className={[
                  'canvas-drop-preview-cell',
                  previewCell.cell === 1 ? 'fill' : 'clear',
                ].join(' ')}
                key={previewCell.key}
                style={{
                  transform: `translate(${(previewPosition.col + previewCell.colOffset) * 18}px, ${
                    (previewPosition.row + previewCell.rowOffset) * 18
                  }px)`,
                }}
              />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function getCellPosition(target: EventTarget | null): CellPosition | null {
  if (!(target instanceof HTMLElement)) {
    return null;
  }

  const cell = target.closest<HTMLElement>('.canvas-cell');

  if (!cell) {
    return null;
  }

  const row = Number(cell.dataset.row);
  const col = Number(cell.dataset.col);

  if (!Number.isInteger(row) || !Number.isInteger(col)) {
    return null;
  }

  return { row, col };
}

function getCellKey(position: CellPosition): string {
  return `${position.row}:${position.col}`;
}
