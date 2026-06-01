import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import './SizeControls.css';

export const MIN_CANVAS_SIZE = 1;
export const MAX_CANVAS_SIZE = 300;

interface SizeControlsProps {
  width: number;
  height: number;
  onApplySize: (width: number, height: number) => void;
}

export function SizeControls({ width, height, onApplySize }: SizeControlsProps) {
  const [draftWidth, setDraftWidth] = useState(width);
  const [draftHeight, setDraftHeight] = useState(height);

  useEffect(() => {
    setDraftWidth(width);
    setDraftHeight(height);
  }, [width, height]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    onApplySize(clampSize(draftWidth), clampSize(draftHeight));
  };

  return (
    <form className="size-controls" onSubmit={handleSubmit}>
      <label>
        <span>Ширина</span>
        <input
          type="number"
          min={MIN_CANVAS_SIZE}
          max={MAX_CANVAS_SIZE}
          value={draftWidth}
          onChange={(event) => setDraftWidth(Number(event.target.value))}
        />
      </label>

      <label>
        <span>Высота</span>
        <input
          type="number"
          min={MIN_CANVAS_SIZE}
          max={MAX_CANVAS_SIZE}
          value={draftHeight}
          onChange={(event) => setDraftHeight(Number(event.target.value))}
        />
      </label>

      <button type="submit">Применить</button>
    </form>
  );
}

function clampSize(value: number): number {
  if (!Number.isFinite(value)) {
    return MIN_CANVAS_SIZE;
  }

  return Math.min(MAX_CANVAS_SIZE, Math.max(MIN_CANVAS_SIZE, Math.round(value)));
}
