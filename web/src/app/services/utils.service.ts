import { inject, Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { version } from '../../../public/version';
import { CaseMetadata } from '../types/case';

const DARK = 'NEON_DARK';
const BANNER = 'NEON_BANNER';
const CASES = 'NEON_CASES';

@Injectable({
  providedIn: 'root',
})
export class UtilsService {
  messageService = inject(MessageService);
  private router = inject(Router);
  private bannerText: string = '';
  readonly frontendVersion: string = version;
  isDarkMode = false;

  calculateSimpleChecksum(input: string): number {
    let checksum = 0;
    for (let i = 0; i < input.length; i++) {
      checksum ^= input.charCodeAt(i);
    }
    return checksum;
  }

  get banner(): string {
    const storedChecksum = +(localStorage.getItem(BANNER) || '0');
    if (this.calculateSimpleChecksum(this.bannerText) === storedChecksum) return '';
    return this.bannerText;
  }

  set banner(str: string) {
    this.bannerText = str;
  }

  ackBanner(bannerText: string): void {
    localStorage.setItem(BANNER, this.calculateSimpleChecksum(bannerText).toString());
  }

  toast(severity = 'info', summary = 'Info', detail = '', life = 3000): void {
    this.messageService.add({
      severity,
      summary,
      detail,
      life,
      sticky: life == -1,
    });
  }

  navigateHomeWithError(msg = ''): void {
    if (msg) this.toast('error', 'Unauthorized', msg);
    this.router.navigate(['/home']);
  }

  toFileDownload(content: string, name: string, ext: string = 'md') {
    const blob = new Blob([content], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `neon_${name}.${ext}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  isDarkModeEnabled(): boolean {
    return !!localStorage.getItem(DARK);
  }

  toggleDarkMode(): void {
    this.isDarkMode = !this.isDarkMode;
    if (this.isDarkMode) localStorage.removeItem(DARK);
    else localStorage.setItem(DARK, '1');
    const element = document.documentElement;
    element.classList.toggle('dark');
  }

  getStoredCaseGuids(): string[] {
    return JSON.parse(localStorage.getItem(CASES) || '[]');
  }

  refreshStoredCases(cases: CaseMetadata[]): void {
    try {
      const guids = cases.map((c) => c.guid);
      localStorage.setItem(CASES, JSON.stringify(guids));
    } catch {
      this.toast('error', 'Error', 'localStorage was not initialized. Error.');
    }
  }

  addCaseGuidToStorage(guid: string): void {
    const storedGuids = this.getStoredCaseGuids();
    if (!storedGuids.includes(guid)) {
      storedGuids.push(guid);
      localStorage.setItem(CASES, JSON.stringify(storedGuids));
    }
  }
}
