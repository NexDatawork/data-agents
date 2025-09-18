import { supabase, isSupabaseConfigured } from "./supabase"
import { getCurrentUser } from "./auth"

export interface UserSettings {
  id?: string
  user_id: string
  notifications: {
    emailNotifications: boolean
    pushNotifications: boolean
    analysisComplete: boolean
    weeklyReports: boolean
    securityAlerts: boolean
  }
  privacy: {
    dataRetention: string
    shareAnalytics: boolean
    publicProfile: boolean
  }
  apiSettings: {
    openaiApiKey: string
    azureEndpoint: string
    rateLimiting: boolean
  }
  created_at?: string
  updated_at?: string
}

export interface PasswordChangeData {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export async function getUserSettings(): Promise<UserSettings | null> {
  try {
    if (!isSupabaseConfigured()) {
      console.warn("Supabase not configured, using localStorage fallback")
      const savedSettings = localStorage.getItem("nexdatawork_settings")
      if (savedSettings) {
        return JSON.parse(savedSettings)
      }
      return null
    }

    const user = await getCurrentUser()
    if (!user) {
      throw new Error("User not authenticated")
    }

    const { data, error } = await supabase.from("user_settings").select("*").eq("user_id", user.id).single()

    if (error) {
      if (error.code === "PGRST116") {
        // No settings found, return null
        return null
      }
      throw error
    }

    // Map database columns to camelCase
    return {
      ...data,
      apiSettings: data.api_settings,
    }
  } catch (error) {
    console.error("Error fetching user settings:", error)
    throw error
  }
}

export async function saveUserSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
  try {
    if (!isSupabaseConfigured()) {
      console.warn("Supabase not configured, using localStorage fallback")
      const settingsData = {
        ...settings,
        updated_at: new Date().toISOString(),
      }
      localStorage.setItem("nexdatawork_settings", JSON.stringify(settingsData))
      return settingsData as UserSettings
    }

    const user = await getCurrentUser()
    if (!user) {
      throw new Error("User not authenticated")
    }

    // Map camelCase to database column names
    const settingsData = {
      user_id: user.id,
      notifications: settings.notifications,
      privacy: settings.privacy,
      api_settings: settings.apiSettings, // Map to snake_case
      updated_at: new Date().toISOString(),
    }

    const { data, error } = await supabase
      .from("user_settings")
      .upsert(settingsData, {
        onConflict: "user_id",
      })
      .select()
      .single()

    if (error) {
      throw error
    }

    // Map database response back to camelCase
    return {
      ...data,
      apiSettings: data.api_settings,
    }
  } catch (error) {
    console.error("Error saving user settings:", error)
    throw error
  }
}

export async function changePassword(passwordData: PasswordChangeData): Promise<void> {
  try {
    if (!isSupabaseConfigured()) {
      throw new Error("Password change requires Supabase configuration")
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      throw new Error("New passwords do not match")
    }

    if (passwordData.newPassword.length < 8) {
      throw new Error("Password must be at least 8 characters long")
    }

    // First verify the current password by attempting to sign in
    const user = await getCurrentUser()
    if (!user?.email) {
      throw new Error("User email not found")
    }

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: user.email,
      password: passwordData.currentPassword,
    })

    if (signInError) {
      throw new Error("Current password is incorrect")
    }

    // Update the password
    const { error: updateError } = await supabase.auth.updateUser({
      password: passwordData.newPassword,
    })

    if (updateError) {
      throw updateError
    }
  } catch (error) {
    console.error("Error changing password:", error)
    throw error
  }
}

export async function enableTwoFactorAuth(): Promise<void> {
  try {
    if (!isSupabaseConfigured()) {
      throw new Error("Two-factor authentication requires Supabase configuration")
    }

    // This would integrate with Supabase Auth's MFA features
    // For now, we'll throw an error indicating it's not implemented
    throw new Error("Two-factor authentication setup is not yet implemented")
  } catch (error) {
    console.error("Error enabling 2FA:", error)
    throw error
  }
}
