import { createClient } from "@supabase/supabase-js"
import type { User } from "@supabase/supabase-js"

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type { User }

// Function to check if Supabase is configured
export function isSupabaseConfigured(): boolean {
  return !!(
    supabaseUrl &&
    supabaseAnonKey &&
    supabaseUrl !== "your-supabase-url" &&
    supabaseAnonKey !== "your-supabase-anon-key"
  )
}

// Safe client getter
export function getSupabaseClient() {
  if (!isSupabaseConfigured()) {
    console.warn("Supabase is not configured. Using demo mode.")
    return null
  }
  return supabase
}
