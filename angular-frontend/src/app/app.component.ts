import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { Subscription, interval } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

import { ApiService } from './services/api.service';
import { ThemeService } from './services/theme.service';
import { JobStatus, PipelineRequest } from './models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HttpClientModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatExpansionModule,
    MatProgressBarModule,
    MatIconModule,
    MatCardModule
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  configForm: FormGroup;
  currentJob: JobStatus | null = null;
  isBackendHealthy = false;
  isSubmitting = false;
  private jobStatusSubscription?: Subscription;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    public themeService: ThemeService
  ) {
    this.configForm = this.createForm();
  }

  ngOnInit() {
    this.checkBackendHealth();
  }

  ngOnDestroy() {
    this.jobStatusSubscription?.unsubscribe();
  }

  private createForm(): FormGroup {
    return this.fb.group({
      url: ['', [Validators.required, Validators.pattern(/^https?:\/\/.+/)]],
      query: ['Extract Golden Questions and Expected Responses that users commonly ask about this product/service for comprehensive bot testing'],
      outputFilename: ['golden_qna.xlsx', Validators.required],
      
      // Analysis options
      analysisQuestions: [true],
      criticalThinking: [false],
      outputFormat: ['Excel (.xlsx)'],
      
      // Advanced options
      scrollPages: [5, [Validators.min(1), Validators.max(20)]],
      crawl: [false],
      allowExternal: [false],
      maxDepth: [1, [Validators.min(1), Validators.max(5)]],
      maxPages: [20, [Validators.min(1), Validators.max(200)]],
      
      // Retrieval & Validation
      k: [30, [Validators.min(5), Validators.max(200)]],
      validate: [false],
      debug: [false],
      
      // Test Cases
      withTestCases: [true],
      tcVariations: [20, [Validators.min(1), Validators.max(100)]],
      tcNegatives: [12, [Validators.min(1), Validators.max(100)]],
      tcLlm: [false]
    });
  }

  private checkBackendHealth() {
    this.apiService.checkHealth().subscribe({
      next: () => {
        this.isBackendHealthy = true;
      },
      error: () => {
        this.isBackendHealthy = false;
      }
    });
  }

  onSubmit() {
    if (this.configForm.valid && !this.isSubmitting) {
      this.isSubmitting = true;
      const formValue = this.configForm.value;
      
      const request: PipelineRequest = {
        url: formValue.url,
        query: formValue.query,
        output_filename: formValue.outputFilename,
        k: formValue.k,
        scroll_pages: formValue.scrollPages,
        output_format: 'excel',
        validate_content: formValue.validate || formValue.debug,
        crawl: formValue.crawl,
        max_depth: formValue.maxDepth,
        max_pages: formValue.maxPages,
        same_domain_only: !formValue.allowExternal,
        with_test_cases: formValue.withTestCases,
        test_cases_llm: formValue.tcLlm,
        tc_variations: formValue.tcVariations,
        tc_negatives: formValue.tcNegatives
      };

      this.apiService.startPipeline(request).subscribe({
        next: (job) => {
          this.currentJob = job;
          this.isSubmitting = false;
          this.startJobMonitoring(job.job_id);
        },
        error: (error) => {
          console.error('Failed to start pipeline:', error);
          this.isSubmitting = false;
        }
      });
    }
  }

  private startJobMonitoring(jobId: string) {
    this.jobStatusSubscription?.unsubscribe();
    
    this.jobStatusSubscription = interval(2000)
      .pipe(
        switchMap(() => this.apiService.getJobStatus(jobId)),
        takeWhile(job => job.status === 'pending' || job.status === 'running', true)
      )
      .subscribe({
        next: (job) => {
          this.currentJob = job;
        },
        error: (error) => {
          console.error('Failed to get job status:', error);
        }
      });
  }

  downloadResult() {
    if (this.currentJob?.job_id) {
      this.apiService.downloadResult(this.currentJob.job_id).subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = this.configForm.value.outputFilename;
          link.click();
          window.URL.revokeObjectURL(url);
        },
        error: (error) => {
          console.error('Failed to download result:', error);
        }
      });
    }
  }

  startNewAnalysis() {
    this.currentJob = null;
    this.jobStatusSubscription?.unsubscribe();
  }

  getStatusIcon(): string {
    if (!this.currentJob) return '';
    
    switch (this.currentJob.status) {
      case 'pending': return 'schedule';
      case 'running': return 'sync';
      case 'completed': return 'check_circle';
      case 'failed': return 'error';
      default: return '';
    }
  }

  getStatusClass(): string {
    if (!this.currentJob) return '';
    return `status-${this.currentJob.status}`;
  }
}
