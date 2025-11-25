import { Component } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';

@Component({
  selector: 'app-delete-confirm-modal',
  imports: [ButtonModule, ReactiveFormsModule, FormsModule, InputTextModule, FormsModule],
  standalone: true,
  templateUrl: './delete-confirm-modal.component.html',
  styleUrl: './delete-confirm-modal.component.scss',
})
export class DeleteConfirmModalComponent {
  toConfirm: string = '';
  confirmInput = new FormControl('');

  constructor(
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
  ) {
    this.toConfirm = this.config.data;
  }

  close() {
    const value = this.confirmInput.value;
    if (!value || this.toConfirm != this.confirmInput.value) return;
    this.ref.close(true);
  }
}
