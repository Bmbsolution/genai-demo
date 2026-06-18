"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import { useCompleteAuth } from "@/hooks/use-complete-auth";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type TokenPair = components["schemas"]["TokenPairResponse"];

interface CredentialResponse {
  credential: string;
}

interface GoogleIdApi {
  initialize(config: { client_id: string; callback: (r: CredentialResponse) => void }): void;
  renderButton(parent: HTMLElement, options: Record<string, string | number>): void;
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdApi } };
  }
}

const GIS_SRC = "https://accounts.google.com/gsi/client";

function loadGis(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("GIS load failed")));
      return;
    }
    const script = document.createElement("script");
    script.src = GIS_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("GIS load failed"));
    document.head.appendChild(script);
  });
}

/** Renders Google's "Continue with Google" button. No-op if the client id is unset. */
export function GoogleSignInButton() {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  const containerRef = useRef<HTMLDivElement>(null);
  const complete = useCompleteAuth();
  const tc = useTranslations("common");
  // Keep the latest closures without re-initializing GIS on every render.
  const handlers = useRef({ complete, tc });
  handlers.current = { complete, tc };

  useEffect(() => {
    if (!clientId || !containerRef.current) return undefined;
    let cancelled = false;

    loadGis()
      .then(() => {
        const container = containerRef.current;
        if (cancelled || !container || !window.google) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => {
            apiFetch<TokenPair>("/api/v1/auth/google", {
              method: "POST",
              body: { id_token: response.credential },
              auth: false,
            })
              .then((tokens) => handlers.current.complete(tokens))
              .catch(() => toast.error(handlers.current.tc("error")));
          },
        });
        window.google.accounts.id.renderButton(container, {
          type: "standard",
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "rectangular",
          width: 320,
        });
      })
      .catch(() => {
        /* GIS unavailable (offline / blocked) — the button simply won't appear. */
      });

    return () => {
      cancelled = true;
    };
  }, [clientId]);

  if (!clientId) return null;
  return <div ref={containerRef} className="flex justify-center" />;
}
