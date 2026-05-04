import { useState } from "react";

const KEY = "vidget_gh_pat";

export function usePAT(): {
  pat: string;
  setPAT: (v: string) => void;
  clearPAT: () => void;
} {
  const [pat, setPATState] = useState(() => localStorage.getItem(KEY) ?? "");
  const setPAT = (v: string) => {
    localStorage.setItem(KEY, v);
    setPATState(v);
  };
  const clearPAT = () => {
    localStorage.removeItem(KEY);
    setPATState("");
  };
  return { pat, setPAT, clearPAT };
}
