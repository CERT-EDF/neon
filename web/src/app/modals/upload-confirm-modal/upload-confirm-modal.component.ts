import { Component } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { ApiService } from '../../services/api.service';
import { FileSizePipe } from '../../shared/filesize.pipe';
import { Constant } from '../../types/API';
import { FocusTrapModule } from 'primeng/focustrap';
import { take } from 'rxjs';

@Component({
  selector: 'app-upload-confirm-modal',
  standalone: true,
  imports: [FloatLabelModule, InputTextModule, FileSizePipe, ButtonModule, FocusTrapModule, ReactiveFormsModule],
  templateUrl: './upload-confirm-modal.component.html',
  styleUrls: ['./upload-confirm-modal.component.scss'],
})
export class UploadConfirmModal {
  secretInput = new FormControl<string>('');
  constant?: Constant;
  file?: File;

  constructor(
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
    private apiService: ApiService,
  ) {
    this.file = this.config.data?.file;

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (data) => {
          this.constant = data;

          const filename = this.file?.name;
          if (!filename) return;

          const matchedSecret = data.globs.find((secPattern) => {
            const regex = new RegExp(secPattern.glob);
            return regex.test(filename);
          })?.secret;
          this.secretInput.setValue(matchedSecret || 'infected');
        },
      });
  }

  closeDialog() {
    let ret = this.secretInput.value;
    this.ref.close(ret);
  }
}
