"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import {
  ChevronRight,
  ChevronLeft,
  User,
  Target,
  Database,
  Sparkles,
  CheckCircle,
  Briefcase,
  TrendingUp,
  Users,
  Settings,
  BarChart3,
  FileSpreadsheet,
  Cloud,
  HardDrive,
  Globe,
  Loader2,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { saveOnboardingData } from "@/lib/onboarding-service"
import { useToast } from "@/hooks/use-toast"

interface OnboardingModalProps {
  isOpen: boolean
  onComplete: (data: OnboardingData) => void
  onClose?: () => void
}

export interface OnboardingData {
  firstName: string
  role: string
  goals: string[]
  customGoal: string
  dataTypes: string[]
  dataLocations: string[]
}

const roles = [
  { id: "ceo", label: "CEO", icon: Briefcase },
  { id: "product", label: "Product Manager", icon: Target },
  { id: "analyst", label: "Data Analyst", icon: BarChart3 },
  { id: "marketing", label: "Marketing", icon: TrendingUp },
  { id: "operations", label: "Operations", icon: Settings },
  { id: "other", label: "Other", icon: Users },
]

const goals = [
  "Summarize messy CSVs",
  "Analyze sales data",
  "Track customer behavior",
  "Monitor KPIs",
  "Generate reports",
  "Identify trends",
  "Clean data",
  "Create dashboards",
]

const dataTypes = [
  "Sales data",
  "Customer data",
  "Financial data",
  "Marketing data",
  "Operational data",
  "Survey responses",
  "Web analytics",
  "Other",
]

const dataLocations = [
  { id: "csv", label: "CSV files", icon: FileSpreadsheet },
  { id: "sheets", label: "Google Sheets", icon: Cloud },
  { id: "excel", label: "Excel files", icon: FileSpreadsheet },
  { id: "database", label: "Database", icon: HardDrive },
  { id: "api", label: "APIs", icon: Globe },
  { id: "other", label: "Other sources", icon: Database },
]

