import { supabase } from "./supabase"

export interface SignUpData {
  email: string
  password: string
  username: string
}

export interface AuthResult {
  success: boolean
  error?: string
  user?: any
}

export async function signUp({ email, password, username }: SignUpData): Promise<AuthResult> {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username: username,
          display_name: username,
          full_name: username,
        },
      },
    })

    if (error) {
      // Handle specific Supabase errors
      let errorMessage = error.message

      if (error.message.includes("User already registered")) {
        errorMessage = "An account with this email already exists"
      } else if (error.message.includes("Password should be at least")) {
        errorMessage = "Password must be at least 8 characters long"
      } else if (error.message.includes("Invalid email")) {
        errorMessage = "Please enter a valid email address"
      } else if (error.message.includes("Signup is disabled")) {
        errorMessage = "Account creation is currently disabled"
      }

      return {
        success: false,
        error: errorMessage,
      }
    }

    return {
      success: true,
      user: data.user,
    }
  } catch (err: any) {
    console.error("Signup error:", err)
    return {
      success: false,
      error: "An unexpected error occurred. Please try again.",
    }
  }
}

export async function signIn(email: string, password: string): Promise<AuthResult> {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      return {
        success: false,
        error: error.message,
      }
    }

    return {
      success: true,
      user: data.user,
    }
  } catch (err: any) {
    return {
      success: false,
      error: "An unexpected error occurred",
    }
  }
}

export async function signOut(): Promise<void> {
  try {
    console.log("Starting logout process...")

    // Clear local storage first
    localStorage.removeItem("nexdatawork_onboarding")

    // Sign out from Supabase
    const { error } = await supabase.auth.signOut()

    if (error) {
      console.error("Supabase logout error:", error)
      throw error
    }

    console.log("Logout successful")
  } catch (err) {
    console.error("Logout error:", err)
    throw err
  }
}

export async function getCurrentUser() {
  try {
    // First check if we have a session
    const {
      data: { session },
      error: sessionError,
    } = await supabase.auth.getSession()

    if (sessionError) {
      console.error("Session error:", sessionError)
      return null
    }

    if (!session) {
      // No session exists, user is not logged in - this is normal
      return null
    }

    // If we have a session, get the user
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser()

    if (userError) {
      console.error("Get user error:", userError)
      return null
    }

    return user
  } catch (err) {
    console.error("Get user error:", err)
    return null
  }
}
