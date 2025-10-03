import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PipelineRequest, JobStatus } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  startPipeline(request: PipelineRequest): Observable<JobStatus> {
    return this.http.post<JobStatus>(`${this.baseUrl}/api/pipeline/start`, request);
  }

  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.baseUrl}/api/pipeline/status/${jobId}`);
  }

  downloadResult(jobId: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/api/pipeline/download/${jobId}`, {
      responseType: 'blob'
    });
  }
}
