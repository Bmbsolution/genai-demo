import type { Metadata } from "next";
import {
  Bricolage_Grotesque,
  Hanken_Grotesk,
  Inter,
  JetBrains_Mono,
  Montserrat,
} from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";

import { Providers } from "./providers";
import "./globals.css";

// Display: characterful grotesque for headings + brand. Body: refined,
// readable Hanken Grotesk. Mono: JetBrains for repo URLs, criterion ids, code.
const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});
const sans = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});
// Corporate marketing pairing (landing page): Montserrat display + Inter body.
const corpDisplay = Montserrat({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-corp-display",
  display: "swap",
});
const corpBody = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-corp-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Gatherly",
  description: "Plan events, invite guests, collect RSVPs",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      suppressHydrationWarning
      className={`${display.variable} ${sans.variable} ${mono.variable} ${corpDisplay.variable} ${corpBody.variable}`}
    >
      {/* suppressHydrationWarning: browser extensions (e.g. Grammarly) inject
          data-gr-ext-* attributes onto <body> before React hydrates. */}
      <body className="font-sans antialiased" suppressHydrationWarning>
        <NextIntlClientProvider messages={messages}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
