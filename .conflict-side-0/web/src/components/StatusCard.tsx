import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { fetchLatestRun } from "../api/github";
import type { WorkflowRun } from "../types";

interface StatusCardProps {
  pat: string;
  onComplete: () => void;
}

function isActiveStatus(status: string): boolean {
  return status === "queued" || status === "in_progress" || status === "waiting";
}

export function StatusCard({ pat, onComplete }: StatusCardProps) {
  const sawActiveRef = useRef(false);

  const { data: run } = useQuery<WorkflowRun | null>({
    queryKey: ["latestRun", pat],
    queryFn: () => fetchLatestRun(pat),
    refetchInterval: (query) => {
      const current = query.state.data;
      if (!current || current.status === "completed") return false;
      return 5_000;
    },
  });

  useEffect(() => {
    if (!run) return;
    if (isActiveStatus(run.status)) {
      sawActiveRef.current = true;
    }
    if (run.status === "completed" && sawActiveRef.current) {
      sawActiveRef.current = false;
      onComplete();
    }
  }, [run, onComplete]);

  if (!run || run.status === "completed") return null;

  const label = run.status === "queued" ? "Queued" : "Running";

  return (
    <div
      style={{
        background: "var(--color-background-secondary)",
        border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: 12,
        padding: "1.25rem",
        marginBottom: "1rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 16,
            height: 16,
            border: "2px solid var(--color-border-secondary)",
            borderTopColor: "#185FA5",
            borderRadius: "50%",
            animation: "vidget-spin 0.8s linear infinite",
            flexShrink: 0,
          }}
          aria-hidden
        />
        <div>
          <div style={{ fontSize: 14 }}>
            {label} ·{" "}
            <a href={run.html_url} target="_blank" rel="noreferrer" style={{ color: "#185FA5" }}>
              run #{run.id}
            </a>
          </div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 3 }}>
            Started {new Date(run.created_at).toLocaleTimeString()}
          </div>
        </div>
      </div>
      <style>{`@keyframes vidget-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
