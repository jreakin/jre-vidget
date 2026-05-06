import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { TopBar } from "../components/TopBar";
import { AppRouter } from "../router";

const githubApi = vi.hoisted(() => ({
  fetchUploads: vi.fn(async () => []),
  fetchLatestRun: vi.fn(async () => null),
  listSecretNames: vi.fn(async () => [
    "VIDGET_CLIENT_ID",
    "VIDGET_CLIENT_SECRET",
    "VIDGET_REFRESH_TOKEN",
  ]),
  dispatchPublish: vi.fn(async () => undefined),
  getRepoPublicKey: vi.fn(async () => ({ key: "x", key_id: "123" })),
  setSecret: vi.fn(async () => undefined),
}));

vi.mock("../api/github", () => githubApi);

describe("web smoke", () => {
  afterEach(() => {
    localStorage.clear();
  });

  it("ErrorBoundary renders children when there is no error", () => {
    render(
      <ErrorBoundary repo="owner/repo">
        <div data-testid="child">ok</div>
      </ErrorBoundary>,
    );
    expect(screen.getByTestId("child")).toHaveTextContent("ok");
  });

  it("TopBar renders branding and clear action", () => {
    const onClear = vi.fn();
    render(<TopBar onClearPAT={onClear} />);
    expect(screen.getByText(/powered by vidget/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /disconnect/i })).toBeInTheDocument();
  });
});

describe("AppRouter smoke", () => {
  beforeEach(() => {
    localStorage.setItem("vidget_gh_pat", "ghp_smoke_test_token");
    localStorage.setItem("vidget_setup_complete", "true");
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("renders the shell via RouterProvider after PAT and setup gate", async (): Promise<void> => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const repo = "jreakin/jre-vidget";

    render(
      <QueryClientProvider client={queryClient}>
        <ErrorBoundary repo={repo}>
          <AppRouter />
        </ErrorBoundary>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /disconnect/i })).toBeInTheDocument();
    });
    expect(screen.getByText("New upload")).toBeInTheDocument();
  });
});
