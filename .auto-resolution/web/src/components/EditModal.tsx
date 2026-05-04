import { useEffect } from "react";
import type { UploadRecord } from "../types";

interface EditModalProps {
  record: UploadRecord;
  onClose: () => void;
}

export function EditModal({ record, onClose }: EditModalProps) {
  const studioUrl = `https://studio.youtube.com/video/${record.video_id}/edit`;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      role="presentation"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-modal-title"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--color-background-primary)",
          border: "0.5px solid var(--color-border-tertiary)",
          borderRadius: 12,
          padding: "1.5rem",
          maxWidth: 420,
          width: "90%",
        }}
      >
        <div id="edit-modal-title" style={{ fontSize: 16, fontWeight: 500, marginBottom: "0.5rem" }}>
          Edit metadata
        </div>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1rem" }}>
          <strong>{record.title}</strong>
        </p>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: "1.25rem" }}>
          Title and description can be edited directly in YouTube Studio. In-page editing via the
          YouTube API will be added in a future update.
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <a
            href={studioUrl}
            target="_blank"
            rel="noreferrer"
            style={{
              flex: 1,
              background: "#185FA5",
              color: "white",
              border: "none",
              borderRadius: 8,
              padding: "8px 0",
              fontSize: 14,
              fontWeight: 500,
              textAlign: "center",
              textDecoration: "none",
            }}
          >
            Open in YouTube Studio
          </a>
          <button type="button" onClick={onClose} style={{ flex: 1 }}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
