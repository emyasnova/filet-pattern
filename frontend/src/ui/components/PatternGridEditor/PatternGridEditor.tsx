import { useRef } from 'react';

import { normalizePatternTransparency } from '../../../application/normalizePatternTransparency';
import type { PatternCell } from '../../../domain/cell';
import './PatternGridEditor.css';

interface PatternGridEditorProps {
  cells: PatternCell[][];
  zoom: number;
  onChange: (cells: PatternCell[][]) => void;
}

type Brush = 0 | 1;

export function PatternGridEditor({ cells, zoom, onChange }: PatternGridEditorProps) {
  const brushRef = useRef<Brush | null>(null);
  const paintedCellsRef = useRef<PatternCell[][] | null>(null);

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
    brushRef.current = cells[row]?.[column] === 1 ? 0 : 1;
    paintedCellsRef.current = cells.map((currentRow) => [...currentRow]);
    paint(row, column);
  };

  const finishPainting = () => {
    if (brushRef.current === null || !paintedCellsRef.current) return;

    onChange(normalizePatternTransparency(paintedCellsRef.current));
    brushRef.current = null;
    paintedCellsRef.current = null;
  };

  return (
    <div className="pattern-grid-editor">
      <div
        className="pattern-grid-viewport"
        onPointerCancel={finishPainting}
        onPointerLeave={finishPainting}
        onPointerUp={finishPainting}
      >
        <div
          className="pattern-edit-grid"
          style={{
            gridTemplateColumns: `repeat(${cells[0]?.length ?? 0}, ${zoom}px)`,
          }}
        >
          {cells.flatMap((row, rowIndex) =>
            row.map((cell, columnIndex) => (
              <button
                type="button"
                className={`pattern-edit-cell pattern-edit-cell--${cell === null ? 'null' : cell}`}
                key={`${rowIndex}-${columnIndex}`}
                style={{ width: zoom, height: zoom }}
                aria-label={`Строка ${rowIndex + 1}, столбец ${columnIndex + 1}`}
                onPointerDown={(event) => {
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
