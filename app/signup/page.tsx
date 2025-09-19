"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { signUp, signOut } from "@/lib/auth"
import { SignupSuccessModal } from "@/components/signup-success-modal"
import Link from "next/link"
import { BarChart3, X, Eye, EyeOff, Check } from "lucide-react"

interface PasswordRequirement {
  label: string
  test: (password: string) => boolean
}

const passwordRequirements: PasswordRequirement[] = [
  { label: "At least 8 characters", test: (pwd) => pwd.length >= 8 },
  { label: "Contains lowercase letter", test: (pwd) => /[a-z]/.test(pwd) },
  { label: "Contains uppercase letter", test: (pwd) => /[A-Z]/.test(pwd) },
  { label: "Contains number", test: (pwd) => /\d/.test(pwd) },
  { label: "Contains symbol", test: (pwd) => /[!_@#$%^&*(),.?":{}|<>]/.test(pwd) },
]

export default function SignupPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [username, setUsername] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [signupError, setSignupError] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [showPasswordRequirements, setShowPasswordRequirements] = useState(false)

  const errorRef = useRef<HTMLDivElement>(null)

  const isPasswordValid = passwordRequirements.every((req) => req.test(password))

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setSignupError("")

    // Validate username
    if (!username.trim()) {
      setSignupError("Please enter your username")
      setIsLoading(false)
      setTimeout(() => errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100)
      return
    }

    // Validate email
    if (!email.trim()) {
      setSignupError("Please enter your email address")
      setIsLoading(false)
      setTimeout(() => errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100)
      return
    }

    // Validate password requirements
    if (!isPasswordValid) {
      setSignupError("Password does not meet the requirements")
      setIsLoading(false)
      setTimeout(() => errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100)
      return
    }

    // Validate passwords match
    if (password !== confirmPassword) {
      setSignupError("Passwords do not match")
      setIsLoading(false)
      setTimeout(() => errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100)
      return
    }

    try {
      const result = await signUp({ email, password, username })

      if (result.success) {
        console.log("Signup successful, logging user out immediately")

        // Log user out immediately after successful signup
        try {
          await signOut()
          console.log("User logged out after signup")
        } catch (logoutError) {
          console.error("Error logging out after signup:", logoutError)
        }

        // Show success modal
        setShowSuccessModal(true)
      } else {
        setSignupError(result.error || "Signup failed. Please try again.")
        // Auto-focus to error message
        setTimeout(() => errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100)
      }
    } catch (error) {
      setSignupError("An unexpected error occurred. Please try again.")
      setTimeout(() => errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuccessRedirect = async () => {
    console.log("Success redirect triggered, logging user out before redirect")

    // Log user out before redirecting
    try {
      await signOut()
      console.log("User logged out before redirect")
    } catch (logoutError) {
      console.error("Error logging out before redirect:", logoutError)
    }

    // Redirect to login page
    window.location.href = "/"
  }

  const handlePasswordChange = (value: string) => {
    setPassword(value)
    setShowPasswordRequirements(value.length > 0)
    // Clear error when user starts typing
    if (signupError) setSignupError("")
  }

  const handleInputChange = (field: string, value: string) => {
    if (field === "username") setUsername(value)
    if (field === "email") setEmail(value)
    if (field === "confirmPassword") setConfirmPassword(value)

    // Clear error when user starts typing
    if (signupError) setSignupError("")
  }

  return (
    <>
      <div className="min-h-screen bg-white flex">
        {/* Left Panel - Signup Form */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-8">
            {/* Logo and Header */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full flex items-center justify-center bg-violet-600">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <span className="text-2xl font-semibold text-violet-700">NexDatawork</span>
              </div>
              <div>
                <h1 className="font-bold text-2xl text-violet-600 bg-transparent">Create Your Account</h1>
                <p className="text-gray-600 mt-2">Join thousands of users analyzing data with AI</p>
              </div>
            </div>

            {/* Error Message */}
            {signupError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-error-message ref={errorRef}>
                <div className="flex items-start">
                  <X className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
                  <p className="text-sm text-red-600">{signupError}</p>
                </div>
              </div>
            )}

            {/* Signup Form */}
            <div className="space-y-6">
              <form onSubmit={handleSignup} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-medium text-gray-700">
                    Username
                  </Label>
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => handleInputChange("username", e.target.value)}
                    className="h-12 border-gray-200 focus:border-primary focus:ring-primary"
                    required
                    disabled={isLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                    Email address
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => handleInputChange("email", e.target.value)}
                    className="h-12 border-gray-200 focus:border-primary focus:ring-primary"
                    required
                    disabled={isLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                    Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Create a strong password"
                      value={password}
                      onChange={(e) => handlePasswordChange(e.target.value)}
                      className="h-12 border-gray-200 focus:border-primary focus:ring-primary pr-12"
                      required
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                      disabled={isLoading}
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>

                  {/* Password Requirements */}
                  {showPasswordRequirements && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-md border">
                      <p className="text-sm font-medium text-gray-700 mb-2">Password requirements:</p>
                      <div className="space-y-1">
                        {passwordRequirements.map((req, index) => {
                          const isValid = req.test(password)
                          return (
                            <div key={index} className="flex items-center gap-2 text-sm">
                              {isValid ? (
                                <Check className="w-4 h-4 text-green-600" />
                              ) : (
                                <X className="w-4 h-4 text-red-500" />
                              )}
                              <span className={isValid ? "text-green-600" : "text-red-500"}>{req.label}</span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                    Confirm Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm your password"
                      value={confirmPassword}
                      onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                      className="h-12 border-gray-200 focus:border-primary focus:ring-primary pr-12"
                      required
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                      disabled={isLoading}
                    >
                      {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-start space-x-2">
                  <input
                    type="checkbox"
                    id="terms"
                    className="rounded border-gray-300 text-primary focus:ring-primary mt-1"
                    required
                    disabled={isLoading}
                  />
                  <Label htmlFor="terms" className="text-sm text-gray-600 leading-relaxed">
                    I agree to the{" "}
                    <Link href="/terms" className="text-primary hover:text-primary/80 underline">
                      Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link href="/privacy" className="text-primary hover:text-primary/80 underline">
                      Privacy Policy
                    </Link>
                  </Label>
                </div>

                <Button
                  type="submit"
                  disabled={isLoading || !isPasswordValid}
                  className="w-full h-12 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Creating account...
                    </div>
                  ) : (
                    "Create account"
                  )}
                </Button>
              </form>

              <p className="text-center text-sm text-gray-600">
                Already have an account?{" "}
                <Link href="/" className="text-primary hover:text-primary/80 font-medium">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel - Enhanced Animated Dots */}
        <div className="flex-1 flex items-center justify-center p-8 relative overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100">
          {/* Enhanced Animated Round Dots */}
          <div className="absolute inset-0 overflow-hidden">
            {/* Small Floating Orbs with High Transparency */}
            {Array.from({ length: 8 }).map((_, i) => {
              const positions = [
                { top: "10%", left: "10%" },
                { top: "15%", right: "15%" },
                { top: "25%", left: "8%" },
                { top: "35%", right: "12%" },
                { bottom: "20%", left: "12%" },
                { bottom: "30%", left: "18%" },
                { bottom: "15%", right: "18%" },
                { bottom: "25%", right: "10%" },
              ]

              return (
                <div
                  key={`orb-${i}`}
                  className="absolute animate-pulse"
                  style={{
                    ...positions[i],
                    animationDelay: `${i * 800}ms`,
                    animationDuration: `${4000 + i * 500}ms`,
                  }}
                >
                  <div
                    className="relative bg-gradient-to-br from-violet-400 via-purple-500 to-pink-500 rounded-full shadow-sm opacity-20"
                    style={{
                      width: `${8 + i * 2}px`,
                      height: `${8 + i * 2}px`,
                      filter: "blur(0.5px)",
                      boxShadow: `0 0 ${8 + i * 2}px rgba(139, 92, 246, 0.15)`,
                    }}
                  >
                    <div className="absolute inset-1 bg-gradient-to-br from-white/20 to-transparent rounded-full" />
                  </div>
                </div>
              )
            })}

            {/* Floating Particles */}
            {Array.from({ length: 25 }).map((_, i) => {
              const isLeftSide = i % 2 === 0
              const isTopHalf = i < 12

              return (
                <div
                  key={`particle-${i}`}
                  className="absolute rounded-full opacity-40"
                  style={{
                    width: `${Math.random() * 6 + 2}px`,
                    height: `${Math.random() * 6 + 2}px`,
                    background: `linear-gradient(45deg, ${
                      ["#8b5cf6", "#a855f7", "#ec4899", "#f59e0b", "#06b6d4"][Math.floor(Math.random() * 5)]
                    }, ${["#6366f1", "#8b5cf6", "#d946ef", "#f97316", "#0ea5e9"][Math.floor(Math.random() * 5)]})`,
                    [isTopHalf ? "top" : "bottom"]: `${Math.random() * 35 + (isTopHalf ? 5 : 5)}%`,
                    [isLeftSide ? "left" : "right"]: `${Math.random() * 30 + 5}%`,
                    animation: `floatUpDown ${3000 + Math.random() * 4000}ms ease-in-out infinite`,
                    animationDelay: `${Math.random() * 5000}ms`,
                    filter: "blur(0.5px)",
                  }}
                />
              )
            })}

            {/* Pulsing Rings */}
            {Array.from({ length: 4 }).map((_, i) => {
              const ringPositions = [
                { top: "12%", left: "12%" },
                { top: "18%", right: "18%" },
                { bottom: "18%", left: "18%" },
                { bottom: "12%", right: "12%" },
              ]

              return (
                <div key={`ring-${i}`} className="absolute" style={ringPositions[i]}>
                  <div
                    className="border-2 border-violet-300 rounded-full animate-ping opacity-30"
                    style={{
                      width: `${30 + i * 10}px`,
                      height: `${30 + i * 10}px`,
                      animationDuration: `${2000 + i * 1000}ms`,
                      animationDelay: `${i * 500}ms`,
                    }}
                  />
                </div>
              )
            })}

            {/* Morphing Blobs */}
            {Array.from({ length: 3 }).map((_, i) => {
              const blobPositions = [
                { top: "8%", left: "25%" },
                { bottom: "12%", left: "8%" },
                { top: "25%", right: "8%" },
              ]

              return (
                <div key={`blob-${i}`} className="absolute opacity-20" style={blobPositions[i]}>
                  <div
                    className="bg-gradient-to-br from-purple-400 to-pink-400 rounded-full"
                    style={{
                      width: `${15 + i * 5}px`,
                      height: `${15 + i * 5}px`,
                      animation: `morphBlob ${4000 + i * 1000}ms ease-in-out infinite`,
                      animationDelay: `${i * 1500}ms`,
                      filter: "blur(1px)",
                    }}
                  />
                </div>
              )
            })}
          </div>

          {/* Main Welcome Text */}
          <div className="relative z-10 text-center">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text leading-tight text-violet-700">
              Join
              <br />
              NexDatawork
            </h1>
            <p className="text-lg text-gray-600 mt-4">Start your data analysis journey today</p>
          </div>

          {/* Custom CSS for animations */}
          <style jsx>{`
            @keyframes floatUpDown {
              0%, 100% { transform: translateY(0px) rotate(0deg); }
              25% { transform: translateY(-10px) rotate(90deg); }
              50% { transform: translateY(-5px) rotate(180deg); }
              75% { transform: translateY(-15px) rotate(270deg); }
            }
            
            @keyframes morphBlob {
              0%, 100% { 
                transform: scale(1) rotate(0deg);
                border-radius: 50%;
              }
              25% { 
                transform: scale(1.2) rotate(90deg);
                border-radius: 60% 40% 30% 70%;
              }
              50% { 
                transform: scale(0.8) rotate(180deg);
                border-radius: 30% 60% 70% 40%;
              }
              75% { 
                transform: scale(1.1) rotate(270deg);
                border-radius: 40% 30% 60% 70%;
              }
            }
          `}</style>
        </div>
      </div>

      {/* Signup Success Modal */}
      <SignupSuccessModal
        isOpen={showSuccessModal}
        onRedirect={handleSuccessRedirect}
        onClose={() => setShowSuccessModal(false)}
      />
    </>
  )
}
