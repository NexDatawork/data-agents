"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { signIn, getCurrentUser } from "@/lib/auth"
import { OnboardingModal, type OnboardingData } from "@/components/onboarding-modal"
import { supabase } from "@/lib/supabase"
import Link from "next/link"
import { Separator } from "@/components/ui/separator"
import { BarChart3, X, Loader2 } from "lucide-react"
import { getOnboardingData } from "@/lib/onboarding-service"
import { useToast } from "@/hooks/use-toast"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [isMicrosoftLoading, setIsMicrosoftLoading] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [loginError, setLoginError] = useState("")
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const { toast } = useToast()

  // Check if user is already logged in
  useEffect(() => {
    const checkUser = async () => {
      try {
        setIsCheckingAuth(true)

        // Add a small delay to ensure logout has completed if user just logged out
        await new Promise((resolve) => setTimeout(resolve, 500))

        // Check for existing session first
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession()

        if (sessionError) {
          console.log("Session error:", sessionError)
          setIsCheckingAuth(false)
          return
        }

        if (!session) {
          console.log("No session found")
          setIsCheckingAuth(false)
          return
        }

        // If we have a session, get the user
        const user = await getCurrentUser()

        if (user) {
          console.log("User is authenticated, checking if first time or returning user")
          await handleUserRedirect(user)
          return
        }

        // No valid user, stay on login page
        setIsCheckingAuth(false)
      } catch (error) {
        console.log("Auth check error:", error)
        setIsCheckingAuth(false)
      }
    }

    checkUser()

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log("Auth state changed:", event, session?.user?.email)

      if (event === "SIGNED_IN" && session?.user) {
        console.log("Sign in detected, handling user redirect")
        // Add a small delay to ensure the session is fully established
        setTimeout(async () => {
          await handleUserRedirect(session.user)
        }, 1000)
      } else if (event === "SIGNED_OUT") {
        console.log("User signed out")
        setShowOnboarding(false)
        setIsCheckingAuth(false)
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  // Handle user redirect logic based on onboarding status
  const handleUserRedirect = async (user: any) => {
    try {
      console.log("handleUserRedirect called with user:", user.email)

      // Check if this is first time user or returning user using Supabase
      const onboardingResult = await getOnboardingData()
      const hasOnboardingData = onboardingResult.data !== null

      const hasLoggedInBefore = user.user_metadata?.has_logged_in_before === true
      const userCreatedAt = new Date(user.created_at)
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)
      const isNotBrandNewUser = userCreatedAt < fiveMinutesAgo

      console.log("User redirect check:", {
        hasOnboardingData,
        hasLoggedInBefore,
        isNotBrandNewUser,
        userCreatedAt: user.created_at,
      })

      // If user has onboarding data OR has logged in before OR is not brand new, go to dashboard
      if (hasOnboardingData || hasLoggedInBefore || isNotBrandNewUser) {
        console.log("Returning user detected, redirecting to dashboard")
        // Use window.location.replace instead of href to avoid back button issues
        window.location.replace("/dashboard")
      } else {
        console.log("First-time user detected, showing onboarding")
        setShowOnboarding(true)
        setIsCheckingAuth(false)
      }
    } catch (error) {
      console.error("Error in handleUserRedirect:", error)
      // Default to dashboard on error to prevent infinite loading
      console.log("Defaulting to dashboard due to error")
      window.location.replace("/dashboard")
    }
  }

  // Show loading while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-indigo-600 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600">Loading...</span>
        </div>
      </div>
    )
  }

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setLoginError("")

    try {
      const result = await signIn(email, password)

      if (result.success && result.user) {
        console.log("Login successful for user:", result.user.email)
        // Don't handle redirect here, let the auth state change listener handle it
      } else {
        setLoginError(result.error || "Login failed. Please check your credentials.")
        // Auto-focus to error message
        setTimeout(() => {
          const errorElement = document.querySelector("[data-error-message]")
          if (errorElement) {
            errorElement.scrollIntoView({ behavior: "smooth", block: "center" })
          }
        }, 100)
      }
    } catch (error) {
      setLoginError("An unexpected error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    try {
      setIsGoogleLoading(true)
      console.log("Google login initiated")

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/`,
          queryParams: {
            access_type: "offline",
            prompt: "consent",
          },
        },
      })

      if (error) {
        console.error("Google login error:", error)
        toast({
          title: "Login Error",
          description: error.message || "Failed to sign in with Google. Please try again.",
          variant: "destructive",
        })
        setIsGoogleLoading(false)
      } else {
        console.log("Google login initiated successfully")
        // Don't set loading to false here as the page will redirect
      }
    } catch (error) {
      console.error("Google login error:", error)
      toast({
        title: "Login Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      })
      setIsGoogleLoading(false)
    }
  }

  const handleMicrosoftLogin = async () => {
    try {
      setIsMicrosoftLoading(true)
      console.log("Microsoft login initiated")

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "azure",
        options: {
          redirectTo: `${window.location.origin}/`,
          scopes: "email profile",
        },
      })

      if (error) {
        console.error("Microsoft login error:", error)
        toast({
          title: "Login Error",
          description: error.message || "Failed to sign in with Microsoft. Please try again.",
          variant: "destructive",
        })
        setIsMicrosoftLoading(false)
      } else {
        console.log("Microsoft login initiated successfully")
        // Don't set loading to false here as the page will redirect
      }
    } catch (error) {
      console.error("Microsoft login error:", error)
      toast({
        title: "Login Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      })
      setIsMicrosoftLoading(false)
    }
  }

  const handleOnboardingComplete = async (onboardingData: OnboardingData) => {
    console.log("Onboarding completed, redirecting to main app with data:", onboardingData)

    // Store onboarding data in localStorage for backup
    localStorage.setItem("nexdatawork_onboarding", JSON.stringify(onboardingData))

    // Mark user as having completed onboarding in user metadata
    try {
      const user = await getCurrentUser()
      if (user) {
        // Update user metadata to mark onboarding as complete
        const { error } = await supabase.auth.updateUser({
          data: {
            ...user.user_metadata,
            has_logged_in_before: true,
            onboarding_completed: true,
            onboarding_completed_at: new Date().toISOString(),
          },
        })

        if (error) {
          console.error("Error updating user metadata:", error)
        } else {
          console.log("User metadata updated successfully")
        }
      }
    } catch (error) {
      console.log("Could not update user metadata:", error)
    }

    setShowOnboarding(false)
    // Redirect to main app
    window.location.replace("/dashboard")
  }

  const handleOnboardingClose = () => {
    console.log("Onboarding closed without completion")

    // Still mark user as having logged in before to prevent showing onboarding again
    const markUserAsReturning = async () => {
      try {
        const user = await getCurrentUser()
        if (user) {
          await supabase.auth.updateUser({
            data: {
              ...user.user_metadata,
              has_logged_in_before: true,
              onboarding_skipped: true,
              onboarding_skipped_at: new Date().toISOString(),
            },
          })
        }
      } catch (error) {
        console.log("Could not update user metadata:", error)
      }
    }

    markUserAsReturning()
    setShowOnboarding(false)
    // If user closes onboarding, still redirect to dashboard
    window.location.replace("/dashboard")
  }

  return (
    <>
      <div className="min-h-screen bg-white flex">
        {/* Left Panel - Login Form */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-8">
            {/* Logo and Header */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <span className="text-2xl font-semibold text-gray-900">NexDatawork</span>
              </div>
              <h1 className="font-bold text-2xl text-violet-600 bg-transparent">Your AI-Powered Data Agent</h1>
            </div>

            {/* Error Message */}
            {loginError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-error-message>
                <div className="flex items-start">
                  <X className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
                  <p className="text-sm text-red-600">{loginError}</p>
                </div>
              </div>
            )}

            {/* Login Form */}
            <div className="space-y-6">
              {/* Social Login Buttons - Featured */}
              <div className="space-y-3">
                <Button
                  onClick={handleGoogleLogin}
                  disabled={isGoogleLoading || isMicrosoftLoading}
                  className="w-full h-12 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition-all duration-200 shadow-sm"
                >
                  {isGoogleLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Signing in with Google...</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <svg className="h-5 w-5" viewBox="0 0 24 24">
                        <path
                          fill="#4285F4"
                          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        />
                        <path
                          fill="#34A853"
                          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        />
                        <path
                          fill="#FBBC04"
                          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        />
                        <path
                          fill="#EA4335"
                          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        />
                      </svg>
                      <span>Continue with Google</span>
                    </div>
                  )}
                </Button>

                <Button
                  onClick={handleMicrosoftLogin}
                  disabled={isGoogleLoading || isMicrosoftLoading}
                  className="w-full h-12 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition-all duration-200 shadow-sm"
                >
                  {isMicrosoftLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Signing in with Microsoft...</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z" />
                      </svg>
                      <span>Continue with Microsoft</span>
                    </div>
                  )}
                </Button>
              </div>

              <div className="relative">
                <Separator className="bg-gray-200" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="bg-white px-4 text-sm text-gray-500">Or continue with email</span>
                </div>
              </div>

              <form onSubmit={handleEmailLogin} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                    Email address
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter Your Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-12 border-gray-200 focus:border-primary focus:ring-primary"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                      Password
                    </Label>
                    <Link href="/forgot-password" className="text-sm text-primary hover:text-primary/80">
                      Forgot password?
                    </Link>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter Your Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-12 border-gray-200 focus:border-primary focus:ring-primary"
                    required
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="remember"
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <Label htmlFor="remember" className="text-sm text-gray-600">
                    Remember me
                  </Label>
                </div>

                <Button
                  type="submit"
                  disabled={isLoading || isGoogleLoading || isMicrosoftLoading}
                  className="w-full h-12 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white font-medium transition-all duration-200"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Signing in...
                    </div>
                  ) : (
                    "Sign in"
                  )}
                </Button>
              </form>

              <p className="text-center text-sm text-gray-600">
                Don't have an account?{" "}
                <Link href="/signup" className="text-primary hover:text-primary/80 font-medium">
                  Sign up
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel - Static Purple/Blue Design */}
        <div className="hidden md:flex flex-1 items-center justify-center p-8 relative overflow-hidden bg-gradient-to-br from-purple-600 to-blue-600">
          {/* Main Welcome Text */}
          <div className="relative z-10 text-center space-y-4">
            <h1 className="text-5xl font-bold text-white leading-tight">
              Welcome to
              <br />
              NexDatawork
            </h1>
            <div className="text-xl text-white/90 font-medium font-sans text-center">
              <div>Analyze Your Data</div>
              <div>Faster and Smarter</div>
            </div>
          </div>
        </div>

        {/* Mobile-friendly version that shows on small screens */}
        <div className="md:hidden w-full bg-gradient-to-r from-purple-600 to-blue-600 py-8 px-4">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-white">Welcome to NexDatawork</h2>
            <p className="text-white/90">Better experience in desktop</p>
          </div>
        </div>
      </div>

      {/* Onboarding Modal */}
      <OnboardingModal isOpen={showOnboarding} onComplete={handleOnboardingComplete} onClose={handleOnboardingClose} />
    </>
  )
}
