"use client"

import { useState, useEffect } from "react"
import { UploadPanel } from "@/components/upload-panel"
import { DashboardPanel } from "@/components/dashboard-panel"
import { ReasoningPanel } from "@/components/reasoning-panel"
import { TopBar } from "@/components/top-bar"
import { DatasetsPanel } from "@/components/datasets-panel"
import { cn } from "@/lib/utils"
import { LogPanel } from "@/components/log-panel"
import type { OnboardingData } from "@/components/onboarding-modal"
import { setCsvContext } from "@/lib/langchain-service"
import { getOnboardingData } from "@/lib/onboarding-service"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"

// Define Message type locally to avoid AI SDK dependency
interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
}

// CSV parsing utility function
function parseCSV(csvText: string): { headers: string[]; rows: string[][] } {
  const lines = csvText.split("\n").filter((line) => line.trim())
  if (lines.length === 0) return { headers: [], rows: [] }

  const headers = lines[0].split(",").map((h) => h.trim().replace(/"/g, ""))
  const rows = lines.slice(1).map((line) => line.split(",").map((cell) => cell.trim().replace(/"/g, "")))

  return { headers, rows }
}

// Data analysis utility functions
function analyzeDataTypes(headers: string[], rows: string[][]) {
  const columnTypes: { [key: string]: "number" | "string" | "date" } = {}

  headers.forEach((header, index) => {
    const values = rows.map((row) => row[index]).filter((val) => val && val.trim())

    if (values.length === 0) {
      columnTypes[header] = "string"
      return
    }

    // Check if numeric
    const numericValues = values.filter((val) => !isNaN(Number(val)))
    if (numericValues.length > values.length * 0.8) {
      columnTypes[header] = "number"
      return
    }

    // Check if date
    const dateValues = values.filter((val) => !isNaN(Date.parse(val)))
    if (dateValues.length > values.length * 0.8) {
      columnTypes[header] = "date"
      return
    }

    columnTypes[header] = "string"
  })

  return columnTypes
}

function generateInsights(
  headers: string[],
  rows: string[][],
  columnTypes: { [key: string]: string },
  industry: string,
  topic: string,
  onboardingData?: OnboardingData | null,
) {
  const insights: string[] = []

  // Personalized greeting based on onboarding data
  if (onboardingData) {
    const roleLabel =
      {
        ceo: "CEO",
        product: "Product Manager",
        analyst: "Data Analyst",
        marketing: "Marketing Professional",
        operations: "Operations Manager",
        other: "Professional",
      }[onboardingData.role] || "Professional"

    insights.push(`Welcome ${onboardingData.firstName}! As a ${roleLabel}, here's your personalized analysis:`)
  }

  // Basic data insights
  insights.push(`Dataset contains ${rows.length} records with ${headers.length} columns`)

  const numericColumns = Object.entries(columnTypes)
    .filter(([_, type]) => type === "number")
    .map(([name]) => name)
  const stringColumns = Object.entries(columnTypes)
    .filter(([_, type]) => type === "string")
    .map(([name]) => name)
  const dateColumns = Object.entries(columnTypes)
    .filter(([_, type]) => type === "date")
    .map(([name]) => name)

  // Goal-specific insights based on onboarding
  if (onboardingData?.goals.length > 0) {
    const primaryGoal = onboardingData.goals[0]

    if (primaryGoal.includes("sales") || primaryGoal.includes("revenue")) {
      const salesColumns = headers.filter(
        (h) =>
          h.toLowerCase().includes("sales") ||
          h.toLowerCase().includes("revenue") ||
          h.toLowerCase().includes("amount") ||
          h.toLowerCase().includes("price"),
      )
      if (salesColumns.length > 0) {
        insights.push(
          `Found ${salesColumns.length} sales-related columns perfect for your ${primaryGoal} goal: ${salesColumns.slice(0, 3).join(", ")}`,
        )
      }
    }

    if (primaryGoal.includes("customer") || primaryGoal.includes("behavior")) {
      const customerColumns = headers.filter(
        (h) =>
          h.toLowerCase().includes("customer") ||
          h.toLowerCase().includes("user") ||
          h.toLowerCase().includes("client") ||
          h.toLowerCase().includes("name"),
      )
      if (customerColumns.length > 0) {
        insights.push(`Identified ${customerColumns.length} customer-related fields for your ${primaryGoal} analysis`)
      }
    }

    if (primaryGoal.includes("trend") || primaryGoal.includes("time")) {
      if (dateColumns.length > 0) {
        insights.push(
          `Perfect! Found ${dateColumns.length} date columns for trend analysis: ${dateColumns.slice(0, 2).join(", ")}`,
        )
      }
    }
  }

  // Data type insights
  if (numericColumns.length > 0) {
    insights.push(
      `Found ${numericColumns.length} numeric columns: ${numericColumns.slice(0, 3).join(", ")}${numericColumns.length > 3 ? "..." : ""}`,
    )
  }

  if (stringColumns.length > 0) {
    insights.push(
      `Found ${stringColumns.length} categorical columns: ${stringColumns.slice(0, 3).join(", ")}${stringColumns.length > 3 ? "..." : ""}`,
    )
  }

  if (dateColumns.length > 0) {
    insights.push(
      `Found ${dateColumns.length} date columns: ${dateColumns.slice(0, 3).join(", ")}${dateColumns.length > 3 ? "..." : ""}`,
    )
  }

  // Missing data analysis
  const missingDataCounts = headers.map((header) => {
    const columnIndex = headers.indexOf(header)
    const missingCount = rows.filter((row) => !row[columnIndex] || row[columnIndex].trim() === "").length
    return { column: header, missing: missingCount, percentage: (missingCount / rows.length) * 100 }
  })

  const columnsWithMissingData = missingDataCounts.filter((col) => col.missing > 0)
  if (columnsWithMissingData.length > 0) {
    const highMissingColumns = columnsWithMissingData.filter((col) => col.percentage > 10)
    if (highMissingColumns.length > 0) {
      insights.push(
        `High missing data detected in: ${highMissingColumns.map((col) => `${col.column} (${col.percentage.toFixed(1)}%)`).join(", ")}`,
      )
    } else {
      insights.push(`Minor missing data found in ${columnsWithMissingData.length} columns`)
    }
  } else {
    insights.push("No missing data detected - dataset is complete")
  }

  // Role-specific insights
  if (onboardingData?.role) {
    if (onboardingData.role === "ceo") {
      insights.push(
        "Executive Summary: This dataset provides comprehensive business metrics suitable for strategic decision-making",
      )
    } else if (onboardingData.role === "analyst") {
      insights.push("Analyst Note: Dataset structure is well-suited for statistical analysis and modeling")
    } else if (onboardingData.role === "marketing") {
      const marketingColumns = headers.filter(
        (h) =>
          h.toLowerCase().includes("campaign") ||
          h.toLowerCase().includes("channel") ||
          h.toLowerCase().includes("source") ||
          h.toLowerCase().includes("conversion"),
      )
      if (marketingColumns.length > 0) {
        insights.push(
          `Marketing Focus: Found ${marketingColumns.length} marketing-relevant columns for campaign analysis`,
        )
      }
    }
  }

  // Unique value analysis for categorical columns
  stringColumns.slice(0, 2).forEach((column) => {
    const columnIndex = headers.indexOf(column)
    const values = rows.map((row) => row[columnIndex]).filter((val) => val && val.trim())
    const uniqueValues = [...new Set(values)]
    insights.push(`Column '${column}' has ${uniqueValues.length} unique values`)
  })

  // Numeric column analysis
  numericColumns.slice(0, 2).forEach((column) => {
    const columnIndex = headers.indexOf(column)
    const values = rows.map((row) => Number(row[columnIndex])).filter((val) => !isNaN(val))
    if (values.length > 0) {
      const min = Math.min(...values)
      const max = Math.max(...values)
      const avg = values.reduce((sum, val) => sum + val, 0) / values.length
      insights.push(`Column '${column}' ranges from ${min.toFixed(2)} to ${max.toFixed(2)} (avg: ${avg.toFixed(2)})`)
    }
  })

  return insights
}

function generateVisualizations(headers: string[], rows: string[][], columnTypes: { [key: string]: string }) {
  const visualizations: any[] = []

  const numericColumns = Object.entries(columnTypes)
    .filter(([_, type]) => type === "number")
    .map(([name]) => name)
  const stringColumns = Object.entries(columnTypes)
    .filter(([_, type]) => type === "string")
    .map(([name]) => name)

  // Bar chart for first categorical column
  if (stringColumns.length > 0) {
    const column = stringColumns[0]
    const columnIndex = headers.indexOf(column)
    const values = rows.map((row) => row[columnIndex]).filter((val) => val && val.trim())
    const valueCounts: { [key: string]: number } = {}

    values.forEach((val) => {
      valueCounts[val] = (valueCounts[val] || 0) + 1
    })

    const sortedEntries = Object.entries(valueCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10) // Top 10 values

    if (sortedEntries.length > 0) {
      visualizations.push({
        type: "bar",
        title: `Distribution of ${column}`,
        data: {
          labels: sortedEntries.map(([label]) => label),
          datasets: [
            {
              label: "Count",
              data: sortedEntries.map(([, count]) => count),
              backgroundColor: "rgba(59, 130, 246, 0.8)",
              borderColor: "rgba(59, 130, 246, 1)",
              borderWidth: 1,
            },
          ],
        },
      })
    }
  }

  // Line chart for numeric data over index (if we have numeric columns)
  if (numericColumns.length > 0) {
    const column = numericColumns[0]
    const columnIndex = headers.indexOf(column)
    const values = rows
      .map((row, index) => ({
        x: index + 1,
        y: Number(row[columnIndex]),
      }))
      .filter((point) => !isNaN(point.y))

    if (values.length > 0) {
      // Sample data points if too many
      const sampledValues =
        values.length > 50 ? values.filter((_, index) => index % Math.ceil(values.length / 50) === 0) : values

      visualizations.push({
        type: "line",
        title: `${column} Trend`,
        data: {
          labels: sampledValues.map((point) => point.x.toString()),
          datasets: [
            {
              label: column,
              data: sampledValues.map((point) => point.y),
              borderColor: "rgba(34, 197, 94, 1)",
              backgroundColor: "rgba(34, 197, 94, 0.1)",
              tension: 0.1,
            },
          ],
        },
      })
    }
  }

  // Scatter plot if we have 2+ numeric columns
  if (numericColumns.length >= 2) {
    const xColumn = numericColumns[0]
    const yColumn = numericColumns[1]
    const xIndex = headers.indexOf(xColumn)
    const yIndex = headers.indexOf(yColumn)

    const scatterData = rows
      .map((row) => ({
        x: Number(row[xIndex]),
        y: Number(row[yIndex]),
      }))
      .filter((point) => !isNaN(point.x) && !isNaN(point.y))

    if (scatterData.length > 0) {
      // Sample data points if too many
      const sampledData =
        scatterData.length > 100
          ? scatterData.filter((_, index) => index % Math.ceil(scatterData.length / 100) === 0)
          : scatterData

      visualizations.push({
        type: "scatter",
        title: `${xColumn} vs ${yColumn}`,
        data: {
          datasets: [
            {
              label: `${xColumn} vs ${yColumn}`,
              data: sampledData,
              backgroundColor: "rgba(168, 85, 247, 0.6)",
              borderColor: "rgba(168, 85, 247, 1)",
            },
          ],
        },
      })
    }
  }

  return visualizations
}

export default function Home() {
  const [files, setFiles] = useState<File[]>([])
  const [industry, setIndustry] = useState<string>("")
  const [topic, setTopic] = useState<string>("")
  const [requirement, setRequirement] = useState<string>("")
  const [customRequirement, setCustomRequirement] = useState<string>("")
  const [messages, setMessages] = useState<Message[]>([])
  const [reasoning, setReasoning] = useState<string[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<any>(null)
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false)
  const [leftPanelWidth, setLeftPanelWidth] = useState("30%")
  const [middlePanelWidth, setMiddlePanelWidth] = useState("50%")
  const [rightPanelWidth, setRightPanelWidth] = useState("20%")
  const [activeView, setActiveView] = useState<"dashboard" | "log" | "datasets">("dashboard")
  const [langchainAnalysis, setLangchainAnalysis] = useState<string>("")
  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(null)
  const [isLoadingOnboarding, setIsLoadingOnboarding] = useState(true)
  const { toast } = useToast()
  const [uploadPanelWidth, setUploadPanelWidth] = useState(30) // percentage

  const handleCustomRequirementChange = (value: string) => {
    setCustomRequirement(value)
  }

  // Load onboarding data from Supabase on component mount
  useEffect(() => {
    const loadOnboardingData = async () => {
      try {
        setIsLoadingOnboarding(true)
        console.log("Loading onboarding data from Supabase...")

        const result = await getOnboardingData()

        if (result.error && result.error === "User not authenticated") {
          console.log("User not authenticated - using localStorage fallback")
          // Fall back to localStorage if user is not authenticated
          const localData = localStorage.getItem("nexdatawork_onboarding")
          if (localData) {
            try {
              const parsed = JSON.parse(localData)
              setOnboardingData(parsed)
              console.log("Loaded onboarding data from localStorage:", parsed)
            } catch (error) {
              console.error("Failed to parse localStorage onboarding data:", error)
            }
          }
        } else if (result.error) {
          console.error("Error loading onboarding data:", result.error)
          // Fall back to localStorage if Supabase fails
          const localData = localStorage.getItem("nexdatawork_onboarding")
          if (localData) {
            try {
              const parsed = JSON.parse(localData)
              setOnboardingData(parsed)
              console.log("Loaded onboarding data from localStorage as fallback:", parsed)
            } catch (error) {
              console.error("Failed to parse localStorage onboarding data:", error)
            }
          }
        } else if (result.data) {
          setOnboardingData(result.data)
          console.log("Loaded onboarding data from Supabase:", result.data)

          // Also update localStorage for consistency
          localStorage.setItem("nexdatawork_onboarding", JSON.stringify(result.data))

          // Auto-populate fields based on onboarding data
          if (result.data.dataTypes.length > 0) {
            // Map data types to industries
            const dataTypeToIndustry: { [key: string]: string } = {
              "Sales data": "retail",
              "Customer data": "retail",
              "Financial data": "finance",
              "Marketing data": "marketing",
              "Operational data": "manufacturing",
            }

            const detectedIndustry = dataTypeToIndustry[result.data.dataTypes[0]]
            if (detectedIndustry) {
              setIndustry(detectedIndustry)
            }
          }

          // Set topic based on goals
          if (result.data.goals.length > 0) {
            const goalToTopic: { [key: string]: string } = {
              "Analyze sales data": "sales",
              "Track customer behavior": "customer",
              "Monitor KPIs": "operations",
              "Identify trends": "trends",
              "Generate reports": "reporting",
            }

            const detectedTopic = goalToTopic[result.data.goals[0]]
            if (detectedTopic) {
              setTopic(detectedTopic)
            }
          }
        } else {
          console.log("No onboarding data found in Supabase")
          // Check localStorage as fallback
          const localData = localStorage.getItem("nexdatawork_onboarding")
          if (localData) {
            try {
              const parsed = JSON.parse(localData)
              setOnboardingData(parsed)
              console.log("Loaded onboarding data from localStorage:", parsed)
            } catch (error) {
              console.error("Failed to parse localStorage onboarding data:", error)
            }
          }
        }
      } catch (error) {
        console.error("Unexpected error loading onboarding data:", error)
        if (error instanceof Error && !error.message.includes("not authenticated")) {
          toast({
            title: "Error loading preferences",
            description: "Could not load your saved preferences. Using defaults.",
            variant: "destructive",
          })
        }
      } finally {
        setIsLoadingOnboarding(false)
      }
    }

    loadOnboardingData()
  }, [toast])

  // Update middle panel width when left panel is collapsed
  useEffect(() => {
    if (isLeftPanelCollapsed) {
      // When collapsed, we don't need to change the middle panel width
      // as it will be handled by the flex-1 class and calc() in the style
    } else {
      setLeftPanelWidth("30%")
      setMiddlePanelWidth("50%")
      setRightPanelWidth("20%")
    }
  }, [isLeftPanelCollapsed])

  const handleFileUpload = (newFiles: File[]) => {
    setFiles(newFiles)
  }

  const handleIndustryChange = (value: string) => {
    setIndustry(value)
  }

  const handleTopicChange = (value: string) => {
    setTopic(value)
  }

  const handleRequirementChange = (value: string) => {
    setRequirement(value)
  }

  const handleLeftPanelCollapse = (collapsed: boolean) => {
    setIsLeftPanelCollapsed(collapsed)
  }

  const handleViewChange = (view: "dashboard" | "log" | "datasets") => {
    setActiveView(view)
  }

  const handleRunAnalysis = async () => {
    if (files.length === 0) return

    // Start analysis process
    setIsAnalyzing(true)
    setReasoning([])
    setLangchainAnalysis("")
    setAnalysisResults(null)

    // Scroll to Agent Reasoning panel
    setTimeout(() => {
      const reasoningPanel = document.querySelector("[data-reasoning-panel]")
      if (reasoningPanel) {
        reasoningPanel.scrollIntoView({ behavior: "smooth", block: "start" })
      }
    }, 100)

    // Add immediate real-time reasoning steps with context-aware messages
    const immediateSteps = [
      "🔄 **Analysis Initiated**: Starting data processing pipeline",
      "📁 **File Reading**: Parsing CSV structure and validating format",
      "🔍 **Data Validation**: Checking data integrity and column types",
    ]

    // Show immediate steps with delays
    for (let i = 0; i < immediateSteps.length; i++) {
      setTimeout(() => {
        setReasoning((prev) => [...prev, immediateSteps[i]])
      }, i * 600)
    }

    // Add personalized greeting if onboarding data exists
    if (onboardingData) {
      setTimeout(() => {
        setReasoning((prev) => [
          ...prev,
          `👋 **Welcome ${onboardingData.firstName}!** Preparing personalized analysis for ${onboardingData.role} role`,
        ])
      }, 1800)
    }

    try {
      // Read and analyze the actual CSV file
      const file = files[0]
      console.log("📁 Reading file:", file.name, "Size:", file.size)

      const fileContent = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const result = e.target?.result
          if (typeof result === "string") {
            resolve(result)
          } else {
            reject(new Error("Failed to read file as text"))
          }
        }
        reader.onerror = (e) => reject(new Error("File reading failed"))
        reader.readAsText(file)
      })

      console.log("📄 File content length:", fileContent.length)

      // Parse CSV content
      const { headers, rows } = parseCSV(fileContent)

      if (headers.length === 0 || rows.length === 0) {
        throw new Error("CSV file appears to be empty or invalid")
      }

      console.log("📊 Parsed CSV:", { headers: headers.length, rows: rows.length })

      // Add real-time parsing feedback
      setReasoning((prev) => [
        ...prev,
        `✅ **File Parsed Successfully**: Found ${headers.length} columns and ${rows.length} rows`,
        `📊 **Data Structure**: Analyzing column types and data patterns`,
        `🎯 **Context Integration**: Applying ${industry || "general"} industry knowledge`,
      ])

      // Add goal-specific reasoning if available
      if (onboardingData?.goals.length > 0) {
        setReasoning((prev) => [
          ...prev,
          `🎯 **Goal Alignment**: Tailoring analysis for "${onboardingData.goals[0]}" objective`,
        ])
      }

      // Create personalized analysis question based on onboarding data
      let analysisQuestion = `Analyze this ${industry || "general"} dataset${topic ? ` focusing on ${topic}` : ""}${requirement ? ` with ${requirement} requirements` : ""}`

      // Add custom requirements if provided
      if (customRequirement.trim()) {
        analysisQuestion += `. Specific analysis requirements: ${customRequirement.trim()}`
      }

      if (onboardingData) {
        const roleContext =
          {
            ceo: "executive-level strategic insights",
            product: "product management and user behavior insights",
            analyst: "detailed statistical analysis and data patterns",
            marketing: "marketing performance and customer acquisition insights",
            operations: "operational efficiency and process optimization insights",
            other: "comprehensive business insights",
          }[onboardingData.role] || "business insights"

        const goalContext =
          onboardingData.goals.length > 0 ? ` with focus on ${onboardingData.goals.slice(0, 2).join(" and ")}` : ""

        analysisQuestion = `As a ${onboardingData.role} named ${onboardingData.firstName}, provide ${roleContext} for this dataset${goalContext}. ${analysisQuestion}`
      }

      // Prepare request data with onboarding context
      const requestData = {
        csvData: rows,
        headers,
        question: analysisQuestion,
        industry: industry || "",
        topic: topic || "",
        requirement: requirement || "",
        customRequirement: customRequirement || "",
        filename: file.name,
        onboardingData: onboardingData,
      }

      console.log("🚀 Sending analysis request with onboarding context...")

      // Add API preparation steps
      setReasoning((prev) => [
        ...prev,
        "🧠 **AI Engine**: Connecting to NexDatawork data agent",
        "⚡ **Processing**: Sending data to advanced AI analysis pipeline",
        "🔗 **Reasoning Core**: Applying multi-step reasoning framework",
      ])

      // Call the server-side API for Azure OpenAI analysis
      const analysisResponse = await fetch("/api/analyze-csv", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      })

      console.log("📡 Response status:", analysisResponse.status)

      // Check if response is ok
      if (!analysisResponse.ok) {
        const errorText = await analysisResponse.text()
        console.error("❌ API Error Response:", errorText)

        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch (parseError) {
          console.error("Failed to parse error response as JSON:", parseError)
          throw new Error(`Server error (${analysisResponse.status}): ${errorText.substring(0, 200)}`)
        }

        throw new Error(errorData.details || errorData.error || "Failed to analyze CSV")
      }

      // Parse response with error handling
      let analysisData
      try {
        const responseText = await analysisResponse.text()
        console.log("📄 Response text length:", responseText.length)

        if (!responseText.trim()) {
          throw new Error("Empty response from server")
        }

        analysisData = JSON.parse(responseText)
        console.log("✅ Successfully parsed response JSON")
      } catch (parseError) {
        console.error("❌ Failed to parse response JSON:", parseError)
        throw new Error("Invalid response format from server")
      }

      // Validate response structure
      if (!analysisData || typeof analysisData !== "object") {
        throw new Error("Invalid analysis data structure")
      }

      if (!analysisData.success) {
        throw new Error(analysisData.error || "Analysis failed")
      }

      // Show reasoning steps one by one
      const reasoningSteps = analysisData.reasoning || []
      for (let i = 0; i < reasoningSteps.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 800))
        setReasoning((prev) => [...prev, reasoningSteps[i]])
      }

      setLangchainAnalysis(analysisData.analysis || "")

      // Analyze data types (fallback method)
      const columnTypes = analyzeDataTypes(headers, rows)

      // Generate insights from actual data with onboarding context
      const insights = generateInsights(headers, rows, columnTypes, industry, topic, onboardingData)

      // Generate visualizations from actual data
      const visualizations = generateVisualizations(headers, rows, columnTypes)

      // Calculate data quality score for the new sections
      const missingDataCounts = headers.map((header) => {
        const columnIndex = headers.indexOf(header)
        const missingCount = rows.filter((row) => !row[columnIndex] || row[columnIndex].trim() === "").length
        return (missingCount / rows.length) * 100
      })
      const dataQualityScore = 100 - missingDataCounts.reduce((a, b) => a + b, 0) / missingDataCounts.length

      // Create analysis results from real data with enhanced structure for new sections
      const analysisResults = {
        summary: `Analysis complete for ${file.name} - ${industry || "general"} industry ${
          topic ? `focusing on ${topic}` : ""
        } ${requirement ? `with ${requirement} requirements` : ""}.`,
        insights: insights,
        visualizations,
        langchainAnalysis: analysisData.analysis || "",
        fileInfo: {
          filename: file.name,
          rows: rows.length,
          columns: headers.length,
          columnNames: headers,
          columnTypes,
          dataQualityScore: dataQualityScore,
        },
      }

      setAnalysisResults(analysisResults)

      // Set CSV context for chat
      setCsvContext(rows, headers, industry, topic, file.name)

      // Add a personalized system message to the chat with real results
      const greeting = onboardingData ? `Hi ${onboardingData.firstName}! ` : ""
      const roleSpecific =
        onboardingData?.role === "ceo"
          ? "executive summary"
          : onboardingData?.role === "analyst"
            ? "detailed analysis"
            : onboardingData?.role === "marketing"
              ? "marketing insights"
              : "analysis"

      const systemMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content:
          `✅ **${greeting}Data Agent Analysis Complete!**\n\n` +
          `📊 **File:** ${file.name}\n` +
          `📈 **Size:** ${rows.length.toLocaleString()} rows × ${headers.length} columns\n` +
          `🧠 **AI Analysis:** Advanced reasoning with NexDatawork Intelligence\n` +
          `👤 **Personalized for:** ${onboardingData ? `${onboardingData.role} role` : "General analysis"}\n\n` +
          `🔍 **Key Insights for ${roleSpecific}:**\n` +
          insights
            .slice(0, 5)
            .map((insight: string) => `• ${insight}`)
            .join("\n") +
          "\n\n📋 **Dashboard Updated!** Check the Dashboard tab for detailed AI-powered analysis and visualizations.\n\n💬 **Chat Ready!** You can now ask questions about your data in the Chat tab.",
      }

      setMessages((prev) => [...prev, systemMessage])
    } catch (error) {
      console.error("❌ Error running analysis:", error)

      // Add error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content:
          `❌ **Analysis Error**\n\n` +
          `Failed to analyze "${files[0]?.name || "your file"}":\n\n` +
          `${error instanceof Error ? error.message : "Unknown error occurred"}\n\n` +
          `**Troubleshooting:**\n` +
          `• Ensure the file is a valid CSV format\n` +
          `• Check that the file has proper headers\n` +
          `• Verify the file is not corrupted or empty\n` +
          `• Ensure Azure OpenAI credentials are configured correctly\n` +
          `• Try refreshing the page and uploading again`,
      }
      setMessages((prev) => [...prev, errorMessage])

      // Set error state for dashboard
      setAnalysisResults({
        error: error instanceof Error ? error.message : "Analysis failed",
        insights: ["Could not process the uploaded CSV file", "Please check the file format and try again"],
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Legacy chat submit handler (not used anymore since we're using useChat)
  const handleChatSubmit = async (message: string) => {
    // This is now handled by the useChat hook in DashboardPanel
    console.log("Legacy chat submit:", message)
  }

  // Show loading state while onboarding data is being loaded
  if (isLoadingOnboarding) {
    return (
      <div className="flex min-h-screen flex-col bg-[#f8f9fc]">
        <TopBar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-gray-600">Loading your preferences...</span>
          </div>
        </div>
      </div>
    )
  }

  const handleUploadPanelWidthChange = (widthPercentage: number) => {
    setUploadPanelWidth(widthPercentage)
  }

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left Panel - Upload Panel (no top bar above it) */}
      <div
        className={cn("flex-shrink-0 transition-all duration-300", isLeftPanelCollapsed ? "w-16" : "")}
        style={{
          width: isLeftPanelCollapsed ? "64px" : `${uploadPanelWidth}%`,
        }}
      >
        <UploadPanel
          onFileUpload={handleFileUpload}
          onIndustryChange={handleIndustryChange}
          onTopicChange={handleTopicChange}
          onRequirementChange={handleRequirementChange}
          onCustomRequirementChange={handleCustomRequirementChange}
          onRunAnalysis={handleRunAnalysis}
          onCollapseChange={handleLeftPanelCollapse}
          onViewChange={handleViewChange}
          onWidthChange={handleUploadPanelWidthChange}
          files={files}
          industry={industry}
          topic={topic}
          requirement={requirement}
          customRequirement={customRequirement}
        />
      </div>

      {/* Right side with TopBar and content panels */}
      <div className="flex-1 flex flex-col">
        <TopBar />

        {/* Content area below top bar */}
        <div className="flex flex-1 overflow-hidden gap-0">
          {/* Middle Panel */}
          <div
            className="flex-1 min-w-0 h-full bg-white"
            style={{
              width: isLeftPanelCollapsed ? `calc(80% - 64px)` : `${70 - uploadPanelWidth}%`,
            }}
          >
            {activeView === "log" ? (
              <LogPanel />
            ) : activeView === "datasets" ? (
              <DatasetsPanel />
            ) : (
              <DashboardPanel
                messages={messages}
                onChatSubmit={handleChatSubmit}
                isAnalyzing={isAnalyzing}
                analysisResults={analysisResults}
                onboardingData={onboardingData}
              />
            )}
          </div>

          {/* Right Panel - Reasoning Panel */}
          <div
            className="flex-shrink-0 h-full bg-white"
            style={{
              width: "20%",
            }}
          >
            <ReasoningPanel
              reasoning={reasoning}
              isAnalyzing={isAnalyzing}
              analysisComplete={!isAnalyzing && reasoning.length > 0}
              error={analysisResults?.error}
              onboardingData={onboardingData}
              analysisResults={analysisResults}
            />
          </div>
        </div>
      </div>

      {/* Mobile view remains the same */}
      <div className="md:hidden flex flex-col h-screen bg-white">
        <div className="flex-1 overflow-y-auto p-4">
          {activeView === "log" ? (
            <LogPanel />
          ) : activeView === "datasets" ? (
            <DatasetsPanel />
          ) : (
            <DashboardPanel
              messages={messages}
              onChatSubmit={handleChatSubmit}
              isAnalyzing={isAnalyzing}
              analysisResults={analysisResults}
              onboardingData={onboardingData}
            />
          )}
        </div>

        {/* Mobile navigation */}
        <div className="border-t bg-white p-2">
          <div className="flex justify-around">
            <Button
              variant={activeView === "dashboard" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleViewChange("dashboard")}
            >
              Dashboard
            </Button>
            <Button variant="ghost" size="sm" onClick={() => handleFileUpload([])}>
              Upload
            </Button>
            <Button
              variant={activeView === "log" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleViewChange("log")}
            >
              Log
            </Button>
            <Button
              variant={activeView === "datasets" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleViewChange("datasets")}
            >
              Datasets
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
