import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { TopBar } from "../components/TopBar";

describe("web smoke", () => {
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
