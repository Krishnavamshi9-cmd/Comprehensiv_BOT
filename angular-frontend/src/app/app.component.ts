import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ApiService } from './services/api.service';
import { JobStatus, PipelineRequest } from './models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  url = '';
  query = 'Extract Golden Questions and Expected Responses that users commonly ask about this product/service for comprehensive bot testing';
  outputFilename = 'golden_qna.xlsx';
  currentJob: JobStatus | null = null;
  isSubmitting = false;

  constructor(private apiService: ApiService) {}

  onSubmit() {
    if (!this.url || this.isSubmitting) return;
    
    this.isSubmitting = true;
    const request: PipelineRequest = {
      url: this.url,
      query: this.query,
      output_filename: this.outputFilename
    };

    this.apiService.startPipeline(request).subscribe({
      next: (job) => {
        this.currentJob = job;
        this.isSubmitting = false;
        this.checkJobStatus(job.job_id);
      },
      error: () => {
        this.isSubmitting = false;
        alert('Failed to start pipeline');
      }
    });
  }

  checkJobStatus(jobId: string) {
    const interval = setInterval(() => {
      this.apiService.getJobStatus(jobId).subscribe({
        next: (job) => {
          this.currentJob = job;
          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval);
          }
        }
      });
    }, 2000);
  }

  downloadResult() {
    if (!this.currentJob?.job_id) return;
    
    this.apiService.downloadResult(this.currentJob.job_id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = this.outputFilename;
        link.click();
        window.URL.revokeObjectURL(url);
      }
    });
  }

  startNew() {
    this.currentJob = null;
  }
}
