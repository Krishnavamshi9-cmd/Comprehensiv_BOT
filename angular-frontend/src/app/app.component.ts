import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ApiService } from './services/api.service';
import { JobStatus, PipelineRequest, AdvancedSettings } from './models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  url = '';
  query = '';
  outputFilename = '';
  currentJob: JobStatus | null = null;
  isSubmitting = false;
  isDarkMode = false;
  showAdvancedSettings = false;

  // Advanced Settings (Scraping-focused only)
  advancedSettings = {
    // Scraping Strategy
    scrapingStrategy: 'auto', // auto, playwright, stealth, requests
    enableStealth: true,
    forceHttp1: true,
    
    // Content Extraction
    minContentLength: 200,
    validateQuality: true,
    enableCrawling: false,
    maxCrawlDepth: 1,
    maxCrawlPages: 20,
    sameDomainOnly: true,
    
    // Timeouts & Performance
    timeoutMs: 60000,
    scrollPages: 5,
    humanDelayMin: 1000,
    humanDelayMax: 3000,
    
    // Browser Settings
    headless: true,
    viewport: { width: 1920, height: 1080 },
    userAgent: 'auto', // auto, chrome, firefox, safari
    
    // Content Filtering
    excludeNavigation: true,
    excludeAds: true,
    excludeSocial: true,
    excludeComments: true,
    
    // Output Settings
    includeMetadata: false,
    includeTimestamps: false,
    maxQuestions: 100,
    questionFormat: 'qa', // qa, faq, structured
    
    // Retry Settings
    maxRetries: 3,
    retryDelay: 2000,
    enableFallbacks: true
  };

  constructor(private apiService: ApiService) {}

  onSubmit() {
    if (!this.url || this.isSubmitting) return;
    
    this.isSubmitting = true;
    const request: PipelineRequest = {
      url: this.url,
      query: this.query || 'Extract comprehensive Q&A content for bot training',
      output_filename: this.outputFilename || 'golden_qna.xlsx',
      advanced_settings: this.showAdvancedSettings ? this.advancedSettings : undefined
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
        link.download = this.outputFilename || 'golden_qna.xlsx';
        link.click();
        window.URL.revokeObjectURL(url);
      }
    });
  }

  startNew() {
    this.currentJob = null;
  }

  toggleTheme() {
    this.isDarkMode = !this.isDarkMode;
    document.body.classList.toggle('dark', this.isDarkMode);
  }

  toggleAdvancedSettings() {
    this.showAdvancedSettings = !this.showAdvancedSettings;
  }

  resetAdvancedSettings() {
    this.advancedSettings = {
      scrapingStrategy: 'auto',
      enableStealth: true,
      forceHttp1: true,
      minContentLength: 200,
      validateQuality: true,
      enableCrawling: false,
      maxCrawlDepth: 1,
      maxCrawlPages: 20,
      sameDomainOnly: true,
      timeoutMs: 60000,
      scrollPages: 5,
      humanDelayMin: 1000,
      humanDelayMax: 3000,
      headless: true,
      viewport: { width: 1920, height: 1080 },
      userAgent: 'auto',
      excludeNavigation: true,
      excludeAds: true,
      excludeSocial: true,
      excludeComments: true,
      includeMetadata: false,
      includeTimestamps: false,
      maxQuestions: 100,
      questionFormat: 'qa',
      maxRetries: 3,
      retryDelay: 2000,
      enableFallbacks: true
    };
  }

  onAdvancedSettingChange() {
    // Validate interdependent settings
    if (!this.advancedSettings.enableCrawling) {
      this.advancedSettings.maxCrawlDepth = 1;
      this.advancedSettings.maxCrawlPages = 1;
    }
    
    if (this.advancedSettings.timeoutMs < 10000) {
      this.advancedSettings.timeoutMs = 10000;
    }
    
    if (this.advancedSettings.maxQuestions < 1) {
      this.advancedSettings.maxQuestions = 1;
    }
  }
}
