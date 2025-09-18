import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase"
import { getCurrentUser } from "@/lib/auth"

export interface UserProfile {
  id?: string
  user_id: string
  first_name?: string
  last_name?: string
  bio?: string
  location?: string
  company?: string
  role?: string
  phone?: string
  website?: string
  avatar_url?: string
  preferences?: Record<string, any>
  created_at?: string
  updated_at?: string
}

export interface ProfileUpdateData {
  first_name?: string
  last_name?: string
  bio?: string
  location?: string
  company?: string
  role?: string
  phone?: string
  website?: string
  avatar_url?: string
  preferences?: Record<string, any>
}

/**
 * Get user profile from Supabase
 */
export async function getUserProfile(): Promise<{ data: UserProfile | null; error: string | null }> {
  try {
    if (!isSupabaseConfigured()) {
      console.warn("Supabase not configured, using demo mode")
      return { data: null, error: null }
    }

    const client = getSupabaseClient()
    if (!client) {
      return { data: null, error: "Supabase client not available" }
    }

    const user = await getCurrentUser()
    if (!user) {
      return { data: null, error: "User not authenticated" }
    }

    console.log("Fetching profile for user:", user.id)

    const { data, error } = await client.from("user_profiles").select("*").eq("user_id", user.id).single()

    if (error) {
      if (error.code === "PGRST116") {
        // No profile found, this is normal for new users
        console.log("No profile found for user, will create one on first update")
        return { data: null, error: null }
      }
      console.error("Error fetching user profile:", error)
      return { data: null, error: error.message }
    }

    console.log("Profile fetched successfully:", data)
    return { data, error: null }
  } catch (error) {
    console.error("Error in getUserProfile:", error)
    return { data: null, error: error instanceof Error ? error.message : "Unknown error" }
  }
}

/**
 * Update or create user profile in Supabase
 */
export async function updateUserProfile(
  profileData: ProfileUpdateData,
): Promise<{ data: UserProfile | null; error: string | null }> {
  try {
    if (!isSupabaseConfigured()) {
      console.warn("Supabase not configured, using demo mode")
      return { data: null, error: null }
    }

    const client = getSupabaseClient()
    if (!client) {
      return { data: null, error: "Supabase client not available" }
    }

    const user = await getCurrentUser()
    if (!user) {
      return { data: null, error: "User not authenticated" }
    }

    console.log("Updating profile for user:", user.id, profileData)

    // First, try to update existing profile
    const { data: updateData, error: updateError } = await client
      .from("user_profiles")
      .update({
        ...profileData,
        updated_at: new Date().toISOString(),
      })
      .eq("user_id", user.id)
      .select()
      .single()

    if (updateError) {
      if (updateError.code === "PGRST116") {
        // No existing profile, create a new one
        console.log("No existing profile found, creating new one")

        const { data: insertData, error: insertError } = await client
          .from("user_profiles")
          .insert({
            user_id: user.id,
            ...profileData,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
          .select()
          .single()

        if (insertError) {
          console.error("Error creating user profile:", insertError)
          return { data: null, error: insertError.message }
        }

        console.log("Profile created successfully:", insertData)
        return { data: insertData, error: null }
      } else {
        console.error("Error updating user profile:", updateError)
        return { data: null, error: updateError.message }
      }
    }

    console.log("Profile updated successfully:", updateData)
    return { data: updateData, error: null }
  } catch (error) {
    console.error("Error in updateUserProfile:", error)
    return { data: null, error: error instanceof Error ? error.message : "Unknown error" }
  }
}

/**
 * Delete user profile from Supabase
 */
export async function deleteUserProfile(): Promise<{ error: string | null }> {
  try {
    if (!isSupabaseConfigured()) {
      console.warn("Supabase not configured, using demo mode")
      return { error: null }
    }

    const client = getSupabaseClient()
    if (!client) {
      return { error: "Supabase client not available" }
    }

    const user = await getCurrentUser()
    if (!user) {
      return { error: "User not authenticated" }
    }

    console.log("Deleting profile for user:", user.id)

    const { error } = await client.from("user_profiles").delete().eq("user_id", user.id)

    if (error) {
      console.error("Error deleting user profile:", error)
      return { error: error.message }
    }

    console.log("Profile deleted successfully")
    return { error: null }
  } catch (error) {
    console.error("Error in deleteUserProfile:", error)
    return { error: error instanceof Error ? error.message : "Unknown error" }
  }
}

/**
 * Check if user has a profile
 */
export async function hasUserProfile(): Promise<{ hasProfile: boolean; error: string | null }> {
  try {
    if (!isSupabaseConfigured()) {
      return { hasProfile: false, error: null }
    }

    const client = getSupabaseClient()
    if (!client) {
      return { hasProfile: false, error: "Supabase client not available" }
    }

    const user = await getCurrentUser()
    if (!user) {
      return { hasProfile: false, error: "User not authenticated" }
    }

    const { data, error } = await client.from("user_profiles").select("id").eq("user_id", user.id).single()

    if (error) {
      if (error.code === "PGRST116") {
        return { hasProfile: false, error: null }
      }
      return { hasProfile: false, error: error.message }
    }

    return { hasProfile: !!data, error: null }
  } catch (error) {
    console.error("Error in hasUserProfile:", error)
    return { hasProfile: false, error: error instanceof Error ? error.message : "Unknown error" }
  }
}
