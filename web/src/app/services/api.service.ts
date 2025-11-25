import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, distinctUntilChanged, map, of, shareReplay, tap } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { UtilsService } from './utils.service';
import { AuthParams } from '../types/OIDC';
import { APIResponse, Constant, Info, PendingDownloadKey, AnalyzerInfo, Identity, User } from '../types/API';
import { Router } from '@angular/router';
import { CaseMetadata, CaseSampleMetadata, SampleAnalysis } from '../types/case';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private utils = inject(UtilsService);
  private http = inject(HttpClient);
  private router = inject(Router);
  public apiBaseUrl: string = '/api';

  private _userSubject$ = new BehaviorSubject<string>('');
  readonly user$ = this._userSubject$.asObservable();

  private infoCache: Info | undefined;
  private constantCache: Constant | undefined;

  login(data: Object): Observable<APIResponse<User>> {
    return this.http.post<APIResponse<User>>(`${this.apiBaseUrl}/auth/login`, { data }).pipe(
      tap((resp) => {
        if (resp.data) this._userSubject$.next(resp.data.username);
      }),
    );
  }

  unauthorizedRedirectLogin(): void {
    this.router.navigate(['/login']);
  }

  logout(): Observable<APIResponse<null>> {
    return this.http.get<APIResponse<null>>(`${this.apiBaseUrl}/auth/logout`).pipe(
      tap(() => {
        this._userSubject$.next('');
        this.utils.toast('success', 'Logged out', 'Logged out successfully');
        this.router.navigate(['/login']);
      }),
    );
  }

  getAuthParams(): Observable<APIResponse<AuthParams>> {
    return this.http.get<APIResponse<AuthParams>>(`${this.apiBaseUrl}/auth/config`);
  }

  getInfo(): Observable<Info> {
    if (this.infoCache) return of(this.infoCache);
    return this.http.get<APIResponse<Info>>(`${this.apiBaseUrl}/info`).pipe(
      tap((resp) => (this.infoCache = resp.data)),
      map((resp) => resp.data),
    );
  }

  getConstant(): Observable<Constant> {
    if (this.constantCache) return of(this.constantCache);
    return this.http.get<APIResponse<Constant>>(`${this.apiBaseUrl}/constant`).pipe(
      tap((resp) => {
        this.constantCache = resp.data;
        if (resp.data.banner && this.utils.banner !== resp.data.banner) {
          this.utils.banner = resp.data.banner;
        }
      }),
      map((resp) => resp.data),
    );
  }

  isLogged(): Observable<boolean> {
    if (this._userSubject$.value) return of(true);
    return this.http.get<APIResponse<{ username: string }>>(`${this.apiBaseUrl}/auth/is_logged`).pipe(
      tap((resp) => {
        if (resp.data?.username) this._userSubject$.next(resp.data.username);
      }),
      map(() => true),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getIdentities(): Observable<Identity> {
    return this.http.get<APIResponse<User[]>>(`${this.apiBaseUrl}/auth/identities`).pipe(
      map((resp) => {
        const users = resp.data.map((u) => u.username);
        const groups = Array.from(new Set(resp.data.flatMap((u) => u.groups)));
        return { users, groups };
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCase(caseGuid: string): Observable<CaseMetadata> {
    return this.http.get<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}`).pipe(
      map((resp) => resp.data),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  getCases(): Observable<CaseMetadata[]> {
    return this.http.get<APIResponse<CaseMetadata[]>>(`${this.apiBaseUrl}/cases`).pipe(
      map((resp) => {
        const previous = this.utils.getStoredCaseGuids();
        return resp.data.map((c: CaseMetadata) => ({
          ...c,
          unseenNew: previous.includes(c.guid) ? false : true,
        }));
      }),
      tap((resp) => {
        this.utils.refreshStoredCases(resp);
      }),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  postCase(caseData: CaseMetadata): Observable<CaseMetadata> {
    return this.http.post<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case`, caseData).pipe(
      tap((resp) => this.utils.addCaseGuidToStorage(resp.data.guid)),
      map((resp) => resp.data),
    );
  }

  putCase(caseGuid: string, caseData: Partial<CaseMetadata>): Observable<CaseMetadata> {
    return this.http
      .put<APIResponse<CaseMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}`, caseData)
      .pipe(map((resp) => resp.data));
  }

  getCaseSamples(caseGuid: string): Observable<CaseSampleMetadata[]> {
    return this.http.get<APIResponse<CaseSampleMetadata[]>>(`${this.apiBaseUrl}/case/${caseGuid}/samples`).pipe(
      map((resp) => resp.data || []),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  downloadSample(caseGuid: string, sampleGuid: string): Observable<void> {
    return this.http
      .get<APIResponse<PendingDownloadKey>>(`${this.apiBaseUrl}/case/${caseGuid}/sample/${sampleGuid}/download`)
      .pipe(
        map((resp) => {
          window.open(`${this.apiBaseUrl}/download/${resp.data.guid}/${resp.data.token}`, '_blank');
        }),
      );
  }

  getSamples(): Observable<CaseSampleMetadata[]> {
    return this.http.get<APIResponse<CaseSampleMetadata[]>>(`${this.apiBaseUrl}/samples`).pipe(
      map((resp) => resp.data || []),
      distinctUntilChanged(),
      shareReplay({ bufferSize: 1, refCount: true }),
    );
  }

  postCaseSample(caseSample: FormData, caseGuid: string): Observable<any> {
    return this.http.post<APIResponse<CaseSampleMetadata[]>>(`${this.apiBaseUrl}/case/${caseGuid}/sample`, caseSample, {
      reportProgress: true,
      observe: 'events',
    });
  }

  deleteSample(caseGuid: string, sampleGuid: string): Observable<any> {
    return this.http.delete<APIResponse<{}>>(`${this.apiBaseUrl}/case/${caseGuid}/sample/${sampleGuid}`);
  }

  putCaseSample(
    sample: Partial<CaseSampleMetadata>,
    caseGuid: string,
    sampleGuid: string,
  ): Observable<CaseSampleMetadata> {
    return this.http
      .put<APIResponse<CaseSampleMetadata>>(`${this.apiBaseUrl}/case/${caseGuid}/sample/${sampleGuid}`, sample)
      .pipe(map((resp) => resp.data));
  }

  getSampleAnalyses(caseGuid: string, sampleGuid: string): Observable<SampleAnalysis[]> {
    return this.http
      .get<APIResponse<SampleAnalysis[]>>(`${this.apiBaseUrl}/case/${caseGuid}/sample/${sampleGuid}/analyses`)
      .pipe(map((resp) => resp.data));
  }

  getSampleAnalysisLog(caseGuid: string, sampleGuid: string, analyzer: string): Observable<string> {
    return this.http.get<string>(`${this.apiBaseUrl}/case/${caseGuid}/sample/${sampleGuid}/analysis/${analyzer}/log`, {
      responseType: 'text' as 'json',
    });
  }

  downloadSampleAnalysis(caseGuid: string, sampleGuid: string, analyzerName: string): Observable<void> {
    return this.http
      .get<
        APIResponse<any>
      >(`${this.apiBaseUrl}/case/${caseGuid}/sample/${sampleGuid}/analysis/${analyzerName}/download`)
      .pipe(
        map((resp) => {
          window.open(`${this.apiBaseUrl}/download/${resp.data.guid}/${resp.data.token}`, '_blank');
        }),
      );
  }

  getAnalyzerInfos(): Observable<AnalyzerInfo[]> {
    return this.http
      .get<APIResponse<AnalyzerInfo[]>>(`${this.apiBaseUrl}/config/analyzers`)
      .pipe(map((resp) => resp.data));
  }

  hashLookup(hash: string): Observable<CaseMetadata[]> {
    this.http
      .get<APIResponse<CaseMetadata[]>>(`${this.apiBaseUrl}/search/digest/${hash}`)
      .pipe(map((resp) => resp.data));
  }
}
