import { supabase } from "./supabase"
import { getCurrentUser } from "./auth"
import type { OnboardingData } from "@/components/onboarding-modal"

export interface OnboardingResult {
  success: boolean
  data?: OnboardingData | null
  error?: string
}

export async function saveOnboardingData(data: OnboardingData): Promise<OnboardingResult> {
  try {
    const user = await getCurrentUser()

    if (!user) {
      return {
        success: false,
        error: "User not authenticated",
      }
    }

    const onboardingRecord = {
      user_id: user.id,
      first_name: data.firstName,
      role: data.role,
      goals: data.goals,
      custom_goal: data.customGoal,
      data_types: data.dataTypes,
      data_locations: data.dataLocations,
      updated_at: new Date().toISOString(),
    }

    const { data: result, error } = await supabase
      .from("onboarding_data")
      .upsert(onboardingRecord, {
        onConflict: "user_id",
      })
      .select()
      .single()

    if (error) {
      console.error("Error saving onboarding data:", error)
      return {
        success: false,
        error: error.message,
      }
    }

    return {
      success: true,
      data: data,
    }
  } catch (error) {
    console.error("Unexpected error saving onboarding data:", error)
    return {
      success: false,
      error: "An unexpected error occurred",
    }
  }
}

export async function getOnboardingData(): Promise<OnboardingResult> {
  try {
    const user = await getCurrentUser()

    if (!user) {
      return {
        success: false,
        error: "User not authenticated",
      }
    }

    const { data, error } = await supabase.from("onboarding_data").select("*").eq("user_id", user.id).single()

    if (error) {
      if (error.code === "PGRST116") {
        // No data found - this is normal for new users
        return {
          success: true,
          data: null,
        }
      }

      console.error("Error fetching onboarding data:", error)
      return {
        success: false,
        error: error.message,
      }
    }

    if (!data) {
      return {
        success: true,
        data: null,
      }
    }

    // Transform database record back to OnboardingData format
    const onboardingData: OnboardingData = {
      firstName: data.first_name,
      role: data.role,
      goals: data.goals || [],
      customGoal: data.custom_goal || "",
      dataTypes: data.data_types || [],
      dataLocations: data.data_locations || [],
    }

    return {
      success: true,
      data: onboardingData,
    }
  } catch (error) {
    console.error("Unexpected error fetching onboarding data:", error)
    return {
      success: false,
      error: "An unexpected error occurred",
    }
  }
}

export async function deleteOnboardingData(): Promise<OnboardingResult> {
  try {
    const user = await getCurrentUser()

    if (!user) {
      return {
        success: false,
        error: "User not authenticated",
      }
    }

    const { error } = await supabase.from("onboarding_data").delete().eq("user_id", user.id)

    if (error) {
      console.error("Error deleting onboarding data:", error)
      return {
        success: false,
        error: error.message,
      }
    }

    return {
      success: true,
      data: null,
    }
  } catch (error) {
    console.error("Unexpected error deleting onboarding data:", error)
    return {
      success: false,
      error: "An unexpected error occurred",
    }
  }
}
