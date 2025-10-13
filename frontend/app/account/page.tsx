"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TopBar } from "@/components/top-bar"
import {
  ArrowLeft,
  Save,
  User,
  Mail,
  Calendar,
  MapPin,
  Briefcase,
  Edit3,
  Phone,
  Globe,
  Target,
  Database,
} from "lucide-react"
import { getCurrentUser } from "@/lib/auth"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { getOnboardingData, saveOnboardingData } from "@/lib/onboarding-service"
import { getUserProfile, updateUserProfile, type UserProfile, type ProfileUpdateData } from "@/lib/profile-service"
import type { OnboardingData } from "@/components/onboarding-modal"

export default function AccountPage() {
  const [user, setUser] = useState<any>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [isEditingPreferences, setIsEditingPreferences] = useState(false)
  const [isSavingPreferences, setIsSavingPreferences] = useState(false)
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    bio: "",
    location: "",
    company: "",
    role: "",
    phone: "",
    website: "",
  })
  const [preferencesData, setPreferencesData] = useState<OnboardingData>({
    firstName: "",
    role: "",
    goals: [],
    customGoal: "",
    dataTypes: [],
    dataLocations: [],
  })
  const { toast } = useToast()
  const router = useRouter()

  // Available options for preferences
  const roleOptions = [
    { value: "ceo", label: "CEO" },
    { value: "product", label: "Product Manager" },
    { value: "analyst", label: "Data Analyst" },
    { value: "marketing", label: "Marketing Professional" },
    { value: "operations", label: "Operations Manager" },
    { value: "other", label: "Other" },
  ]

  const goalOptions = [
    "Improve decision making",
    "Increase revenue",
    "Reduce costs",
    "Better understand customers",
    "Optimize operations",
    "Identify trends",
    "Automate reporting",
    "Risk management",
  ]

  const dataTypeOptions = [
    "Sales data",
    "Customer data",
    "Financial data",
    "Marketing data",
    "Operational data",
    "Survey data",
    "Web analytics",
    "Social media data",
  ]

  const dataLocationOptions = [
    "Excel/CSV files",
    "Google Sheets",
    "Database",
    "CRM system",
    "Cloud storage",
    "Email attachments",
    "Internal systems",
    "Third-party APIs",
  ]

  useEffect(() => {
    loadUserData()
  }, [])

  const loadUserData = async () => {
    try {
      setIsLoading(true)

      // Load user data
      const currentUser = await getCurrentUser()
      setUser(currentUser)

      // Load profile data from Supabase
      const profileResult = await getUserProfile()
      if (profileResult.error) {
        console.error("Error loading profile:", profileResult.error)
        toast({
          title: "Error loading profile",
          description: profileResult.error,
          variant: "destructive",
        })
      } else {
        setProfile(profileResult.data)
      }

      // Load onboarding data from Supabase
      const onboardingResult = await getOnboardingData()
      if (onboardingResult.data) {
        setOnboardingData(onboardingResult.data)
        // Set preferences data for editing
        setPreferencesData(onboardingResult.data)
      } else {
        // Initialize with empty data if no preferences exist
        setPreferencesData({
          firstName: currentUser?.user_metadata?.first_name || "",
          role: "",
          goals: [],
          customGoal: "",
          dataTypes: [],
          dataLocations: [],
        })
      }

      // Populate form data with priority: profile data > onboarding data > user metadata
      setFormData({
        first_name:
          profileResult.data?.first_name ||
          onboardingResult.data?.firstName ||
          currentUser?.user_metadata?.first_name ||
          "",
        last_name:
          profileResult.data?.last_name ||
          onboardingResult.data?.lastName ||
          currentUser?.user_metadata?.last_name ||
          "",
        email: currentUser?.email || "",
        bio: profileResult.data?.bio || currentUser?.user_metadata?.bio || "",
        location: profileResult.data?.location || currentUser?.user_metadata?.location || "",
        company:
          profileResult.data?.company || onboardingResult.data?.company || currentUser?.user_metadata?.company || "",
        role: profileResult.data?.role || onboardingResult.data?.role || currentUser?.user_metadata?.role || "",
        phone: profileResult.data?.phone || currentUser?.user_metadata?.phone || "",
        website: profileResult.data?.website || currentUser?.user_metadata?.website || "",
      })
    } catch (error) {
      console.error("Error loading user data:", error)
      toast({
        title: "Error loading account data",
        description: "Could not load your account information. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveProfile = async () => {
    try {
      setIsSaving(true)

      // Prepare profile update data
      const profileUpdateData: ProfileUpdateData = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        bio: formData.bio.trim(),
        location: formData.location.trim(),
        company: formData.company.trim(),
        role: formData.role.trim(),
        phone: formData.phone.trim(),
        website: formData.website.trim(),
      }

      // Update profile in Supabase
      const result = await updateUserProfile(profileUpdateData)

      if (result.error) {
        throw new Error(result.error)
      }

      // Update local state
      setProfile(result.data)

      toast({
        title: "Profile updated successfully",
        description: "Your account information has been saved.",
      })

      setIsEditingProfile(false)
    } catch (error) {
      console.error("Error saving profile:", error)
      toast({
        title: "Error saving profile",
        description: error instanceof Error ? error.message : "Could not save your changes. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleSavePreferences = async () => {
    try {
      setIsSavingPreferences(true)

      // Save preferences to onboarding_data table
      const result = await saveOnboardingData(preferencesData)

      if (!result.success) {
        throw new Error(result.error || "Failed to save preferences")
      }

      // Update local state
      setOnboardingData(preferencesData)

      toast({
        title: "Preferences updated successfully",
        description: "Your data analysis preferences have been saved.",
      })

      setIsEditingPreferences(false)
    } catch (error) {
      console.error("Error saving preferences:", error)
      toast({
        title: "Error saving preferences",
        description: error instanceof Error ? error.message : "Could not save your preferences. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSavingPreferences(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handlePreferenceChange = (field: keyof OnboardingData, value: any) => {
    setPreferencesData((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleGoalToggle = (goal: string, checked: boolean) => {
    setPreferencesData((prev) => ({
      ...prev,
      goals: checked ? [...prev.goals, goal] : prev.goals.filter((g) => g !== goal),
    }))
  }

  const handleDataTypeToggle = (dataType: string, checked: boolean) => {
    setPreferencesData((prev) => ({
      ...prev,
      dataTypes: checked ? [...prev.dataTypes, dataType] : prev.dataTypes.filter((dt) => dt !== dataType),
    }))
  }

  const handleDataLocationToggle = (location: string, checked: boolean) => {
    setPreferencesData((prev) => ({
      ...prev,
      dataLocations: checked ? [...prev.dataLocations, location] : prev.dataLocations.filter((dl) => dl !== location),
    }))
  }

  const handleCancelProfile = () => {
    // Reset form data to original values
    setFormData({
      first_name: profile?.first_name || onboardingData?.firstName || user?.user_metadata?.first_name || "",
      last_name: profile?.last_name || onboardingData?.lastName || user?.user_metadata?.last_name || "",
      email: user?.email || "",
      bio: profile?.bio || user?.user_metadata?.bio || "",
      location: profile?.location || user?.user_metadata?.location || "",
      company: profile?.company || onboardingData?.company || user?.user_metadata?.company || "",
      role: profile?.role || onboardingData?.role || user?.user_metadata?.role || "",
      phone: profile?.phone || user?.user_metadata?.phone || "",
      website: profile?.website || user?.user_metadata?.website || "",
    })
    setIsEditingProfile(false)
  }

  const handleCancelPreferences = () => {
    // Reset preferences data to original database values
    if (onboardingData) {
      setPreferencesData(onboardingData)
    } else {
      setPreferencesData({
        firstName: user?.user_metadata?.first_name || "",
        role: "",
        goals: [],
        customGoal: "",
        dataTypes: [],
        dataLocations: [],
      })
    }
    setIsEditingPreferences(false)
  }

  const getUserDisplayName = () => {
    if (formData.first_name && formData.last_name) {
      return `${formData.first_name} ${formData.last_name}`
    }
    if (formData.first_name) {
      return formData.first_name
    }
    return user?.email?.split("@")[0] || "User"
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

  const getRoleLabel = (role: string) => {
    const roleLabels = {
      ceo: "CEO",
      product: "Product Manager",
      analyst: "Data Analyst",
      marketing: "Marketing Professional",
      operations: "Operations Manager",
      other: "Other",
    }
    return roleLabels[role as keyof typeof roleLabels] || role
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col bg-[#f8f9fc]">
        <TopBar title="My Account" />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-gray-600">Loading account information...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#f8f9fc]">
      <TopBar title="My Account" />

      <div className="flex-1 p-6 max-w-4xl mx-auto w-full">
        {/* Back Button */}
        <Button variant="ghost" onClick={() => router.push("/dashboard")} className="mb-6 hover:bg-white">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>

        <div className="grid gap-6">
          {/* Profile Header Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Avatar className="h-20 w-20">
                    <AvatarImage src="/placeholder.svg?height=80&width=80" alt={getUserDisplayName()} />
                    <AvatarFallback className="bg-violet-600 text-white text-xl font-medium">
                      {getUserInitials()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-2xl">{getUserDisplayName()}</CardTitle>
                    <CardDescription className="text-base mt-1">
                      {formData.role && getRoleLabel(formData.role)}
                      {formData.company && ` at ${formData.company}`}
                    </CardDescription>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        Active
                      </Badge>
                      <Badge variant="outline">
                        Member since {new Date(user?.created_at || Date.now()).toLocaleDateString()}
                      </Badge>
                      {profile && (
                        <Badge variant="outline" className="bg-blue-50 text-blue-700">
                          Profile Complete
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <Button
                  variant={isEditingProfile ? "default" : "outline"}
                  onClick={() => setIsEditingProfile(!isEditingProfile)}
                >
                  <Edit3 className="h-4 w-4 mr-2" />
                  {isEditingProfile ? "Cancel" : "Edit Profile"}
                </Button>
              </div>
            </CardHeader>
          </Card>

          {/* Account Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Account Information
              </CardTitle>
              <CardDescription>
                Manage your personal information and preferences
                {profile && (
                  <span className="text-green-600 ml-2">
                    • Last updated: {new Date(profile.updated_at || "").toLocaleDateString()}
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">First Name</Label>
                  <Input
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => handleInputChange("first_name", e.target.value)}
                    disabled={!isEditingProfile}
                    className={!isEditingProfile ? "bg-gray-50" : ""}
                    placeholder="Enter your first name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">Last Name</Label>
                  <Input
                    id="last_name"
                    value={formData.last_name}
                    onChange={(e) => handleInputChange("last_name", e.target.value)}
                    disabled={!isEditingProfile}
                    className={!isEditingProfile ? "bg-gray-50" : ""}
                    placeholder="Enter your last name"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email Address
                </Label>
                <Input id="email" type="email" value={formData.email} disabled className="bg-gray-50" />
                <p className="text-sm text-gray-500">
                  Email address cannot be changed. Contact support team@nexdatawork.io if you need to update this.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company" className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4" />
                    Company
                  </Label>
                  <Input
                    id="company"
                    value={formData.company}
                    onChange={(e) => handleInputChange("company", e.target.value)}
                    disabled={!isEditingProfile}
                    className={!isEditingProfile ? "bg-gray-50" : ""}
                    placeholder="Your company name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={formData.role}
                    onChange={(e) => handleInputChange("role", e.target.value)}
                    disabled={!isEditingProfile}
                    className={!isEditingProfile ? "bg-gray-50" : ""}
                    placeholder="Your job title or role"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="location" className="flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    Location
                  </Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => handleInputChange("location", e.target.value)}
                    disabled={!isEditingProfile}
                    className={!isEditingProfile ? "bg-gray-50" : ""}
                    placeholder="City, Country"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone" className="flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    Phone Number
                  </Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => handleInputChange("phone", e.target.value)}
                    disabled={!isEditingProfile}
                    className={!isEditingProfile ? "bg-gray-50" : ""}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="website" className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  Website
                </Label>
                <Input
                  id="website"
                  value={formData.website}
                  onChange={(e) => handleInputChange("website", e.target.value)}
                  disabled={!isEditingProfile}
                  className={!isEditingProfile ? "bg-gray-50" : ""}
                  placeholder="https://yourwebsite.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  value={formData.bio}
                  onChange={(e) => handleInputChange("bio", e.target.value)}
                  disabled={!isEditingProfile}
                  className={!isEditingProfile ? "bg-gray-50" : ""}
                  placeholder="Tell us about yourself..."
                  rows={3}
                />
              </div>

              {isEditingProfile && (
                <div className="flex gap-3 pt-4">
                  <Button onClick={handleSaveProfile} disabled={isSaving}>
                    <Save className="h-4 w-4 mr-2" />
                    {isSaving ? "Saving..." : "Save Changes"}
                  </Button>
                  <Button variant="outline" onClick={handleCancelProfile}>
                    Cancel
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data Analysis Preferences */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Data Analysis Preferences
                  </CardTitle>
                  <CardDescription>
                    Your preferences for data analysis and insights
                    {onboardingData && <span className="text-green-600 ml-2">• Configured</span>}
                  </CardDescription>
                </div>
                <Button
                  variant={isEditingPreferences ? "default" : "outline"}
                  onClick={() => setIsEditingPreferences(!isEditingPreferences)}
                >
                  <Edit3 className="h-4 w-4 mr-2" />
                  {isEditingPreferences ? "Cancel" : "Edit Preferences"}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {isEditingPreferences ? (
                <>
                  {/* Editable Preferences Form */}
                  <div className="space-y-2">
                    <Label htmlFor="pref_firstName">First Name</Label>
                    <Input
                      id="pref_firstName"
                      value={preferencesData.firstName}
                      onChange={(e) => handlePreferenceChange("firstName", e.target.value)}
                      placeholder="Enter your first name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="pref_role">Role</Label>
                    <Select
                      value={preferencesData.role}
                      onValueChange={(value) => handlePreferenceChange("role", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select your role" />
                      </SelectTrigger>
                      <SelectContent>
                        {roleOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-3">
                    <Label>Goals (select all that apply)</Label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {goalOptions.map((goal) => (
                        <div key={goal} className="flex items-center space-x-2">
                          <Checkbox
                            id={`goal-${goal}`}
                            checked={preferencesData.goals.includes(goal)}
                            onCheckedChange={(checked) => handleGoalToggle(goal, checked as boolean)}
                          />
                          <Label htmlFor={`goal-${goal}`} className="text-sm font-normal">
                            {goal}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="customGoal">Custom Goal (optional)</Label>
                    <Input
                      id="customGoal"
                      value={preferencesData.customGoal}
                      onChange={(e) => handlePreferenceChange("customGoal", e.target.value)}
                      placeholder="Describe any other goals..."
                    />
                  </div>

                  <div className="space-y-3">
                    <Label>Data Types (select all that apply)</Label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {dataTypeOptions.map((dataType) => (
                        <div key={dataType} className="flex items-center space-x-2">
                          <Checkbox
                            id={`datatype-${dataType}`}
                            checked={preferencesData.dataTypes.includes(dataType)}
                            onCheckedChange={(checked) => handleDataTypeToggle(dataType, checked as boolean)}
                          />
                          <Label htmlFor={`datatype-${dataType}`} className="text-sm font-normal">
                            {dataType}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Data Locations (select all that apply)</Label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {dataLocationOptions.map((location) => (
                        <div key={location} className="flex items-center space-x-2">
                          <Checkbox
                            id={`location-${location}`}
                            checked={preferencesData.dataLocations.includes(location)}
                            onCheckedChange={(checked) => handleDataLocationToggle(location, checked as boolean)}
                          />
                          <Label htmlFor={`location-${location}`} className="text-sm font-normal">
                            {location}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-3 pt-4">
                    <Button onClick={handleSavePreferences} disabled={isSavingPreferences}>
                      <Save className="h-4 w-4 mr-2" />
                      {isSavingPreferences ? "Saving..." : "Save Preferences"}
                    </Button>
                    <Button variant="outline" onClick={handleCancelPreferences}>
                      Cancel
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  {/* Display Current Preferences */}
                  {onboardingData ? (
                    <>
                      <div>
                        <Label className="text-sm font-medium text-gray-700">Role</Label>
                        <p className="text-sm text-gray-900 mt-1">{getRoleLabel(onboardingData.role)}</p>
                      </div>

                      {onboardingData.goals && onboardingData.goals.length > 0 && (
                        <div>
                          <Label className="text-sm font-medium text-gray-700">Goals</Label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {onboardingData.goals.map((goal, index) => (
                              <Badge key={index} variant="secondary">
                                {goal}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {onboardingData.customGoal && (
                        <div>
                          <Label className="text-sm font-medium text-gray-700">Custom Goal</Label>
                          <p className="text-sm text-gray-900 mt-1">{onboardingData.customGoal}</p>
                        </div>
                      )}

                      {onboardingData.dataTypes && onboardingData.dataTypes.length > 0 && (
                        <div>
                          <Label className="text-sm font-medium text-gray-700">Data Types</Label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {onboardingData.dataTypes.map((type, index) => (
                              <Badge key={index} variant="outline">
                                {type}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {onboardingData.dataLocations && onboardingData.dataLocations.length > 0 && (
                        <div>
                          <Label className="text-sm font-medium text-gray-700">Data Locations</Label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {onboardingData.dataLocations.map((location, index) => (
                              <Badge key={index} variant="outline">
                                {location}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 mb-4">No preferences configured yet</p>
                      <Button onClick={() => setIsEditingPreferences(true)}>Set Up Preferences</Button>
                    </div>
                  )}

                  <Separator />
                  <p className="text-sm text-gray-500">
                    These preferences help personalize your data analysis experience and improve the relevance of
                    insights generated for you.
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* Account Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Account Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">0</div>
                  <div className="text-sm text-gray-600">Files Analyzed</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">0</div>
                  <div className="text-sm text-gray-600">Insights Generated</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">0</div>
                  <div className="text-sm text-gray-600">Chat Messages</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
