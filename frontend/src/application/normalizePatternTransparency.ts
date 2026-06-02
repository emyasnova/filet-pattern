import type { PatternCell } from '../domain/cell';

export function normalizePatternTransparency(cells: PatternCell[][]): PatternCell[][] {
  const height = cells.length;
  const width = cells[0]?.length ?? 0;

  if (height === 0 || width === 0) {
    return cells.map((row) => [...row]);
  }

  const nextCells = cells.map((row) => [...row]);
  const visited = Array.from({ length: height }, () =>
    Array.from({ length: width }, () => false),
  );
  const queue: Array<[number, number]> = [];

  const push = (row: number, col: number) => {
    if (
      row < 0 ||
      row >= height ||
      col < 0 ||
      col >= width ||
      visited[row][col]
    ) {
      return;
    }

    const value = nextCells[row][col];

    if (value !== 0 && value !== null) {
      return;
    }

    visited[row][col] = true;
    queue.push([row, col]);
  };

  for (let col = 0; col < width; col += 1) {
    push(0, col);
    push(height - 1, col);
  }

  for (let row = 0; row < height; row += 1) {
    push(row, 0);
    push(row, width - 1);
  }

  for (let index = 0; index < queue.length; index += 1) {
    const [row, col] = queue[index];
    nextCells[row][col] = null;

    push(row - 1, col);
    push(row + 1, col);
    push(row, col - 1);
    push(row, col + 1);
  }

  return nextCells;
}
