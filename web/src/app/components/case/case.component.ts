import { ChangeDetectorRef, Component, ElementRef, HostListener, OnDestroy, ViewChild } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { SkeletonModule } from 'primeng/skeleton';
import { ApiService } from '../../services/api.service';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { FileSizePipe } from '../../shared/filesize.pipe';
import { DialogService } from 'primeng/dynamicdialog';
import { Menu, MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { TooltipModule } from 'primeng/tooltip';
import { AnalyzerInfo } from '../../types/API';
import { CaseMetadata, CaseSampleMetadata, FusionEvent, SampleAnalysis } from '../../types/case';
import { UtilsService } from '../../services/utils.service';
import { HttpErrorResponse, HttpEvent, HttpEventType } from '@angular/common/http';
import { DatePipe, KeyValuePipe } from '@angular/common';
import { UploadConfirmModal } from '../../modals/upload-confirm-modal/upload-confirm-modal.component';
import { TabsModule } from 'primeng/tabs';
import { MarkdownModule } from 'ngx-markdown';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { CdkAccordionModule } from '@angular/cdk/accordion';
import { AutoCompleteCompleteEvent, AutoCompleteModule } from 'primeng/autocomplete';
import { ChipModule } from 'primeng/chip';
import { HexPipe } from '../../shared/hex.pipe';
import { CardModule } from 'primeng/card';
import { SampleLogsModalComponent } from '../../modals/sample-logs-modal/sample-logs-modal.component';
import { Subscription, take } from 'rxjs';
import { CaseCreateModalComponent } from '../../modals/case-create-modal/case-create-modal.component';
import { DeleteConfirmModalComponent } from '../../modals/delete-confirm-modal/delete-confirm-modal.component';

@Component({
  selector: 'app-case',
  standalone: true,
  imports: [
    RouterLink,
    FloatLabelModule,
    AutoCompleteModule,
    InputTextModule,
    ButtonModule,
    CdkAccordionModule,
    SelectModule,
    FormsModule,
    ReactiveFormsModule,
    TabsModule,
    ClipboardModule,
    SkeletonModule,
    TextareaModule,
    KeyValuePipe,
    SkeletonModule,
    FileSizePipe,
    MenuModule,
    DatePipe,
    ButtonModule,
    MarkdownModule,
    ChipModule,
    CardModule,
    HexPipe,
    TooltipModule,
  ],
  templateUrl: './case.component.html',
  styleUrl: './case.component.scss',
  providers: [FileSizePipe],
})
export class CaseComponent implements OnDestroy {
  @ViewChild('caseMenu') caseMenu!: Menu;

  @HostListener('document:dragenter', ['$event'])
  onDragEnter(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
    this.dragTarget = event.target;
  }

  @HostListener('document:dragleave', ['$event'])
  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (event.target === this.dragTarget || event.target === document) {
      this.isDragging = false;
    }
  }

  @HostListener('document:dragover', ['$event'])
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }

  @HostListener('document:drop', ['$event'])
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    if (event.dataTransfer?.files) {
      this.openUploadConfirmModal(event.dataTransfer?.files[0]);
    }
  }

  @ViewChild('actionsMenu')
  actionsMenu!: Menu;
  @ViewChild('sampleTabContent')
  sampleTabContentRef?: ElementRef;
  @ViewChild('tagInput')
  tagInput!: ElementRef<HTMLInputElement>;

  selectedSampleTabID = '';
  isDragging = false;
  dragTarget: EventTarget | null = null;

  caseMeta?: CaseMetadata;
  caseSamples: CaseSampleMetadata[] = [];
  displayedSamples: CaseSampleMetadata[] = [];
  uploadProgress: string | null = null;

  tagsInput = new FormControl('');
  tags: string[] = [];
  sampleAvailableTags: string[] = [];
  sampleFilteredTags: string[] = [];
  sampleAvailableIndicatorNature: string[] = [];

  eventSource!: Subscription;
  activeUsers: string[] = [];

  caseForm: FormGroup;
  sampleForm: FormGroup;
  baseSampleForm: FormGroup;

  analyzerInfos: AnalyzerInfo[] = [];
  analyses: {
    [guid: string]: {
      [analyzerName: string]: SampleAnalysis;
    };
  } = {};

  actionsMenuItems: MenuItem[] = [];
  menuSampleSelected = '';
  menuSampleItems: MenuItem[] = [
    {
      label: 'Download',
      icon: 'pi pi-download',
      command: () => this.downloadSample(this.menuSampleSelected),
    },
    {
      label: 'Report',
      icon: 'pi pi-file-export',
      command: () => this.generateSampleReport(this.menuSampleSelected),
    },
  ];

  caseMenuItems: MenuItem[] = [];
  private _isEditModeCase = false;
  get editModeCase(): boolean {
    return this._isEditModeCase;
  }

  set editModeCase(value: boolean) {
    if (value && this.caseMeta) this.caseForm.patchValue(this.caseMeta);
    this._isEditModeCase = value;
  }

  private _editedSampleID: string | null = null;
  get editedSampleID() {
    return this._editedSampleID;
  }
  set editedSampleID(guid: string | null) {
    this._editedSampleID = guid;
    this.resetSampleForm();
    if (!guid) return;
    const sample = this.caseSamples.find((s) => s.guid === guid)!;
    this.sampleForm.patchValue(sample);

    sample.indicators.forEach((indicator) => this.addIndicator(indicator.nature, indicator.value));

    const rulesets = this.sampleForm.get('rulesets') as FormGroup;
    Object.entries(sample.rulesets!).forEach(([ruleName, ruleValue]) =>
      rulesets.addControl(ruleName, new FormControl(ruleValue)),
    );

    setTimeout(() => {
      this.sampleTabContentRef?.nativeElement.scrollIntoView({
        block: 'start',
        behavior: 'smooth',
      });
    }, 10);

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe((constant) => {
        this.sampleAvailableTags = constant.tags.slice().sort();
        this.sampleFilteredTags = this.sampleAvailableTags;
        this.sampleAvailableIndicatorNature = constant.enums.indicator_nature.slice().sort();
      });

    this.tags = sample.tags ?? [];
  }

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
    private filesizePipe: FileSizePipe,
    private utilsService: UtilsService,
    private dialogService: DialogService,
  ) {
    this.sampleForm = this.fb.group({
      description: '',
      report: '',
      symbols: {},
      indicators: this.fb.array([]),
      rulesets: this.fb.group({}),
      opsystem: '',
    });
    this.baseSampleForm = this.sampleForm.value;

    this.caseForm = this.fb.group({
      tsid: '',
      name: ['', Validators.required],
      description: '',
      report: '',
    });

    this.apiService
      .getCase(this.route.snapshot.paramMap.get('id')!)
      .pipe(take(1))
      .subscribe({
        next: (data) => {
          this.caseMeta = data;

          this.eventSource = this.apiService.getCaseEventsSSE(this.caseMeta!.guid).subscribe({
            next: (event) => this.handleSSEEvent(event),
            error: (error) => console.error('SSE error:', error),
          });

          this.apiService
            .getCaseSamples(this.caseMeta.guid)
            .pipe(take(1))
            .subscribe({
              next: (samples) => {
                this.caseSamples = samples;
                this.sortSamples();
              },
              error: () => this.utilsService.navigateHomeWithError('Error while retrieving Case samples'),
            });
        },
      });

    this.apiService
      .getAnalyzerInfos()
      .pipe(take(1))
      .subscribe({
        next: (infos) => (this.analyzerInfos = infos),
      });
  }

  ngOnDestroy(): void {
    if (this.eventSource) this.eventSource.unsubscribe();
  }

  handleSSEEvent(messageEvent: MessageEvent): void {
    if (!messageEvent.data) return;
    const event: FusionEvent = JSON.parse(messageEvent.data);
    const ext = event.ext;
    switch (event.category) {
      case 'subscribers':
        this.activeUsers = ext.usernames;
        break;
      case 'subscribe':
        if (!this.activeUsers.includes(ext.username)) this.activeUsers.push(ext.username);
        break;
      case 'unsubscribe':
        this.activeUsers = this.activeUsers.filter((u) => u !== ext.username);
        break;
      case 'create_sample':
        this.caseSamples = [...this.caseSamples, ext];
        this.sortSamples();
        break;
      case 'create_samples':
        this.caseSamples = [...this.caseSamples, ...ext];
        this.sortSamples();
        break;
      case 'update_sample':
        const sampleIndex = this.caseSamples.findIndex((s) => s.guid === ext.guid);
        if (sampleIndex > -1) {
          this.caseSamples = [
            ...this.caseSamples.slice(0, sampleIndex),
            ext,
            ...this.caseSamples.slice(sampleIndex + 1),
          ];
        }

        const displayedIndex = this.displayedSamples.findIndex((s) => s.guid === ext.guid);
        if (displayedIndex > -1) {
          this.displayedSamples = [
            ...this.displayedSamples.slice(0, displayedIndex),
            ext,
            ...this.displayedSamples.slice(displayedIndex + 1),
          ];
        }
        this.sortSamples();
        break;
      case 'delete_sample':
        this.caseSamples = this.caseSamples.filter((s) => s.guid != ext.guid);
        if (this.displayedSamples.findIndex((s) => s.guid == ext.guid) > -1) {
          this.displayedSamples = this.displayedSamples.filter((s) => s.guid != ext.guid);
          this.selectedSampleTabID = '';
          setTimeout(() => (this.selectedSampleTabID = this.displayedSamples[0]?.guid || ''), 10);
        }
        break;
      case 'update_case':
        this.caseMeta = event.case;
        break;
      case 'delete_case':
        this.utilsService.toast('info', 'Case deleted', 'This case was deleted');
        this.utilsService.navigateHomeWithError();
        break;
      default: {
        if (!event.category.startsWith('analysis_')) break;
        const sample = ext.sample;
        const analysis = ext.analysis;
        const status = event.category.split('analysis_')[1];
        if (this.analyses.hasOwnProperty(sample.guid))
          this.analyses[sample.guid][analysis.analyzer] = { ...analysis, status };
      }
    }
    this.cdr.markForCheck();
  }

  resetSampleForm(): void {
    const indicators = this.sampleForm.get('indicators') as FormArray;
    while (indicators.length) {
      indicators.removeAt(0);
    }

    const rulesets = this.sampleForm.get('rulesets') as FormGroup;
    Object.keys(rulesets.controls).forEach((controlName) => rulesets.removeControl(controlName));

    this.sampleForm.reset(this.baseSampleForm);
    this.tags = [];
  }

  sortSamples(): void {
    this.caseSamples = [...this.caseSamples].sort(
      (a, b) => new Date(b.created).getTime() - new Date(a.created).getTime(),
    );
  }

  searchTags(event: AutoCompleteCompleteEvent): void {
    const availableNotSelected = this.sampleAvailableTags.filter((tag) => !this.tags.includes(tag));
    this.sampleFilteredTags = event.query
      ? availableNotSelected.filter((tag) => tag.toLowerCase().includes(event.query.toLowerCase()))
      : availableNotSelected;
  }

  objKeysCount(obj: object): number {
    return Object.keys(obj).length;
  }

  addTag(): void {
    const value = this.tagsInput.value?.trim();
    if (value && !this.tags.includes(value)) {
      this.tags = [...this.tags, value];
      this.tagsInput.setValue('');
    }
    this.sampleFilteredTags = this.sampleAvailableTags.filter((tag) => !this.tags.includes(tag));
  }

  removeTag(index: number): void {
    this.tags = this.tags.filter((_, idx) => idx !== index);
  }

  get rulesetsFormGroup(): FormGroup {
    return this.sampleForm.get('rulesets') as FormGroup;
  }

  get indicatorsFormArray(): FormArray {
    return this.sampleForm.get('indicators') as FormArray;
  }

  addIndicator(nature?: string, value?: string): void {
    this.indicatorsFormArray.push(
      this.fb.group({
        nature: [nature ?? null, Validators.required],
        value: [value ?? null, Validators.required],
      }),
    );
  }

  removeIndicator(index: number): void {
    this.indicatorsFormArray.removeAt(index);
  }

  closeDisplayedSample(index: number): void {
    this.displayedSamples = this.displayedSamples.filter((_, i) => i !== index);
    if (this.editedSampleID && this.displayedSamples.findIndex((s) => s.guid === this.editedSampleID) === -1) {
      this.editedSampleID = null;
    }
    if (this.displayedSamples.length > 0) {
      this.selectedSampleTabID = this.displayedSamples[this.displayedSamples.length - 1].guid;
    } else {
      this.selectedSampleTabID = '';
    }
  }

  openSample(guid: string): void {
    if (this.displayedSamples.findIndex((s) => s.guid === guid) === -1) {
      const sample = this.caseSamples.find((s) => s.guid === guid);
      if (sample) {
        this.displayedSamples = [...this.displayedSamples, sample];
        this.apiService
          .getSampleAnalyses(this.caseMeta!.guid, guid)
          .pipe(take(1))
          .subscribe((analyses) => {
            this.analyses[guid] = Object.fromEntries(analyses.map((a) => [a.analyzer, a]));
          });
      }
    }

    setTimeout(() => {
      this.sampleTabContentRef?.nativeElement.scrollIntoView({
        block: 'start',
        behavior: 'smooth',
      });
    }, 10);
    this.selectedSampleTabID = guid;
  }

  constructCaseMenu(ev: any) {
    if (!this.caseMeta) return;
    const closeOrReopenItem = this.caseMeta.closed
      ? {
          label: 'Reopen',
          icon: 'pi pi-lock-open',
          iconClass: 'text-green-500!',
          command: () =>
            this.apiService
              .putCase(this.caseMeta!.guid, { closed: '' })
              .pipe(take(1))
              .subscribe({
                next: (meta) => (this.caseMeta = meta),
              }),
        }
      : {
          label: 'Close',
          icon: 'pi pi-times',
          iconClass: 'text-red-500!',
          command: () =>
            this.apiService
              .putCase(this.caseMeta!.guid, { closed: new Date().toISOString() })
              .pipe(take(1))
              .subscribe({
                next: (meta) => (this.caseMeta = meta),
              }),
        };

    this.caseMenuItems = [
      {
        label: 'Generate Report',
        icon: 'pi pi-file-export',
        iconClass: 'text-blue-500!',
        command: () => this.generateReport(),
      },
      {
        label: 'Copy GUID',
        icon: 'pi pi-tag',
        command: () => {
          try {
            navigator.clipboard.writeText(this.caseMeta!.guid);
          } catch {
            console.error('Clipboard not available');
            this.utilsService.toast('error', 'Error', 'Clipboard not available');
          }
        },
      },
      {
        label: 'Edit',
        icon: 'pi pi-pencil',
        disabled: !!this.caseMeta.closed,
        command: () => this.openEditCaseModal(),
      },
      closeOrReopenItem,
      {
        label: 'Delete',
        icon: 'pi pi-trash',
        iconClass: 'text-red-500!',
        command: () => this.deleteCase(),
      },
    ];
    this.caseMenu.toggle(ev);
  }

  downloadSymbols(guid: string): void {
    const sample = this.caseSamples.find((s) => s.guid === guid);
    if (sample) {
      const content = JSON.stringify(sample.symbols);
      this.utilsService.toFileDownload(content, `${sample.name}_symbols`, 'json');
    }
  }

  updateSample(): void {
    const editedSample = this.caseSamples.find((s) => s.guid === this.editedSampleID);
    if (!editedSample) return;
    const data = this.sampleForm.value;
    data.tags = this.tags;
    this.apiService
      .putCaseSample(data, this.caseMeta!.guid, this.editedSampleID!)
      .pipe(take(1))
      .subscribe({
        next: () => {
          this.editedSampleID = null;
        },
      });
  }

  deleteSample(sample: CaseSampleMetadata) {
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      focusOnShow: false,
      dismissableMask: true,
      breakpoints: { '640px': '90vw' },
      data: sample.name,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService.deleteSample(this.caseMeta!.guid, sample.guid).pipe(take(1)).subscribe();
    });
  }

  downloadRuleset(guid: string): void {
    const sample = this.caseSamples.find((s) => s.guid === guid);
    if (sample) {
      const content = JSON.stringify(sample.rulesets);
      this.utilsService.toFileDownload(content, `${sample.name}_rules`, 'json');
    }
  }

  onSymbolsUpload(event: Event): void {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) this.symbolUpdate(file);
  }

  cancelSymbolsUpload(): void {
    const symbolsValue = this.caseSamples.find((s) => s.guid === this.editedSampleID)?.symbols ?? {};
    this.sampleForm.get('symbols')?.setValue(symbolsValue);
  }

  symbolUpdate(file: File): void {
    const reader = new FileReader();

    reader.onload = (event: ProgressEvent<FileReader>) => {
      try {
        this.sampleForm.get('symbols')?.setValue(JSON.parse(event.target!.result as string));
      } catch {
        this.utilsService.toast('error', 'Invalid file', 'File is not valid JSON');
      }
    };

    reader.readAsText(file);
  }

  onSampleUpload(event: Event): void {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) this.openUploadConfirmModal(file);
  }

  openUploadConfirmModal(file: File): void {
    if (!file) return;
    const modal = this.dialogService.open(UploadConfirmModal, {
      header: 'Upload Sample',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      data: {
        file,
      },
    });

    modal.onClose.pipe(take(1)).subscribe((secret: string | null) => {
      if (!secret) return;

      const formData = new FormData();
      formData.append('secret', secret);
      formData.append('file', file, file.name);

      this.apiService.postCaseSample(formData, this.caseMeta!.guid).subscribe({
        next: (event: HttpEvent<any>) => {
          switch (event.type) {
            case HttpEventType.UploadProgress:
              if (event.total) {
                const progress = Math.round((100 * event.loaded) / event.total);
                this.uploadProgress = `[${progress}%] ${file.name}`;
              }
              break;

            case HttpEventType.Response:
              this.utilsService.toast(
                'success',
                'Complete',
                `Sample${event.body.data.length > 1 ? 's' : ''} dissection complete`,
              );
              this.uploadProgress = null;
              break;
          }
        },
        error: (err: HttpErrorResponse) => {
          this.uploadProgress = null;
          console.error(err);
        },
      });
    });
  }

  refreshAnalyses(guid: string): void {
    const iconElement = document.getElementById('refreshAnalysesIcon');
    iconElement?.classList.add('spin-once');
    setTimeout(() => {
      iconElement?.classList.remove('spin-once');
    }, 1000);

    this.apiService
      .getSampleAnalyses(this.caseMeta!.guid, guid)
      .pipe(take(1))
      .subscribe((analyses) => {
        this.analyses[guid] = Object.fromEntries(analyses.map((analysis) => [analysis.analyzer, analysis]));
      });
  }

  openEditCaseModal(): void {
    const modal = this.dialogService.open(CaseCreateModalComponent, {
      header: 'Update Case',
      modal: true,
      appendTo: 'body',
      closable: true,
      dismissableMask: true,
      width: '30vw',
      data: this.caseMeta,
      breakpoints: {
        '960px': '90vw',
      },
    });

    modal.onClose.pipe(take(1)).subscribe((data: CaseMetadata | null) => {
      if (!data) return;
      this.putCase(data);
    });
  }

  putCase(data: Partial<CaseMetadata>): void {
    this.apiService.putCase(this.caseMeta!.guid, data).pipe(take(1)).subscribe();
  }

  deleteCase() {
    if (!this.caseMeta || !this.caseMeta.name) return;
    const modal = this.dialogService.open(DeleteConfirmModalComponent, {
      header: 'Confirm to delete',
      modal: true,
      closable: true,
      dismissableMask: true,
      breakpoints: {
        '640px': '90vw',
      },
      data: this.caseMeta?.name,
    });

    modal.onClose.pipe(take(1)).subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.apiService.deleteCase(this.caseMeta!.guid).pipe(take(1)).subscribe();
    });
  }

  switchEditReport(): void {
    this.editModeCase = !this.editModeCase;
    if (this.editModeCase) this.caseForm.patchValue(this.caseMeta!);
  }

  updateReport() {
    this.putCase({
      report: this.caseForm.get('report')?.value,
    });
    this.editModeCase = false;
  }

  _generateSampleReport(sample: CaseSampleMetadata, nested = false): string {
    let header_base_level = nested ? '###' : '#';

    let sample_filename = sample.name.split('/')[sample.name.split('/').length - 1];
    let report = `${header_base_level} ${sample_filename}\n`;
    report += `${sample.report || 'No data'}  `;
    report += '\n';

    report += `${header_base_level}# Indicators\n`;
    report += `| Nature | Value |\n`;
    report += `|---------|-------|\n`;
    sample.indicators.forEach((indicator) => {
      report += `| ${indicator.nature} | ${indicator.value} |\n`;
    });
    report += `\n`;

    report += `${header_base_level}# Symbols\n`;
    report += `| Address | Value |\n`;
    report += `|---------|-------|\n`;

    Object.entries(sample.symbols).forEach(([symbol, value]) => {
      report += `| ${symbol} | ${value} |\n`;
    });
    report += `\n`;

    report += `${header_base_level}# Rulesets\n`;
    Object.entries(sample.rulesets).forEach(([rule, value]) => {
      report += `**${rule}**\n`;
      report += '```\n';
      report += `${value || 'No data'}\n`;
      report += '```\n\n';
    });
    return report;
  }

  generateSampleReport(guid: string): void {
    if (!this.caseMeta) return;
    const sample = this.caseSamples.find((s) => s.guid === guid);
    if (!sample) return;
    this.utilsService.toFileDownload(this._generateSampleReport(sample), sample.guid);
  }

  generateReport(): void {
    if (!this.caseMeta) return;
    let report = `# ${this.caseMeta.name}\n${this.caseMeta.report || 'Case report is empty.'}\n\n`;
    report += `## Samples\n${this.caseSamples.length} vitrified, ${
      this.caseSamples.filter((s) => s.report).length
    } analyzed.\n\n`;
    report += `| Date | Filename | Size | Tags | Digests | Analyzed |\n`;
    report += `|------|----------|------|------|---------|----------|\n`;

    this.caseSamples.forEach((sample) => {
      report += `| ${sample.created.split('T')[0]} | ${sample.name} | ${this.filesizePipe.transform(sample.size)} | ${
        sample.tags || 'No data'
      } | ${Object.entries(sample.digests)
        .map(([digest, value]) => `${digest}: ${value}`)
        .join('<br>')} | ${sample.report ? 'Yes' : 'No'} |\n`;
    });
    report += '\n\n';

    this.caseSamples.forEach((sample) => {
      if (!sample.report) return;
      report += this._generateSampleReport(sample);
    });

    this.utilsService.toFileDownload(report, this.caseMeta.name);
  }

  downloadSample(guid: string): void {
    if (!guid) return;
    this.apiService
      .downloadSample(this.caseMeta!.guid, guid)
      .pipe(take(1))
      .subscribe({
        next: () => {},
        error: (err) => {
          console.error(err);
        },
      });
  }

  constructMenu(ev: Event, guid: string, analyzerName: string): void {
    const status = this.analyses[guid]?.[analyzerName]?.status;
    const items: MenuItem[] = [
      {
        label: 'Logs',
        icon: 'pi pi-paperclip',
        command: () => this.openSampleLogsModal(guid, analyzerName),
      },
    ];

    if (status === 'success') {
      items.push({
        label: 'Download',
        icon: 'pi pi-download',
        command: () => this.downloadSampleAnalysis(guid, analyzerName),
      });
    }

    this.actionsMenuItems = [
      {
        label: analyzerName,
        items,
      },
    ];
    this.actionsMenu.toggle(ev);
  }

  downloadSampleAnalysis(sampleGuid: string, analyzerName: string): void {
    this.apiService
      .downloadSampleAnalysis(this.caseMeta!.guid, sampleGuid, analyzerName)
      .pipe(take(1))
      .subscribe({
        error: (err) => console.error(err),
      });
  }

  openSampleLogsModal(sampleGuid: string, analyzerName: string): void {
    this.apiService
      .getSampleAnalysisLog(this.caseMeta!.guid, sampleGuid, analyzerName)
      .pipe(take(1))
      .subscribe((content) => {
        this.dialogService.open(SampleLogsModalComponent, {
          header: `${analyzerName} logs`,
          modal: true,
          appendTo: 'body',
          closable: true,
          dismissableMask: true,
          width: '45vw',
          breakpoints: { '960px': '90vw' },
          data: content,
        });
      });
  }
}
