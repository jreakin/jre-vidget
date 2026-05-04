import { useState } from "react";

interface PATGateProps {
  onSave: (pat: string) => void;
}

export function PATGate({ onSave }: PATGateProps) {
  const [value, setValue] = useState("");
  return (
    <div style={{ maxWidth: 480, margin: "4rem auto", padding: "0 1rem" }}>
      <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "1rem" }}>
        Enter your GitHub token
      </h2>
      <p style={{ fontSize: 14, color: "var(--color-text-secondary)", marginBottom: "1rem" }}>
        A fine-grained token with <code>Actions: write</code> and <code>Contents: write</code> on
        this repo. Stored in browser localStorage — only sent to GitHub&apos;s API.
      </p>
      <input
        type="password"
        placeholder="github_pat_..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={{ width: "100%", marginBottom: "0.75rem" }}
      />
      <button
        type="button"
        disabled={!value.startsWith("github_")}
        onClick={() => onSave(value)}
        style={{ width: "100%" }}
      >
        Save token
      </button>
    </div>
  );
}
