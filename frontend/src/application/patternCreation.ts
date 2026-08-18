export function getPatternNameFromFile(fileName: string): string {
  return fileName.replace(/\.[^.]+$/, '');
}
