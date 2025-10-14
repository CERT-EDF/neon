import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DynamicDialogConfig, DynamicDialogRef } from 'primeng/dynamicdialog';
import { FloatLabelModule } from 'primeng/floatlabel';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { FocusTrapModule } from 'primeng/focustrap';
import { Identity } from '../../types/API';
import { ApiService } from '../../services/api.service';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectItemGroup } from 'primeng/api';
import { take } from 'rxjs';

@Component({
  selector: 'app-case-create-modal',
  imports: [
    FloatLabelModule,
    InputTextModule,
    ButtonModule,
    SelectModule,
    ReactiveFormsModule,
    TextareaModule,
    FocusTrapModule,
    MultiSelectModule,
  ],
  standalone: true,
  templateUrl: './case-create-modal.component.html',
  styleUrl: './case-create-modal.component.scss',
})
export class CaseCreateModalComponent {
  caseForm: FormGroup;
  acsGroups: SelectItemGroup[] = [];
  isManaged: boolean = false;
  allowEmptyAcs: boolean = true;

  constructor(
    private ref: DynamicDialogRef,
    private config: DynamicDialogConfig,
    private apiService: ApiService,
    private fb: FormBuilder,
  ) {
    this.caseForm = this.fb.group({
      guid: '',
      tsid: '',
      name: ['', Validators.required],
      description: '',
      acs: [[], Validators.required],
    });

    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => {
          if (constant.allow_empty_acs) {
            this.caseForm.get('acs')?.removeValidators(Validators.required);
            this.caseForm.get('acs')?.updateValueAndValidity();
          }
        },
      });

    this.apiService
      .getIdentities()
      .pipe(take(1))
      .subscribe({
        next: (identities: Identity) => {
          this.acsGroups = [
            {
              label: 'Users',
              items: identities.users.map((u) => ({ label: u, value: u })).sort((a, b) => (a.label > b.label ? 1 : -1)),
            },
            {
              label: 'Groups',
              items: identities.groups
                .map((g) => ({ label: g, value: g }))
                .sort((a, b) => (a.label > b.label ? 1 : -1)),
            },
          ];

          if (this.config.data) {
            this.caseForm.patchValue(this.config.data);
            this.isManaged = this.config.data.managed;
            if (this.isManaged) this.disableCaseForm();
          }
        },
      });
  }

  enableCaseForm() {
    this.caseForm.enable();
  }

  disableCaseForm() {
    this.caseForm.disable();
  }

  closeDialog() {
    let ret = this.caseForm.value;
    this.ref.close(ret);
  }
}
