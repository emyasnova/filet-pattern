import { memo, useLayoutEffect, useRef } from 'react';

import type { Pattern } from '../../../domain/pattern';
import './PatternPreview.css';

interface PatternPreviewProps {
  pattern: Pattern;
}

const MAX_PREVIEW_SIZE = 144;

export const PatternPreview = memo(function PatternPreview({ pattern }: PatternPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const scale = Math.min(MAX_PREVIEW_SIZE / pattern.width, MAX_PREVIEW_SIZE / pattern.height);
  const width = Math.max(1, Math.round(pattern.width * scale));
  const height = Math.max(1, Math.round(pattern.height * scale));

  useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.ceil(width * ratio);
    canvas.height = Math.ceil(height * ratio);
    const context = canvas.getContext('2d');
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, width, height);
    const cellWidth = width / pattern.width;
    const cellHeight = height / pattern.height;
    context.fillStyle = '#111111';
    pattern.cells.forEach((row, rowIndex) => {
      row.forEach((cell, colIndex) => {
        if (cell === 1) {
          context.fillRect(colIndex * cellWidth, rowIndex * cellHeight, cellWidth, cellHeight);
        }
      });
    });
    if (Math.min(cellWidth, cellHeight) >= 4) {
      context.strokeStyle = '#c8ced8';
      context.lineWidth = 1;
      for (let col = 0; col <= pattern.width; col += 1) {
        context.beginPath();
        context.moveTo(col * cellWidth, 0);
        context.lineTo(col * cellWidth, height);
        context.stroke();
      }
      for (let row = 0; row <= pattern.height; row += 1) {
        context.beginPath();
        context.moveTo(0, row * cellHeight);
        context.lineTo(width, row * cellHeight);
        context.stroke();
      }
    }
  }, [height, pattern, width]);

  return (
    <canvas
      ref={canvasRef}
      className="pattern-preview"
      style={{ width, height }}
      aria-label={`${pattern.width} x ${pattern.height}`}
      role="img"
    />
  );
});
