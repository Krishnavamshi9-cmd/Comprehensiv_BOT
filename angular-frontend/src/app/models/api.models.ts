export interface PipelineRequest {
  url: string;
  query: string;
  output_filename: string;
  k: number;
  scroll_pages: number;
  output_format: string;
  validate_content: boolean;
  crawl: boolean;
  max_depth: number;
  max_pages: number;
  same_domain_only: boolean;
  with_test_cases: boolean;
  test_cases_llm: boolean;
  tc_variations: number;
  tc_negatives: number;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  message: string;
  progress?: string;
  output_file?: string;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface HealthResponse {
  message: string;
  version: string;
}
