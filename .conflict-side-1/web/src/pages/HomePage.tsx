import { useCallback, useState } from "react";
import { EditModal } from "../components/EditModal";
import { HistoryList } from "../components/HistoryList";
import { PATGate } from "../components/PATGate";
import { usePAT } from "../hooks/usePAT";
import { StatusCard } from "../components/StatusCard";
import { TopBar } from "../components/TopBar";
import { UploadForm } from "../components/UploadForm";
import type { UploadRecord } from "../types";

export function HomePage() {
  const { pat, setPAT, clearPAT } = usePAT();
  const [refreshKey, setRefreshKey] = useState(0);
  const [editRecord, setEditRecord] = useState<UploadRecord | null>(null);

  const bumpHistory = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  if (!pat) {
    return <PATGate onSave={setPAT} />;
  }

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <TopBar onClearPAT={clearPAT} />
      <UploadForm pat={pat} onDispatched={bumpHistory} />
      <StatusCard pat={pat} onComplete={bumpHistory} />
      <HistoryList refreshKey={refreshKey} onEdit={setEditRecord} />
      {editRecord && <EditModal record={editRecord} onClose={() => setEditRecord(null)} />}
    </div>
  );
}
