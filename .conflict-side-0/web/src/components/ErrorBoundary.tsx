import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  /** e.g. "jreakin/jre-vidget" */
  repo: string;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  private buildIssueUrl(): string {
    const { error } = this.state;
    if (!error) return "#";

    const title = encodeURIComponent(`Web UI error: ${error.message.slice(0, 80)}`);
    const body = encodeURIComponent(
      `## Web UI error report\n\n` +
        `**Error:** \`${error.message}\`\n\n` +
        `**Stack:**\n\`\`\`\n${error.stack ?? "none"}\n\`\`\`\n\n` +
        `**Page:** ${window.location.href}\n\n` +
        `**User agent:** ${navigator.userAgent}\n\n` +
        `---\n*Please review and remove any personal info before submitting.*`,
    );
    const labels = encodeURIComponent("bug,web-ui");
    return `https://github.com/${this.props.repo}/issues/new?title=${title}&body=${body}&labels=${labels}`;
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div style={{ maxWidth: 560, margin: "4rem auto", padding: "0 1rem" }}>
        <div
          style={{
            background: "var(--color-background-primary)",
            border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 12,
            padding: "1.5rem",
          }}
        >
          <div
            style={{
              fontSize: 16,
              fontWeight: 500,
              marginBottom: "0.5rem",
              color: "var(--color-text-danger)",
            }}
          >
            Something went wrong
          </div>
          <p
            style={{
              fontSize: 13,
              color: "var(--color-text-secondary)",
              marginBottom: "0.75rem",
            }}
          >
            The app encountered an unexpected error.
          </p>
          <pre
            style={{
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              background: "var(--color-background-secondary)",
              border: "0.5px solid var(--color-border-tertiary)",
              borderRadius: 6,
              padding: "0.75rem",
              overflow: "auto",
              marginBottom: "1.25rem",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {error.message}
          </pre>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              onClick={() => this.setState({ error: null })}
              style={{ flex: 1 }}
            >
              Try again
            </button>
            <a
              href={this.buildIssueUrl()}
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
                display: "block",
              }}
            >
              Report this bug
            </a>
          </div>
          <p
            style={{
              fontSize: 11,
              color: "var(--color-text-tertiary)",
              marginTop: "0.75rem",
            }}
          >
            Clicking &quot;Report&quot; opens a pre-filled GitHub issue. Review it before
            submitting — no personal info is included automatically.
          </p>
        </div>
      </div>
    );
  }
}
