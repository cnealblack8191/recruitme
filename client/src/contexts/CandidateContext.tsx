import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface CandidateSession {
  id: number;
  fullName: string;
  birthdate: string;
}

const STORAGE_KEY = "eci.candidateSession";

interface CandidateContextValue {
  candidate: CandidateSession | null;
  setCandidate: (c: CandidateSession) => void;
  clearCandidate: () => void;
  ready: boolean;
}

const CandidateContext = createContext<CandidateContextValue>({
  candidate: null,
  setCandidate: () => {},
  clearCandidate: () => {},
  ready: false,
});

export function CandidateProvider({ children }: { children: ReactNode }) {
  const [candidate, setCandidateState] = useState<CandidateSession | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as CandidateSession;
        if (parsed && typeof parsed.id === "number" && parsed.fullName) {
          setCandidateState(parsed);
        }
      }
    } catch {
      /* corrupted storage — start fresh */
    }
    setReady(true);
  }, []);

  const setCandidate = useCallback((c: CandidateSession) => {
    setCandidateState(c);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(c));
  }, []);

  const clearCandidate = useCallback(() => {
    setCandidateState(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({ candidate, setCandidate, clearCandidate, ready }),
    [candidate, setCandidate, clearCandidate, ready]
  );

  return <CandidateContext.Provider value={value}>{children}</CandidateContext.Provider>;
}

export function useCandidate() {
  return useContext(CandidateContext);
}
