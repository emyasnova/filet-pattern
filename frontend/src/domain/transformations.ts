import type { Pattern } from './pattern';
import {
  flipMatrixHorizontal,
  flipMatrixVertical,
  rotateMatrixClockwise,
} from './matrix';

export function rotatePatternClockwise(pattern: Pattern): Pattern {
  return {
    ...pattern,
    width: pattern.height,
    height: pattern.width,
    cells: rotateMatrixClockwise(pattern.cells),
  };
}

export function flipPatternHorizontal(pattern: Pattern): Pattern {
  return {
    ...pattern,
    cells: flipMatrixHorizontal(pattern.cells),
  };
}

export function flipPatternVertical(pattern: Pattern): Pattern {
  return {
    ...pattern,
    cells: flipMatrixVertical(pattern.cells),
  };
}
