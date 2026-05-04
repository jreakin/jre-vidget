import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { dispatchPublish } from "../api/github";
import type { DispatchInputs } from "../types";

interface UploadFormProps {
  pat: string;
  onDispatched: () => void;
}

export function UploadForm({ pat, onDispatched }: UploadFormProps) {
  const [form, setForm] = useState<DispatchInputs>({
    url: "",
    title: "",
    description: "",
    privacy: "public",
    remove_after_upload: false,
  });

  const mutation = useMutation({
    mutationFn: () => dispatchPublish(pat, form),
    onSuccess: () => {
      onDispatched();
      setForm((f) => ({ ...f, url: "", title: "", description: "" }));
    },
  });

  return (
    <div
      style={{
        background: "var(--color-background-primary)",
        border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: 12,
        padding: "1.25rem",
        marginBottom: "1rem",
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontWeight: 500,
          color: "var(--color-text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          marginBottom: "1rem",
        }}
      >
        New upload
      </div>

      <label
        style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}
      >
        Video URL
      </label>
      <input
        type="url"
        placeholder="https://twitter.com/…"
        value={form.url}
        onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
        style={{ width: "100%", marginBottom: 14 }}
      />

      <label
        style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}
      >
        Title
      </label>
      <input
        type="text"
        placeholder="Leave blank to use scraped title"
        value={form.title}
        onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
        style={{ width: "100%", marginBottom: 14 }}
      />

      <label
        style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}
      >
        Description
      </label>
      <textarea
        value={form.description}
        onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
        style={{ width: "100%", height: 72, resize: "none", marginBottom: 14, fontFamily: "inherit" }}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
        <div>
          <label
            style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}
          >
            Privacy
          </label>
          <select
            value={form.privacy}
            onChange={(e) =>
              setForm((f) => ({ ...f, privacy: e.target.value as DispatchInputs["privacy"] }))
            }
            style={{ width: "100%" }}
          >
            <option value="public">Public</option>
            <option value="unlisted">Unlisted</option>
            <option value="private">Private</option>
          </select>
        </div>
        <div>
          <label
            style={{ display: "block", fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 5 }}
          >
            After upload
          </label>
          <select
            value={form.remove_after_upload ? "remove" : "keep"}
            onChange={(e) =>
              setForm((f) => ({ ...f, remove_after_upload: e.target.value === "remove" }))
            }
            style={{ width: "100%" }}
          >
            <option value="keep">Keep local file</option>
            <option value="remove">Delete local file</option>
          </select>
        </div>
      </div>

      {mutation.isError && (
        <p style={{ fontSize: 13, color: "var(--color-text-danger)", marginBottom: 10 }}>
          {mutation.error instanceof Error ? mutation.error.message : String(mutation.error)}
        </p>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={!form.url || mutation.isPending}
          style={{
            background: "#185FA5",
            color: "white",
            border: "none",
            borderRadius: 8,
            padding: "8px 18px",
            fontSize: 14,
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          {mutation.isPending ? "Queuing…" : "Download & upload"}
        </button>
        <button
          type="button"
          onClick={() =>
            setForm({
              url: "",
              title: "",
              description: "",
              privacy: "public",
              remove_after_upload: false,
            })
          }
        >
          Reset
        </button>
        <span style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginLeft: "auto" }}>
          ~2–4 min for 1080p
        </span>
      </div>
    </div>
  );
}
