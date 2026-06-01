import type { Pattern } from '../../../domain/pattern';
import './PatternPreview.css';

interface PatternPreviewProps {
  pattern: Pattern;
}

const MAX_PREVIEW_CELLS = 18;

export function PatternPreview({ pattern }: PatternPreviewProps) {
  const cellSize = Math.max(
    5,
    Math.floor(144 / Math.max(pattern.width, pattern.height, MAX_PREVIEW_CELLS)),
  );

  return (
    <div
      className="pattern-preview"
      style={{
        gridTemplateColumns: `repeat(${pattern.width}, ${cellSize}px)`,
      }}
      aria-label={`${pattern.width} x ${pattern.height}`}
    >
      {pattern.cells.map((row, rowIndex) =>
        row.map((cell, colIndex) => (
          <span
            className={cell === 1 ? 'pattern-preview-cell filled' : 'pattern-preview-cell'}
            key={`${rowIndex}-${colIndex}`}
          />
        )),
      )}
    </div>
  );
}
