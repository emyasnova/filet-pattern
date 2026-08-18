"""Pure operations for editable pattern matrices."""

from collections import deque

PatternCell = int | None


def normalize_pattern_transparency(
    cells: list[list[PatternCell]],
) -> list[list[PatternCell]]:
    """Turn boundary-connected empty cells into transparent cells."""
    if not cells or not cells[0]:
        return [list(row) for row in cells]
    height = len(cells)
    width = len(cells[0])
    normalized = [[0 if cell is None else cell for cell in row] for row in cells]
    visited = [[False] * width for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    def enqueue(row: int, column: int) -> None:
        if not (0 <= row < height and 0 <= column < width):
            return
        if visited[row][column] or normalized[row][column] != 0:
            return
        visited[row][column] = True
        queue.append((row, column))

    for column in range(width):
        enqueue(0, column)
        enqueue(height - 1, column)
    for row in range(height):
        enqueue(row, 0)
        enqueue(row, width - 1)

    while queue:
        row, column = queue.popleft()
        normalized[row][column] = None
        enqueue(row - 1, column)
        enqueue(row + 1, column)
        enqueue(row, column - 1)
        enqueue(row, column + 1)
    return normalized
