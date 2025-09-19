"use client"

import { Badge } from "@/components/ui/badge"
import { Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp, LightbulbIcon } from "lucide-react"
import type { OnboardingData } from "@/components/onboarding-modal"
import { useState } from "react"

interface ReasoningPanelProps {
  reasoning: string[]
  isAnalyzing?: boolean
  analysisComplete?: boolean
  error?: string
  onboardingData?: OnboardingData | null
  analysisResults?: any
}

export function ReasoningPanel({
  reasoning,
  isAnalyzing = false,
  analysisComplete = false,
  error,
  onboardingData,
  analysisResults,
}: ReasoningPanelProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())

  // Check if we're on client side - assume OpenAI is available for UI purposes
  const isOpenAIAvailable = typeof window !== "undefined" || !!process.env.OPENAI_API_KEY

  // Mock usage data for the chart
  const usageData = [
    { day: "Mon", queries: 8 },
    { day: "Tue", queries: 12 },
    { day: "Wed", queries: 6 },
    { day: "Thu", queries: 15 },
    { day: "Fri", queries: 9 },
    { day: "Sat", queries: 11 },
    { day: "Sun", queries: 7 },
  ]

  const maxQueries = Math.max(...usageData.map((d) => d.queries))
  const totalQueries = usageData.reduce((sum, d) => sum + d.queries, 0)

  // Get personalized welcome message
  const getPersonalizedWelcome = () => {
    if (!onboardingData) {
      return ""
    }

    const roleMessages = {
      ceo: "strategic decision-making insights",
      product: "product analytics and user behavior patterns",
      analyst: "detailed statistical analysis and data correlations",
      marketing: "campaign performance and customer insights",
      operations: "process optimization and efficiency metrics",
      other: "comprehensive data insights",
    }

    return `Upload your data to see AI reasoning tailored for ${roleMessages[onboardingData.role as keyof typeof roleMessages] || roleMessages.other}, ${onboardingData.firstName}!`
  }

  const toggleStepExpansion = (index: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedSteps(newExpanded)
  }

  return (
    <div className="w-full h-full bg-white p-6 space-y-6 flex flex-col" data-reasoning-panel>
      {/* Header Section */}
      <div className="flex-shrink-0">
        <div className="flex flex-col items-center justify-center mb-4">
          <h2 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 text-center">Reasoning</h2>
          <div className="flex items-center gap-2 mt-2">
            {isAnalyzing && (
              <Badge variant="secondary">
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                Analyzing...
              </Badge>
            )}
            {analysisComplete && !error && (
              <Badge variant="default" className="bg-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Complete
              </Badge>
            )}
            {error && (
              <Badge variant="destructive">
                <XCircle className="h-3 w-3 mr-1" />
                Error
              </Badge>
            )}
          </div>
        </div>

        {/* Progress Bar Section */}
        {isAnalyzing && (
          <div className="mb-6">
            <div className="p-4 bg-gradient-to-r from-violet-50 to-purple-50 rounded-lg border border-violet-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-violet-800">
                  {onboardingData ? `Analyzing data for ${onboardingData.firstName}...` : "Analyzing your data..."}
                </span>
                <span className="text-xs text-violet-600">
                  {Math.min(Math.round((reasoning.length / 15) * 100), 95)}%
                </span>
              </div>

              {/* Enhanced Dynamic Progress Bar */}
              <div className="w-full bg-violet-100 rounded-full h-3 overflow-hidden mb-3">
                <div
                  className="bg-gradient-to-r from-violet-500 via-purple-500 to-violet-600 h-3 rounded-full transition-all duration-1000 ease-out relative"
                  style={{
                    width: `${Math.min((reasoning.length / 15) * 100 + 10, 95)}%`,
                  }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full"></div>
                </div>
              </div>

              {/* Context-aware Status Messages */}
              <div className="flex items-center gap-2 text-xs text-violet-700">
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce"></div>
                  <div
                    className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
                <span className="font-medium">
                  {reasoning.length < 3
                    ? "Initializing analysis pipeline..."
                    : reasoning.length < 6
                      ? "Processing file structure..."
                      : reasoning.length < 9
                        ? "Connecting to AI engine..."
                        : reasoning.length < 12
                          ? "Generating insights..."
                          : "Finalizing analysis..."}
                </span>
              </div>

              {/* Pulsing Activity Indicator */}
              <div className="mt-3 flex items-center justify-center">
                <div className="flex space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-2 h-2 bg-violet-400 rounded-full animate-pulse"
                      style={{
                        animationDelay: `${i * 0.2}s`,
                        animationDuration: "1.5s",
                      }}
                    ></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 min-h-0">
        {error ? (
          <div className="text-red-600 p-4 bg-red-50 rounded-lg border border-red-200">
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <XCircle className="h-4 w-4" />
              Analysis Error:
            </h4>
            <p className="text-sm">{error}</p>
          </div>
        ) : reasoning.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center p-8 h-full">
            <div className="bg-violet-100 rounded-full p-4 mb-4 animate-pulse">
              <LightbulbIcon className="h-8 w-8 text-violet-600" />
            </div>
            <h3 className="text-xl font-medium mb-2 text-violet-700">Ready for Analysis</h3>
            <p className="text-gray-600 mb-3">Run analysis to see live reasoning</p>
            <div className="mt-6 flex items-center gap-2 text-sm text-violet-600">
              <div className="w-2 h-2 bg-violet-500 rounded-full animate-ping"></div>
              <span>Ready to analyze your data</span>
            </div>
          </div>
        ) : (
          <div className="h-full">
            <div
              className="h-full overflow-y-auto pr-2"
              style={{
                scrollbarWidth: "thin",
                scrollbarColor: "#a855f7 #f1f5f9",
              }}
            >
              <style jsx>{`
                div::-webkit-scrollbar {
                  width: 8px;
                }
                div::-webkit-scrollbar-track {
                  background: #f8fafc;
                  border-radius: 4px;
                }
                div::-webkit-scrollbar-thumb {
                  background: #a855f7;
                  border-radius: 4px;
                }
                div::-webkit-scrollbar-thumb:hover {
                  background: #9333ea;
                }
              `}</style>
              <div className="space-y-3">
                {reasoning.map((step, index) => {
                  // Clean up the text but keep full content
                  const cleanStep = step
                    .replace(
                      /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|🧠|🔍|📊|✅|❌|📈|📉|💡|🎯|🔧|⚡|🚀/gu,
                      "",
                    )
                    .replace(/Langchain\s+Step\s+\d+:?\s*/gi, "")
                    .replace(/Step\s+\d+:?\s*/gi, "")
                    .replace(/\s+/g, " ")
                    .trim()

                  const boldTitleMatch = cleanStep.match(/\*\*(.*?)\*\*:?\s*(.*)/)
                  const isLongContent = cleanStep.length > 100
                  const isExpanded = expandedSteps.has(index)

                  // For display purposes, show preview if not expanded and content is long
                  const displayStep = isLongContent && !isExpanded ? cleanStep.substring(0, 80) + "..." : cleanStep

                  return (
                    <div
                      key={index}
                      className="py-3 px-4 bg-gray-50/50 rounded-lg hover:bg-gray-50 transition-colors animate-fadeIn"
                      style={{
                        animationDelay: `${index * 0.05}s`,
                        animationFillMode: "both",
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-6 h-6 bg-violet-100 text-violet-700 rounded-full flex items-center justify-center text-xs font-medium">
                          {index + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          {boldTitleMatch ? (
                            <div>
                              <div className="text-sm font-semibold text-gray-900 mb-1 leading-relaxed">
                                {boldTitleMatch[1]}
                              </div>
                              {boldTitleMatch[2] && (
                                <div className="text-sm text-gray-700 leading-relaxed">
                                  {isLongContent && !isExpanded
                                    ? boldTitleMatch[2].substring(0, 60) + "..."
                                    : boldTitleMatch[2]}
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-sm text-gray-700 leading-relaxed">{displayStep}</div>
                          )}

                          {/* Show More/Less Button for Long Content */}
                          {isLongContent && (
                            <button
                              onClick={() => toggleStepExpansion(index)}
                              className="mt-2 text-xs text-violet-600 hover:text-violet-800 flex items-center gap-1 transition-colors font-medium"
                            >
                              {isExpanded ? (
                                <>
                                  <ChevronUp className="h-3 w-3" />
                                  Show Less
                                </>
                              ) : (
                                <>
                                  <ChevronDown className="h-3 w-3" />
                                  Show More
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// CSS for animations
const styles = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  .animate-fadeIn {
    animation: fadeIn 0.5s ease-out;
  }
`

// Inject styles
if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style")
  styleSheet.innerText = styles
  document.head.appendChild(styleSheet)
}
