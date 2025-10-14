import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs';
import { ApiService } from './api.service';

export const AuthGuard: CanActivateFn = (_, state) => {
  return inject(ApiService)
    .isLogged()
    .pipe(
      map((authenticated) => {
        if (!authenticated) return inject(Router).parseUrl('/login');
        return true;
      }),
    );
};
