import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  userId: string | null;
  displayName: string | null;
  hydrated: boolean;
  setSession: (tokens: { accessToken: string; refreshToken: string }) => void;
  setUser: (user: { id: string; name: string }) => void;
  setHydrated: () => void;
  clear: () => void;
}

const EMPTY = {
  accessToken: null,
  refreshToken: null,
  userId: null,
  displayName: null,
} as const;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      ...EMPTY,
      hydrated: false,
      setSession: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      setUser: ({ id, name }) => set({ userId: id, displayName: name }),
      setHydrated: () => set({ hydrated: true }),
      clear: () => set({ ...EMPTY }),
    }),
    {
      name: "gatherly-auth",
      // Persist only the session fields; `hydrated` is per-load runtime state.
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        userId: state.userId,
        displayName: state.displayName,
      }),
      onRehydrateStorage: () => (state) => state?.setHydrated(),
    },
  ),
);
