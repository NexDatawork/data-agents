"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Settings, User, LogOut, ChevronDown, Loader2 } from "lucide-react"
import { signOut, getCurrentUser } from "@/lib/auth"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"

interface TopBarProps {
  title?: string
}

export function TopBar({ title = "Dashboard" }: TopBarProps) {
  const [user, setUser] = useState<any>(null)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const router = useRouter()

  useEffect(() => {
    loadUser()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  const loadUser = async () => {
    try {
      const currentUser = await getCurrentUser()
      if (currentUser) {
        setUser(currentUser)
      } else {
        // User is not authenticated - this is normal, not an error
        setUser(null)
      }
    } catch (error) {
      console.error("Error loading user:", error)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true)
      setIsDropdownOpen(false)
      console.log("Logging out user...")

      // Clear any local storage data
      localStorage.removeItem("nexdatawork_onboarding")

      // Sign out the user
      await signOut()

      console.log("Logout successful, redirecting to homepage...")

      // Redirect to homepage after successful logout
      window.location.href = "/"
    } catch (error) {
      console.error("Logout error:", error)
      setIsLoggingOut(false)

      toast({
        title: "Logout failed",
        description: "There was an error signing you out. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleProfileClick = () => {
    setIsDropdownOpen(false)
    router.push("/account")
  }

  const handleSettingsClick = () => {
    router.push("/settings")
  }

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen)
  }

  const getUserDisplayName = () => {
    if (!user) return "User"

    return (
      user.user_metadata?.display_name ||
      user.user_metadata?.username ||
      user.user_metadata?.full_name ||
      user.email?.split("@")[0] ||
      "User"
    )
  }

  const getUserInitials = () => {
    const displayName = getUserDisplayName()
    return displayName
      .split(" ")
      .map((name: string) => name[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const getUserEmail = () => {
    return user?.email || "user@example.com"
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">Welcome to NexDatawork</span>
        </div>
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" onClick={() => (window.location.href = "/")}>
            Sign In
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
      <div className="flex items-center space-x-4"></div>

      <div className="flex items-center space-x-4">
        {/* Settings */}
        <Button variant="ghost" size="sm" onClick={handleSettingsClick}>
          <Settings className="h-5 w-5" />
        </Button>

        {/* User Menu Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={toggleDropdown}
            className="flex items-center space-x-2 hover:bg-gray-100 transition-colors duration-200 p-2 rounded-md"
            disabled={isLoggingOut}
          >
            <Avatar className="h-8 w-8">
              <AvatarImage src="/placeholder.svg?height=32&width=32" alt={getUserDisplayName()} />
              <AvatarFallback className="bg-violet-600 text-white text-sm font-medium">
                {getUserInitials()}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col items-start">
              <span className="text-sm font-medium text-gray-900">{getUserDisplayName()}</span>
              <span className="text-xs text-gray-500">{getUserEmail()}</span>
            </div>
            <ChevronDown
              className={`h-4 w-4 text-gray-500 transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""}`}
            />
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-50">
              {/* User Info Header */}
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="text-sm font-medium text-gray-900">{getUserDisplayName()}</p>
                <p className="text-xs text-gray-500">{getUserEmail()}</p>
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <button
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  onClick={handleProfileClick}
                >
                  <User className="mr-3 h-4 w-4" />
                  My Account
                </button>

                <button
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  onClick={() => {
                    setIsDropdownOpen(false)
                    handleSettingsClick()
                  }}
                >
                  <Settings className="mr-3 h-4 w-4" />
                  Settings
                </button>

                <div className="border-t border-gray-100 my-1"></div>

                <button
                  onClick={handleLogout}
                  disabled={isLoggingOut}
                  className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                >
                  {isLoggingOut ? (
                    <>
                      <Loader2 className="mr-3 h-4 w-4 animate-spin" />
                      Logging out...
                    </>
                  ) : (
                    <>
                      <LogOut className="mr-3 h-4 w-4" />
                      Log out
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
