import type { CanvasState } from '../domain/canvas';

const CELL_SIZE = 12;
const PADDING = 24;
const LABEL_HEIGHT = 32;

export function exportCanvasToPng(canvas: CanvasState): void {
  const exportCanvas = document.createElement('canvas');
  const width = canvas.width * CELL_SIZE + PADDING * 2;
  const height = canvas.height * CELL_SIZE + PADDING * 2 + LABEL_HEIGHT;
  const context = exportCanvas.getContext('2d');

  exportCanvas.width = width;
  exportCanvas.height = height;

  if (!context) {
    return;
  }

  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, width, height);

  context.fillStyle = '#111111';
  canvas.cells.forEach((row, rowIndex) => {
    row.forEach((cell, colIndex) => {
      if (cell === 1) {
        context.fillRect(
          PADDING + colIndex * CELL_SIZE,
          PADDING + rowIndex * CELL_SIZE,
          CELL_SIZE,
          CELL_SIZE,
        );
      }
    });
  });

  drawGrid(context, canvas.width, canvas.height);

  context.fillStyle = '#111111';
  context.font = '16px sans-serif';
  context.fillText(
    `${canvas.width} x ${canvas.height} cells`,
    PADDING,
    PADDING + canvas.height * CELL_SIZE + 24,
  );

  const link = document.createElement('a');
  link.href = exportCanvas.toDataURL('image/png');
  link.download = 'filet-crochet-canvas.png';
  link.click();
}

function drawGrid(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
): void {
  for (let col = 0; col <= width; col += 1) {
    const x = PADDING + col * CELL_SIZE;
    context.beginPath();
    context.strokeStyle = col % 10 === 0 ? '#777777' : '#d0d0d0';
    context.lineWidth = col % 10 === 0 ? 1.5 : 0.75;
    context.moveTo(x, PADDING);
    context.lineTo(x, PADDING + height * CELL_SIZE);
    context.stroke();
  }

  for (let row = 0; row <= height; row += 1) {
    const y = PADDING + row * CELL_SIZE;
    context.beginPath();
    context.strokeStyle = row % 10 === 0 ? '#777777' : '#d0d0d0';
    context.lineWidth = row % 10 === 0 ? 1.5 : 0.75;
    context.moveTo(PADDING, y);
    context.lineTo(PADDING + width * CELL_SIZE, y);
    context.stroke();
  }
}
