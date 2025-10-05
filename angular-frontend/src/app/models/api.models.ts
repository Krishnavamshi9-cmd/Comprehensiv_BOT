export interface AdvancedSettings {
  scrapingStrategy: string;
  enableStealth: boolean;
  forceHttp1: boolean;
  minContentLength: number;
  validateQuality: boolean;
  enableCrawling: boolean;
  maxCrawlDepth: number;
  maxCrawlPages: number;
  sameDomainOnly: boolean;
  timeoutMs: number;
  scrollPages: number;
  humanDelayMin: number;
  humanDelayMax: number;
  headless: boolean;
  viewport: { width: number; height: number };
  userAgent: string;
  excludeNavigation: boolean;
  excludeAds: boolean;
  excludeSocial: boolean;
  excludeComments: boolean;
  includeMetadata: boolean;
  includeTimestamps: boolean;
  maxQuestions: number;
  questionFormat: string;
  maxRetries: number;
  retryDelay: number;
  enableFallbacks: boolean;
}

export interface PipelineRequest {
  url: string;
  query: string;
  output_filename: string;
  advanced_settings?: AdvancedSettings;
}

export interface JobStatus {
  job_id: string;
  status: string;
  message: string;
  output_file?: string;
  error?: string;
}
