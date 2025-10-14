import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToastModule } from 'primeng/toast';
import { UtilsService } from './services/utils.service';
import { ApiService } from './services/api.service';
import { ButtonModule } from 'primeng/button';
import { take } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ToastModule, ButtonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  banner: string = '';

  constructor(
    private utilsService: UtilsService,
    private apiService: ApiService,
  ) {
    this.apiService
      .getConstant()
      .pipe(take(1))
      .subscribe({
        next: (constant) => {
          this.utilsService.banner = constant.banner || '';
          this.banner = this.utilsService.banner;
        },
      });

    this.apiService
      .getInfo()
      .pipe(take(1))
      .subscribe({
        next: (resp) => {
          if (resp.version !== this.utilsService.frontendVersion)
            this.utilsService.toast(
              'error',
              'Version mismatch',
              'Frontend version is not the same as backend version, ensure both are up to date',
              -1,
            );
        },
      });

    if (this.utilsService.isDarkModeEnabled()) {
      this.utilsService.toggleDarkMode();
    }
  }

  ackBanner() {
    this.utilsService.ackBanner(this.banner);
    this.banner = '';
  }
}
