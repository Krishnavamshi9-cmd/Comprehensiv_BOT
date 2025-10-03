export interface PipelineRequest {
  url: string;
  query: string;
  output_filename: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  message: string;
  output_file?: string;
  error?: string;
}
