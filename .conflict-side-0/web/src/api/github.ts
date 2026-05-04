import type { DispatchInputs, UploadRecord, WorkflowRun } from "../types";

const REPO = import.meta.env.VITE_GITHUB_REPO;
const API = "https://api.github.com";
const RAW = "https://raw.githubusercontent.com";

function requireRepo(): string {
  if (!REPO || !REPO.includes("/")) {
    throw new Error(
      "VITE_GITHUB_REPO is not set (expected owner/repo). Set it when running dev or in CI.",
    );
  }
  return REPO;
}

function headers(pat: string): HeadersInit {
  return {
    Authorization: `Bearer ${pat}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

/** Trigger the publish workflow_dispatch. */
export async function dispatchPublish(pat: string, inputs: DispatchInputs): Promise<void> {
  const repo = requireRepo();
  const res = await fetch(`${API}/repos/${repo}/actions/workflows/publish.yml/dispatches`, {
    method: "POST",
    headers: headers(pat),
    body: JSON.stringify({
      ref: "main",
      inputs: {
        url: inputs.url,
        title: inputs.title,
        description: inputs.description,
        privacy: inputs.privacy,
        remove_after_upload: String(inputs.remove_after_upload),
      },
    }),
  });
  if (!res.ok) {
    throw new Error(`Dispatch failed: ${res.status} ${await res.text()}`);
  }
}

/** Fetch the most recent workflow run for the publish workflow. */
export async function fetchLatestRun(pat: string): Promise<WorkflowRun | null> {
  const repo = requireRepo();
  const res = await fetch(
    `${API}/repos/${repo}/actions/workflows/publish.yml/runs?per_page=1`,
    { headers: headers(pat) },
  );
  if (!res.ok) return null;
  const data: { workflow_runs?: WorkflowRun[] } = await res.json();
  const run = data.workflow_runs?.[0];
  return run ?? null;
}

/** Fetch uploads.json from the main branch. No auth needed for public repos. */
export async function fetchUploads(): Promise<UploadRecord[]> {
  const repo = requireRepo();
  const [owner, name] = repo.split("/");
  const res = await fetch(`${RAW}/${owner}/${name}/main/uploads.json`);
  if (!res.ok) return [];
  const data: { uploads?: UploadRecord[] } = await res.json();
  return data.uploads ?? [];
}
