export interface UploadRecord {
  video_id: string;
  url: string;
  title: string;
  source_url: string;
  privacy: "public" | "unlisted" | "private";
  uploaded_at: string;
  run_id: string;
}

export interface WorkflowRun {
  id: number;
  status: "queued" | "in_progress" | "completed" | "waiting" | "action_required" | string;
  conclusion: "success" | "failure" | "cancelled" | "skipped" | null;
  html_url: string;
  created_at: string;
}

export interface DispatchInputs {
  url: string;
  title: string;
  description: string;
  privacy: "public" | "unlisted" | "private";
  remove_after_upload: boolean;
}
