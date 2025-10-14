import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'hex', standalone: true })
export class HexPipe implements PipeTransform {
  transform(value: any): string {
    const numberValue = Number(value);
    if (isNaN(numberValue)) return '';
    return '0x' + numberValue.toString(16).toUpperCase().padStart(2, '0');
  }
}
