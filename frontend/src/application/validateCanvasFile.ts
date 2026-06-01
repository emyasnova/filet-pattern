import type { CanvasState } from '../domain/canvas';
import type { CanvasCell } from '../domain/cell';

export const CANVAS_FILE_VERSION = 1;
export const CANVAS_FILE_TYPE = 'filet-crochet-canvas';

export interface CanvasFile {
  version: typeof CANVAS_FILE_VERSION;
  type: typeof CANVAS_FILE_TYPE;
  width: number;
  height: number;
  cells: CanvasCell[][];
}

export interface ValidateCanvasFileResult {
  canvas?: CanvasState;
  errors: string[];
}

export function createCanvasFile(canvas: CanvasState): CanvasFile {
  return {
    version: CANVAS_FILE_VERSION,
    type: CANVAS_FILE_TYPE,
    width: canvas.width,
    height: canvas.height,
    cells: canvas.cells,
  };
}

export function validateCanvasFile(data: unknown): ValidateCanvasFileResult {
  const errors: string[] = [];

  if (!isRecord(data)) {
    return { errors: ['Файл должен быть JSON-объектом.'] };
  }

  if (data.version !== CANVAS_FILE_VERSION) {
    errors.push(`version должен быть ${CANVAS_FILE_VERSION}.`);
  }

  if (data.type !== CANVAS_FILE_TYPE) {
    errors.push(`type должен быть ${CANVAS_FILE_TYPE}.`);
  }

  if (!isPositiveInteger(data.width)) {
    errors.push('width должен быть положительным целым числом.');
  }

  if (!isPositiveInteger(data.height)) {
    errors.push('height должен быть положительным целым числом.');
  }

  if (!Array.isArray(data.cells)) {
    errors.push('cells должен быть массивом.');
  } else if (isPositiveInteger(data.height) && data.cells.length !== data.height) {
    errors.push(`Количество строк cells должно быть равно height ${data.height}.`);
  }

  if (Array.isArray(data.cells) && isPositiveInteger(data.width)) {
    data.cells.forEach((row, rowIndex) => {
      if (!Array.isArray(row)) {
        errors.push(`cells[${rowIndex}] должен быть массивом.`);
        return;
      }

      if (row.length !== data.width) {
        errors.push(`Длина cells[${rowIndex}] должна быть равна width ${data.width}.`);
      }

      row.forEach((cell, colIndex) => {
        if (!isCanvasCell(cell)) {
          errors.push(`cells[${rowIndex}][${colIndex}] должен быть 0 или 1.`);
        }
      });
    });
  }

  if (errors.length > 0) {
    return { errors };
  }

  return {
    canvas: {
      width: data.width as number,
      height: data.height as number,
      cells: data.cells as CanvasCell[][],
    },
    errors,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isPositiveInteger(value: unknown): value is number {
  return Number.isInteger(value) && Number(value) > 0;
}

function isCanvasCell(value: unknown): value is CanvasCell {
  return value === 0 || value === 1;
}
