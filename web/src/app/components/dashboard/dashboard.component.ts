import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MenuModule } from 'primeng/menu';
import { ApiService } from '../../services/api.service';
import { DialogService } from 'primeng/dynamicdialog';
import { CaseCreateModalComponent } from '../../modals/case-create-modal/case-create-modal.component';
import { CaseMetadata } from '../../types/case';
import { MenuItem } from 'primeng/api';
import { SkeletonModule } from 'primeng/skeleton';
import { AsyncPipe, DatePipe } from '@angular/common';
import { UtilsService } from '../../services/utils.service';
import { DialogModule } from 'primeng/dialog';
import { Info } from '../../types/API';
import { debounceTime, Observable, take } from 'rxjs';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    RouterLink,
    CardModule,
    DatePipe,
    MenuModule,
    ReactiveFormsModule,
    InputTextModule,
    DialogModule,
    ButtonModule,
    AsyncPipe,
    SkeletonModule,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  menuItems: MenuItem[] = [
    {
      label: 'Dark Mode',
      icon: 'pi pi-moon',
      command: () => this.utilsService.toggleDarkMode(),
    },
    {
      label: 'About',
      icon: 'pi pi-info-circle',
      command: () => (this.isAboutDialogVisible = true),
    },
    {
      label: 'Logout',
      icon: 'pi pi-sign-out',
      command: () => this.logout(),
    },
  ];
  info$: Observable<Info>;
  isAboutDialogVisible: boolean = false;
  frontendVersion: string;
  cases: CaseMetadata[] = [];
  displayedCases: CaseMetadata[] = [];
  searchInput = new FormControl('');

  constructor(
    private apiService: ApiService,
    private utilsService: UtilsService,
    private dialogService: DialogService,
  ) {
    this.info$ = this.apiService.getInfo();
    this.frontendVersion = this.utilsService.frontendVersion;

    this.apiService
      .getCases()
      .pipe(take(1))
      .subscribe({
        next: (cases) => {
          this.cases = cases;
          this.updateDisplayedCases(this.cases);
        },
      });

    this.searchInput.valueChanges.pipe(debounceTime(250), takeUntilDestroyed()).subscribe({
      next: (value) => {
        this.updateDisplayedCases(this.cases, value || '');
      },
    });
  }

  openAddCaseModal() {
    const modal = this.dialogService.open(CaseCreateModalComponent, {
      header: 'Create Case',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      breakpoints: {
        '960px': '90vw',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((data: CaseMetadata | null) => {
      if (!data) return;
      this.apiService
        .postCase(data)
        .pipe(take(1))
        .subscribe({
          next: (c) => {
            this.cases = [...this.cases, c];
            this.updateDisplayedCases(this.cases);
          },
        });
    });
  }

  logout(): void {
    this.apiService.logout().pipe(take(1)).subscribe();
  }

  updateDisplayedCases(cases: CaseMetadata[], inputVal?: string): void {
    if (inputVal) {
    const sha256Regex = /^[a-fA-F0-9]{64}$/;    
    if (sha256Regex.test(inputVal)) {
      this.apiService.hashLookup(inputVal)
        .pipe(take(1))
        .subscribe(results => {
          this.displayedCases = results;
        });
    } else {
      this.displayedCases = cases.filter(
        (c: CaseMetadata) =>
          c.name.toLowerCase().includes(inputVal.toLowerCase()) ||
          c.description?.toLowerCase().includes(inputVal.toLowerCase()) ||
          c.tsid?.toString().includes(inputVal),
      );
    }
  } else {
    this.displayedCases = [...cases].sort((a, b) => {
      if (a.closed !== b.closed) return a.closed ? 1 : -1;
      return new Date(b.created!).getTime() - new Date(a.created!).getTime();
    });
  }
  }
}
