import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'fileSize', standalone: true })
export class FileSizePipe implements PipeTransform {
  transform(bytes: number | null | undefined): string {
    if (bytes == null || isNaN(bytes) || bytes === 0) return '0 B';

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const factor = 1024;

    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(factor)), units.length - 1);
    const size = bytes / Math.pow(factor, index);
    return `${size.toFixed(2)} ${units[index]}`;
  }
}
