import { ChangeDetectionStrategy, Component } from '@angular/core';
import { FloatLabelModule } from 'primeng/floatlabel';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { FocusTrapModule } from 'primeng/focustrap';
import { MessageModule } from 'primeng/message';
import { SkeletonModule } from 'primeng/skeleton';
import { HttpErrorResponse } from '@angular/common/http';
import { APIResponse, Info } from '../../types/API';
import { UtilsService } from '../../services/utils.service';
import { AuthParams } from '../../types/OIDC';
import { ApiService } from '../../services/api.service';
import { AsyncPipe } from '@angular/common';
import { Observable, take } from 'rxjs';

@Component({
  selector: 'app-auth',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FloatLabelModule,
    ReactiveFormsModule,
    ButtonModule,
    FormsModule,
    InputTextModule,
    FocusTrapModule,
    SkeletonModule,
    MessageModule,
    AsyncPipe,
  ],
  templateUrl: './auth.component.html',
  styleUrl: './auth.component.scss',
})
export class AuthComponent {
  loginForm: FormGroup;
  info$: Observable<Info>;
  authenticationType = '';
  oidcUrl = '';
  errorMessage = '';

  constructor(
    private apiService: ApiService,
    private utilsService: UtilsService,
    private router: Router,
    private route: ActivatedRoute,
    private fb: FormBuilder,
  ) {
    this.info$ = this.apiService.getInfo();
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });

    this.route.queryParams.pipe(take(1)).subscribe((params) => {
      if (Object.keys(params).length) {
        if (params['code']) {
          this.login({ code: params['code'] });
        } else if (params['error']) {
          this.setErrorMessage(params['error'], params['error_description']);
        } else {
          this.setErrorMessage('Malformed url');
        }
      } else {
        this.apiService
          .getAuthParams()
          .pipe(take(1))
          .subscribe({
            next: (authParams: APIResponse<AuthParams>) => {
              this.authenticationType = authParams.data?.type || '__error__';

              if (this.authenticationType == 'keycloak') {
                const params = authParams.data.parameters;
                if (params) {
                  const host = params.host.startsWith('http')
                    ? params.host.replace(/\/$/, '')
                    : `https://${params.host.replace(/\/$/, '')}`;
                  this.oidcUrl = `${host}${params.include_auth ? '/auth' : ''}/realms/${
                    params.realm
                  }/protocol/openid-connect/auth?response_type=code&client_id=${
                    params.client
                  }&scope=openid%20profile%20email&state=${Math.random().toString().split('.')[1]}&redirect_uri=${
                    params.redirect_uri
                  }`;
                } else {
                  this.setErrorMessage('Error retrieving Keycloak parameters, verify the server configuration');
                }
              }
            },
          });
      }
    });
  }

  private setErrorMessage(error: string, description?: string): void {
    this.errorMessage = description ? `Error: ${description} (${error})` : `Error: ${error}`;
    this.utilsService.toast('error', 'Authentication failed', this.errorMessage, 4000);
  }

  authenticate(): void {
    if (this.authenticationType === 'keycloak') window.location.href = this.oidcUrl;
    else if (this.authenticationType === 'basic' && this.loginForm.valid) this.login(this.loginForm.value);
  }

  login(data: Object): void {
    this.errorMessage = '';
    this.apiService
      .login(data)
      .pipe(take(1))
      .subscribe({
        next: () => this.router.navigateByUrl('/home'),
        error: (err: HttpErrorResponse) => (this.errorMessage = err.error.message || 'Authentication failed'),
      });
  }
}
