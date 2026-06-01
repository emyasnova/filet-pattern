export function cloneMatrix<T>(matrix: T[][]): T[][] {
  return matrix.map((row) => [...row]);
}

export function createMatrix<T>(
  width: number,
  height: number,
  createCell: () => T,
): T[][] {
  return Array.from({ length: height }, () =>
    Array.from({ length: width }, createCell),
  );
}

export function rotateMatrixClockwise<T>(matrix: T[][]): T[][] {
  if (matrix.length === 0) {
    return [];
  }

  const height = matrix.length;
  const width = matrix[0]?.length ?? 0;

  return Array.from({ length: width }, (_, rowIndex) =>
    Array.from(
      { length: height },
      (_, colIndex) => matrix[height - 1 - colIndex][rowIndex],
    ),
  );
}

export function flipMatrixHorizontal<T>(matrix: T[][]): T[][] {
  return matrix.map((row) => [...row].reverse());
}

export function flipMatrixVertical<T>(matrix: T[][]): T[][] {
  return [...matrix].reverse().map((row) => [...row]);
}
