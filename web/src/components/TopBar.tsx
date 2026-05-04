interface TopBarProps {
  onClearPAT: () => void;
}

export function TopBar({ onClearPAT }: TopBarProps) {
  const title = import.meta.env.VITE_APP_TITLE || "vidget";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "2rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div
          style={{
            width: 28,
            height: 28,
            background: "#185FA5",
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="white" aria-hidden>
            <path d="M8 1L1 14h14L8 1zm0 3l4.5 8h-9L8 4z" />
          </svg>
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 500, lineHeight: 1.2 }}>{title}</div>
          <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", lineHeight: 1.2 }}>
            powered by vidget
          </div>
        </div>
      </div>
      <button type="button" onClick={onClearPAT} style={{ fontSize: 13 }}>
        Disconnect
      </button>
    </div>
  );
}
