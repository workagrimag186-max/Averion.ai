import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
  // Always use English as default for now
  // UI translation will be handled client-side based on user preference
  const locale = "en";
  
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default
  };
});

// Made with Bob