export function OnboardingModal({ isOpen, onComplete, onClose }: OnboardingModalProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [data, setData] = useState<OnboardingData>({
    firstName: "",
    role: "",
    goals: [],
    customGoal: "",
    dataTypes: [],
    dataLocations: [],
  })
  const [isSaving, setIsSaving] = useState(false)
  const { toast } = useToast()

  const totalSteps = 4

  const updateData = (updates: Partial<OnboardingData>) => {
    setData((prev) => ({ ...prev, ...updates }))
  }

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const handleComplete = async () => {
    setIsSaving(true)

    try {
      console.log("Saving onboarding data to Supabase:", data)

      // Save to Supabase first
      const result = await saveOnboardingData(data)

      if (!result.success) {
        console.error("Failed to save onboarding data:", result.error)
        toast({
          title: "Error saving data",
          description: result.error || "Failed to save your onboarding information. Please try again.",
          variant: "destructive",
        })
        return
      }

      console.log("Onboarding data saved successfully to Supabase")

      // Also save to localStorage as backup
      localStorage.setItem("nexdatawork_onboarding", JSON.stringify(data))

      toast({
        title: "Welcome aboard!",
        description: "Your preferences have been saved successfully.",
      })

      // Call the completion handler
      onComplete(data)
    } catch (error) {
      console.error("Unexpected error during onboarding completion:", error)
      toast({
        title: "Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  const toggleGoal = (goal: string) => {
    updateData({
      goals: data.goals.includes(goal) ? data.goals.filter((g) => g !== goal) : [...data.goals, goal],
    })
  }

  const toggleDataType = (type: string) => {
    updateData({
      dataTypes: data.dataTypes.includes(type) ? data.dataTypes.filter((t) => t !== type) : [...data.dataTypes, type],
    })
  }

  const toggleDataLocation = (location: string) => {
    updateData({
      dataLocations: data.dataLocations.includes(location)
        ? data.dataLocations.filter((l) => l !== location)
        : [...data.dataLocations, location],
    })
  }

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return data.firstName.trim() && data.role
      case 2:
        return data.goals.length > 0 || data.customGoal.trim()
      case 3:
        return data.dataTypes.length > 0 && data.dataLocations.length > 0
      case 4:
        return true
      default:
        return false
    }
  }

  const renderProgressDots = () => (
    <div className="flex items-center justify-center space-x-4 mb-8">
      {Array.from({ length: totalSteps }, (_, i) => {
        const stepNumber = i + 1
        const isActive = stepNumber === currentStep
        const isCompleted = stepNumber < currentStep

        return (
          <div key={stepNumber} className="flex items-center">
            <div
              className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300",
                isActive
                  ? "bg-violet-600 text-white shadow-lg scale-110"
                  : isCompleted
                    ? "bg-green-500 text-white"
                    : "bg-gray-200 text-gray-500",
              )}
            >
              {isCompleted ? <CheckCircle className="h-5 w-5" /> : stepNumber}
            </div>
            {stepNumber < totalSteps && (
              <div
                className={cn(
                  "w-8 h-0.5 mx-2 transition-colors duration-300",
                  stepNumber < currentStep ? "bg-green-500" : "bg-gray-200",
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="bg-violet-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <User className="h-8 w-8 text-violet-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to NexDatawork!</h2>
        <p className="text-gray-600">Let's get to know you better</p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="firstName" className="text-sm font-medium text-gray-700">
            What's your first name?
          </Label>
          <Input
            id="firstName"
            type="text"
            placeholder="Enter your first name"
            value={data.firstName}
            onChange={(e) => updateData({ firstName: e.target.value })}
            className="mt-1 h-12 border-gray-200 focus:border-violet-500 focus:ring-violet-500"
          />
        </div>

        <div>
          <Label className="text-sm font-medium text-gray-700 mb-3 block">What's your role?</Label>
          <div className="grid grid-cols-2 gap-3">
            {roles.map((role) => {
              const Icon = role.icon
              return (
                <Card
                  key={role.id}
                  className={cn(
                    "cursor-pointer transition-all duration-200 hover:shadow-md",
                    data.role === role.id ? "ring-2 ring-violet-500 bg-violet-50" : "hover:bg-gray-50",
                  )}
                  onClick={() => updateData({ role: role.id })}
                >
                  <CardContent className="p-4 flex items-center space-x-3">
                    <Icon className={cn("h-5 w-5", data.role === role.id ? "text-violet-600" : "text-gray-500")} />
                    <span className={cn("font-medium", data.role === role.id ? "text-violet-900" : "text-gray-700")}>
                      {role.label}
                    </span>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="bg-violet-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Target className="h-8 w-8 text-violet-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">What do you want to achieve?</h2>
        <p className="text-gray-600">Select all that apply or add your own</p>
      </div>

      <div className="space-y-4">
        <div>
          <Label className="text-sm font-medium text-gray-700 mb-3 block">Common goals</Label>
          <div className="grid grid-cols-2 gap-2">
            {goals.map((goal) => (
              <Badge
                key={goal}
                variant={data.goals.includes(goal) ? "default" : "outline"}
                className={cn(
                  "cursor-pointer p-3 justify-center text-center transition-all duration-200 hover:shadow-sm",
                  data.goals.includes(goal)
                    ? "bg-violet-600 hover:bg-violet-700"
                    : "hover:bg-violet-50 hover:border-violet-300",
                )}
                onClick={() => toggleGoal(goal)}
              >
                {goal}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="customGoal" className="text-sm font-medium text-gray-700">
            Or describe your specific goal
          </Label>
          <Textarea
            id="customGoal"
            placeholder="e.g., I want to analyze customer churn patterns..."
            value={data.customGoal}
            onChange={(e) => updateData({ customGoal: e.target.value })}
            className="mt-1 border-gray-200 focus:border-violet-500 focus:ring-violet-500"
            rows={3}
          />
        </div>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="bg-violet-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Database className="h-8 w-8 text-violet-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Tell us about your data</h2>
        <p className="text-gray-600">What kind of data do you work with and where is it stored?</p>
      </div>

      <div className="space-y-6">
        <div>
          <Label className="text-sm font-medium text-gray-700 mb-3 block">What type of data do you have?</Label>
          <div className="grid grid-cols-2 gap-2">
            {dataTypes.map((type) => (
              <Badge
                key={type}
                variant={data.dataTypes.includes(type) ? "default" : "outline"}
                className={cn(
                  "cursor-pointer p-3 justify-center text-center transition-all duration-200 hover:shadow-sm",
                  data.dataTypes.includes(type)
                    ? "bg-violet-600 hover:bg-violet-700"
                    : "hover:bg-violet-50 hover:border-violet-300",
                )}
                onClick={() => toggleDataType(type)}
              >
                {type}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-sm font-medium text-gray-700 mb-3 block">Where is your data stored?</Label>
          <div className="grid grid-cols-2 gap-3">
            {dataLocations.map((location) => {
              const Icon = location.icon
              return (
                <Card
                  key={location.id}
                  className={cn(
                    "cursor-pointer transition-all duration-200 hover:shadow-md",
                    data.dataLocations.includes(location.id)
                      ? "ring-2 ring-violet-500 bg-violet-50"
                      : "hover:bg-gray-50",
                  )}
                  onClick={() => toggleDataLocation(location.id)}
                >
                  <CardContent className="p-4 flex items-center space-x-3">
                    <Icon
                      className={cn(
                        "h-5 w-5",
                        data.dataLocations.includes(location.id) ? "text-violet-600" : "text-gray-500",
                      )}
                    />
                    <span
                      className={cn(
                        "font-medium",
                        data.dataLocations.includes(location.id) ? "text-violet-900" : "text-gray-700",
                      )}
                    >
                      {location.label}
                    </span>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep4 = () => (
    <div className="space-y-6 text-center">
      <div className="bg-gradient-to-br from-violet-100 to-purple-100 rounded-full p-6 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
        <Sparkles className="h-12 w-12 text-violet-600" />
      </div>

      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Welcome aboard, {data.firstName}! 🎉</h2>
        <p className="text-lg text-gray-600 mb-6">
          You're all set to start analyzing your data with AI-powered insights
        </p>
      </div>

      <div className="bg-violet-50 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-violet-900 mb-4">Your Setup Summary:</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-white rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <User className="h-4 w-4 text-violet-600" />
              <span className="font-medium text-gray-700">Role</span>
            </div>
            <p className="text-gray-600">{roles.find((r) => r.id === data.role)?.label || data.role}</p>
          </div>

          <div className="bg-white rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-4 w-4 text-violet-600" />
              <span className="font-medium text-gray-700">Goals</span>
            </div>
            <p className="text-gray-600">
              {data.goals.length > 0
                ? `${data.goals.length} selected goals`
                : data.customGoal
                  ? "Custom goal set"
                  : "No goals selected"}
            </p>
          </div>

          <div className="bg-white rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Database className="h-4 w-4 text-violet-600" />
              <span className="font-medium text-gray-700">Data Sources</span>
            </div>
            <p className="text-gray-600">
              {data.dataLocations.length} source{data.dataLocations.length !== 1 ? "s" : ""} configured
            </p>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <p className="text-blue-800 text-sm">
          💡 <strong>Pro tip:</strong> Start by uploading a CSV file to see NexDatawork's AI analysis in action!
        </p>
      </div>
    </div>
  )

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto p-0">
        <div className="p-8">
          {renderProgressDots()}

          <div className="min-h-[400px]">
            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
            {currentStep === 4 && renderStep4()}
          </div>

          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={currentStep === 1 || isSaving}
              className="flex items-center space-x-2 bg-transparent"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Back</span>
            </Button>

            <div className="text-sm text-gray-500">
              Step {currentStep} of {totalSteps}
            </div>

            {currentStep < totalSteps ? (
              <Button
                onClick={nextStep}
                disabled={!canProceed() || isSaving}
                className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-700"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleComplete}
                disabled={isSaving}
                className="flex items-center space-x-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <span>Finish</span>
                    <Sparkles className="h-4 w-4" />
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
