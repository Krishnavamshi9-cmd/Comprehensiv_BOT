import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { PipelineRequest, JobStatus, HealthResponse } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  checkHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/`)
      .pipe(catchError(this.handleError));
  }

  startPipeline(request: PipelineRequest): Observable<JobStatus> {
    return this.http.post<JobStatus>(`${this.baseUrl}/api/pipeline/start`, request)
      .pipe(catchError(this.handleError));
  }

  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.baseUrl}/api/pipeline/status/${jobId}`)
      .pipe(catchError(this.handleError));
  }

  downloadResult(jobId: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/api/pipeline/download/${jobId}`, {
      responseType: 'blob'
    }).pipe(catchError(this.handleError));
  }

  listJobs(): Observable<{jobs: JobStatus[]}> {
    return this.http.get<{jobs: JobStatus[]}>(`${this.baseUrl}/api/jobs`)
      .pipe(catchError(this.handleError));
  }

  deleteJob(jobId: string): Observable<{message: string}> {
    return this.http.delete<{message: string}>(`${this.baseUrl}/api/pipeline/${jobId}`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      if (error.error && error.error.detail) {
        errorMessage = error.error.detail;
      }
    }
    
    console.error('API Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
