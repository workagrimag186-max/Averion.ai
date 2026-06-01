import {
  createClient,
  type Session,
  type SupabaseClient
} from "@supabase/supabase-js";

let browserClient: SupabaseClient | null = null;

export function getSupabaseBrowserClient(): SupabaseClient | null {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    return null;
  }

  if (!browserClient) {
    browserClient = createClient(supabaseUrl, supabaseAnonKey);
  }

  return browserClient;
}

export function getAuthRedirectUrl(): string {
  if (process.env.NEXT_PUBLIC_AUTH_REDIRECT_URL) {
    return process.env.NEXT_PUBLIC_AUTH_REDIRECT_URL;
  }

  if (typeof window !== "undefined") {
    return `${window.location.origin}/auth/callback`;
  }

  return "http://localhost:3000/auth/callback";
}

export async function getSupabaseSessionSafely(
  client: SupabaseClient
): Promise<Session | null> {
  const { data, error } = await client.auth.getSession();

  if (!error) {
    return data.session;
  }

  await client.auth.signOut({ scope: "local" });
  return null;
}
