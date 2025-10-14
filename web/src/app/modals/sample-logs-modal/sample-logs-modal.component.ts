import { Component } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'app-sample-logs-modal',
  imports: [ButtonModule],
  standalone: true,
  templateUrl: './sample-logs-modal.component.html',
  styleUrl: './sample-logs-modal.component.scss',
})
export class SampleLogsModalComponent {
  content: string = '';

  constructor(
    private ref: DynamicDialogRef,
    private utilsService: UtilsService,
    private config: DynamicDialogConfig,
  ) {
    this.content = this.config.data;
  }

  download() {
    this.utilsService.toFileDownload(this.content, 'output.log');
  }

  closeDialog() {
    this.ref.close();
  }
}
