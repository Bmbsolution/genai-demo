import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  workspaceId: string | null;
  workspaceName: string | null;
  hydrated: boolean;
  setSession: (tokens: { accessToken: string; refreshToken: string }) => void;
  setWorkspace: (workspace: { id: string; name: string }) => void;
  setHydrated: () => void;
  clear: () => void;
}

const EMPTY = {
  accessToken: null,
  refreshToken: null,
  workspaceId: null,
  workspaceName: null,
} as const;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      ...EMPTY,
      hydrated: false,
      setSession: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      setWorkspace: ({ id, name }) => set({ workspaceId: id, workspaceName: name }),
      setHydrated: () => set({ hydrated: true }),
      clear: () => set({ ...EMPTY }),
    }),
    {
      name: "gatherly-auth",
      // Persist only the session fields; `hydrated` is per-load runtime state.
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        workspaceId: state.workspaceId,
        workspaceName: state.workspaceName,
      }),
      onRehydrateStorage: () => (state) => state?.setHydrated(),
    },
  ),
);
