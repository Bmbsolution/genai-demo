import { getRequestConfig } from "next-intl/server";

// Single-locale setup (no i18n routing). Both en and fr message files exist so
// every user-visible string lives in translations; a locale switcher is future.
const LOCALE = "en";

export default getRequestConfig(async () => ({
  locale: LOCALE,
  messages: (await import(`../messages/${LOCALE}.json`)).default,
}));
