import { useQuery } from "@tanstack/react-query";
import { fetchUploads } from "../api/github";
import type { UploadRecord } from "../types";

const PRIVACY_STYLE: Record<string, { color: string; background: string; border: string }> = {
  public: { color: "#3B6D11", background: "#EAF3DE", border: "#97C459" },
  unlisted: { color: "#5F5E5A", background: "#F1EFE8", border: "#B4B2A9" },
  private: { color: "#533A89", background: "#EEEDFE", border: "#AFA9EC" },
};

interface HistoryListProps {
  refreshKey: number;
  onEdit: (record: UploadRecord) => void;
}

export function HistoryList({ refreshKey, onEdit }: HistoryListProps) {
  const { data: uploads = [] } = useQuery<UploadRecord[]>({
    queryKey: ["uploads", refreshKey],
    queryFn: fetchUploads,
    staleTime: 30_000,
  });

  if (uploads.length === 0) return null;

  return (
    <div
      style={{
        background: "var(--color-background-primary)",
        border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: 12,
        padding: "1.25rem",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1rem",
        }}
      >
        <span
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "var(--color-text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.04em",
          }}
        >
          Upload history
        </span>
        <span
          style={{
            fontSize: 12,
            background: "var(--color-background-secondary)",
            border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 10,
            padding: "1px 7px",
            color: "var(--color-text-tertiary)",
          }}
        >
          {uploads.length}
        </span>
      </div>
      {uploads.map((u, i) => {
        const ps = PRIVACY_STYLE[u.privacy] ?? PRIVACY_STYLE.public;
        return (
          <div
            key={`${u.video_id}-${u.run_id}-${i}`}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 12,
              padding: "12px 0",
              borderBottom: i < uploads.length - 1 ? "0.5px solid var(--color-border-tertiary)" : "none",
            }}
          >
            <div
              style={{
                width: 72,
                height: 42,
                background: "var(--color-background-secondary)",
                borderRadius: 4,
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
              aria-hidden
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" opacity={0.3}>
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 500,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {u.title}
              </div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 3 }}>
                {new Date(u.uploaded_at).toLocaleString()}
              </div>
              <div style={{ display: "flex", gap: 6, marginTop: 6, alignItems: "center", flexWrap: "wrap" }}>
                <span
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 6,
                    border: `0.5px solid ${ps.border}`,
                    color: ps.color,
                    background: ps.background,
                  }}
                >
                  {u.privacy}
                </span>
                <a href={u.url} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: "#185FA5" }}>
                  youtu.be/{u.video_id}
                </a>
                <button type="button" onClick={() => onEdit(u)} style={{ fontSize: 12, padding: "3px 8px" }}>
                  Edit metadata
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
