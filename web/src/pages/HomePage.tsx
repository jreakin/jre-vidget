import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { listSecretNames } from "../api/github";
import { EditModal } from "../components/EditModal";
import { HistoryList } from "../components/HistoryList";
import { PATGate } from "../components/PATGate";
import { SetupWizard } from "../components/SetupWizard";
import { StatusCard } from "../components/StatusCard";
import { TopBar } from "../components/TopBar";
import { UploadForm } from "../components/UploadForm";
import { usePAT } from "../hooks/usePAT";
import {
  GCLOUD_CLIENT_ID_KEYS,
  GCLOUD_CLIENT_SECRET_KEYS,
  GCLOUD_REFRESH_TOKEN_KEYS,
  hasAnySecret,
} from "../lib/google-oauth-secrets";
import type { UploadRecord } from "../types";

function oauthSecretsComplete(names: string[]): boolean {
  return (
    hasAnySecret(GCLOUD_CLIENT_ID_KEYS, names) &&
    hasAnySecret(GCLOUD_CLIENT_SECRET_KEYS, names) &&
    hasAnySecret(GCLOUD_REFRESH_TOKEN_KEYS, names)
  );
}

export function HomePage() {
  const { pat, setPAT, clearPAT } = usePAT();
  const [setupComplete, setSetupComplete] = useState(
    () => localStorage.getItem("vidget_setup_complete") === "true",
  );
  const [refreshKey, setRefreshKey] = useState(0);
  const [editRecord, setEditRecord] = useState<UploadRecord | null>(null);

  const bumpHistory = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  const markSetupComplete = useCallback(() => {
    localStorage.setItem("vidget_setup_complete", "true");
    setSetupComplete(true);
  }, []);

  const { data: secretNames, isLoading: checkingSecrets } = useQuery({
    queryKey: ["secretNamesCheck", pat],
    queryFn: () => listSecretNames(pat),
    enabled: Boolean(pat) && !setupComplete,
    retry: 1,
    staleTime: Number.POSITIVE_INFINITY,
  });

  useEffect(() => {
    if (!secretNames) return;
    const allPresent = oauthSecretsComplete(secretNames);
    if (allPresent) {
      queueMicrotask(() => {
        markSetupComplete();
      });
    }
  }, [markSetupComplete, secretNames]);

  const handleClearPAT = useCallback(() => {
    clearPAT();
    setSetupComplete(false);
    localStorage.removeItem("vidget_setup_complete");
  }, [clearPAT]);

  if (!pat) {
    return <PATGate onSave={setPAT} />;
  }

  if (!setupComplete && checkingSecrets) {
    return (
      <div
        style={{
          maxWidth: 520,
          margin: "4rem auto",
          padding: "0 1rem",
          textAlign: "center",
          color: "var(--color-text-secondary)",
          fontSize: 14,
        }}
      >
        Checking configuration…
      </div>
    );
  }

  if (!setupComplete) {
    return <SetupWizard pat={pat} onComplete={markSetupComplete} />;
  }

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <TopBar onClearPAT={handleClearPAT} />
      <UploadForm pat={pat} onDispatched={bumpHistory} />
      <StatusCard pat={pat} onComplete={bumpHistory} />
      <HistoryList refreshKey={refreshKey} onEdit={setEditRecord} />
      {editRecord && <EditModal record={editRecord} onClose={() => setEditRecord(null)} />}
    </div>
  );
}
