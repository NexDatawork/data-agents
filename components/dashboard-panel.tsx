"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, BarChart, LineChart, PieChart, MessageSquare, BrainIcon, Brain, FileText, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { BarChart as BarChartComponent } from "@/components/ui/chart"
import { LineChart as LineChartComponent } from "@/components/ui/chart"
import { PieChart as PieChartComponent } from "@/components/ui/chart"
import { PDFExport } from "@/components/pdf-export"
import ReactMarkdown from "react-markdown"
import type { OnboardingData } from "@/components/onboarding-modal"

// Define Message type locally to avoid AI SDK dependency
interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
}

interface DashboardPanelProps {
  messages: Message[]
  onChatSubmit: (message: string) => void
  isAnalyzing: boolean
  analysisResults: any
  onboardingData?: OnboardingData | null
}

export function DashboardPanel({
  messages,
  onChatSubmit,
  isAnalyzing,
  analysisResults,
  onboardingData,
}: DashboardPanelProps) {
  const [activeTab, setActiveTab] = useState("reasoning")
  const [showPDFExport, setShowPDFExport] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // Chat state management without AI SDK
  const [chatMessages, setChatMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  // Handle chat submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isChatLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    }

    setChatMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsChatLoading(true)
    setChatError(null)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [...chatMessages, userMessage],
          csvContext: analysisResults
            ? {
                filename: analysisResults.fileInfo?.filename || "uploaded.csv",
                rows: analysisResults.fileInfo?.rows || 0,
                columns: analysisResults.fileInfo?.columns || 0,
                headers: analysisResults.fileInfo?.columnNames || [],
                quality: analysisResults.fileInfo?.dataQualityScore?.toFixed(1) || "Unknown",
                columnTypes: analysisResults.fileInfo?.columnTypes || {},
                summary: analysisResults.summary || "",
                insights: analysisResults.insights || [],
              }
            : null,
          onboardingData: onboardingData,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.content || data.message || "I apologize, but I couldn't generate a response.",
      }

      setChatMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Chat error:", error)
      setChatError(error instanceof Error ? error.message : "An error occurred")

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error while processing your request. Please try again.",
      }

      setChatMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  // Combine system messages with chat messages
  const allMessages = [...messages, ...chatMessages]

  // Switch to reasoning tab when analysis results become available
  useEffect(() => {
    if (analysisResults && !analysisResults.error) {
      setActiveTab("reasoning")
    }
  }, [analysisResults])

  // Auto-scroll to bottom of messages only when new messages arrive, not during typing
  useEffect(() => {
    if (allMessages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [allMessages.length]) // Only trigger on message count change, not on every render

  // Get the appropriate chart component based on type
  const getChartComponent = (type: string, data: any, options: any) => {
    switch (type) {
      case "bar":
        return <BarChartComponent data={data} options={options} />
      case "line":
        return <LineChartComponent data={data} options={options} />
      case "pie":
        return <PieChartComponent data={data} options={options} />
      default:
        return <BarChartComponent data={data} options={options} />
    }
  }

  // Get the appropriate icon based on chart type
  const getChartIcon = (type: string) => {
    switch (type) {
      case "bar":
        return <BarChart className="h-4 w-4 text-primary" />
      case "line":
        return <LineChart className="h-4 w-4 text-primary" />
      case "pie":
        return <PieChart className="h-4 w-4 text-primary" />
      default:
        return <BarChart className="h-4 w-4 text-primary" />
    }
  }

  // Check if analysis is complete and has results
  const hasAnalysisResults = analysisResults && !analysisResults.error && !isAnalyzing

  // Get personalized welcome message based on onboarding data
  const getPersonalizedWelcome = () => {
    if (!onboardingData) {
      return "Upload a CSV file and run analysis to get insights based on your actual data"
    }

    const roleMessages = {
      ceo: "Upload your business data to get executive-level strategic insights and KPI analysis",
      product: "Upload product data to analyze user behavior, feature adoption, and product performance metrics",
      analyst: "Upload your dataset to perform detailed statistical analysis and discover data patterns",
      marketing: "Upload marketing data to analyze campaign performance, customer acquisition, and conversion metrics",
      operations: "Upload operational data to identify efficiency opportunities and process optimization insights",
      other: "Upload your data to get comprehensive business insights tailored to your needs",
    }

    const goalContext =
      onboardingData.goals.length > 0 ? ` Focus areas: ${onboardingData.goals.slice(0, 2).join(", ")}` : ""

    return `Hi ${onboardingData.firstName}! ${roleMessages[onboardingData.role as keyof typeof roleMessages] || roleMessages.other}.${goalContext}`
  }

  // Enhanced Statistical Insights with comprehensive analysis
  const generateStatisticalInsights = () => {
    if (!analysisResults?.fileInfo) return []

    const insights = []
    const { fileInfo } = analysisResults

    // Dataset Overview
    if (fileInfo.rows && fileInfo.columns) {
      insights.push(
        `📊 **Dataset Overview**: ${fileInfo.rows.toLocaleString()} records across ${fileInfo.columns} variables`,
      )

      // Data density analysis
      const totalDataPoints = fileInfo.rows * fileInfo.columns
      insights.push(
        `📈 **Data Density**: ${totalDataPoints.toLocaleString()} total data points for comprehensive analysis`,
      )
    }

    // Data Quality Assessment
    if (fileInfo.dataQualityScore !== undefined) {
      const score = fileInfo.dataQualityScore
      const qualityRating =
        score > 95
          ? "Exceptional"
          : score > 90
            ? "Excellent"
            : score > 80
              ? "Very Good"
              : score > 70
                ? "Good"
                : score > 50
                  ? "Fair"
                  : "Poor"
      insights.push(`✅ **Data Quality**: ${score.toFixed(1)}% completeness - ${qualityRating} quality rating`)

      if (score > 90) {
        insights.push(
          `🎯 **Quality Impact**: High-quality data enables reliable statistical modeling and accurate insights`,
        )
      } else if (score > 70) {
        insights.push(`⚠️ **Quality Impact**: Good data quality with minor gaps that may require preprocessing`)
      } else {
        insights.push(`🔧 **Quality Impact**: Data quality issues detected - consider data cleaning before analysis`)
      }
    }

    // Variable Type Distribution
    if (fileInfo.columnTypes) {
      const numericCols = Object.values(fileInfo.columnTypes).filter((type) => type === "number").length
      const categoricalCols = Object.values(fileInfo.columnTypes).filter((type) => type === "string").length
      const dateCols = Object.values(fileInfo.columnTypes).filter((type) => type === "date").length

      insights.push(
        `🔢 **Variable Types**: ${numericCols} numeric, ${categoricalCols} categorical, ${dateCols} temporal variables`,
      )

      // Analysis recommendations based on variable types
      if (numericCols > 0) {
        insights.push(
          `📊 **Numeric Analysis**: ${numericCols} quantitative variables enable statistical modeling, correlation analysis, and predictive analytics`,
        )
      }

      if (categoricalCols > 0) {
        insights.push(
          `🏷️ **Categorical Analysis**: ${categoricalCols} qualitative variables support segmentation, classification, and pattern recognition`,
        )
      }

      if (dateCols > 0) {
        insights.push(
          `📅 **Temporal Analysis**: ${dateCols} time-based variables enable trend analysis, seasonality detection, and forecasting`,
        )
      }

      // Statistical power assessment
      const totalVariables = numericCols + categoricalCols + dateCols
      if (totalVariables >= 10) {
        insights.push(
          `💪 **Statistical Power**: Rich dataset with ${totalVariables} variables provides high analytical power`,
        )
      } else if (totalVariables >= 5) {
        insights.push(`📈 **Statistical Power**: Moderate variable count supports focused analytical approaches`)
      } else {
        insights.push(`🎯 **Statistical Power**: Compact dataset ideal for targeted analysis and clear insights`)
      }
    }

    // Sample size assessment
    if (fileInfo.rows) {
      if (fileInfo.rows >= 10000) {
        insights.push(
          `🚀 **Sample Size**: Large dataset (${fileInfo.rows.toLocaleString()} records) enables robust statistical inference and machine learning`,
        )
      } else if (fileInfo.rows >= 1000) {
        insights.push(
          `📊 **Sample Size**: Medium dataset (${fileInfo.rows.toLocaleString()} records) supports reliable statistical analysis`,
        )
      } else if (fileInfo.rows >= 100) {
        insights.push(
          `📈 **Sample Size**: Small dataset (${fileInfo.rows.toLocaleString()} records) suitable for exploratory analysis`,
        )
      } else {
        insights.push(
          `🔍 **Sample Size**: Compact dataset (${fileInfo.rows} records) ideal for detailed case-by-case analysis`,
        )
      }
    }

    return insights
  }

  // Enhanced Categorical Distribution Analysis
  const generateCategoricalInsights = () => {
    if (!analysisResults?.fileInfo?.columnTypes) return []

    const insights = []
    const categoricalColumns = Object.entries(analysisResults.fileInfo.columnTypes)
      .filter(([_, type]) => type === "string")
      .map(([col, _]) => col)

    if (categoricalColumns.length > 0) {
      // Overview
      insights.push(`🏷️ **Categorical Variables**: Identified ${categoricalColumns.length} categorical dimensions`)
      insights.push(
        `📋 **Variable Names**: ${categoricalColumns.slice(0, 5).join(", ")}${categoricalColumns.length > 5 ? ` and ${categoricalColumns.length - 5} more` : ""}`,
      )

      // Distribution analysis potential
      insights.push(
        `📊 **Distribution Analysis**: Each categorical variable reveals unique distribution patterns and frequency distributions`,
      )
      insights.push(
        `🎯 **Segmentation Potential**: ${categoricalColumns.length} categorical variables enable multi-dimensional customer/data segmentation`,
      )

      // Cross-tabulation opportunities
      if (categoricalColumns.length >= 2) {
        insights.push(
          `🔄 **Cross-Analysis**: ${categoricalColumns.length} variables support cross-tabulation analysis and interaction effects`,
        )
        insights.push(
          `📈 **Combination Analysis**: ${Math.min((categoricalColumns.length * (categoricalColumns.length - 1)) / 2, 10)} unique variable pairs for relationship analysis`,
        )
      }

      // Business applications
      insights.push(
        `💼 **Business Applications**: Categorical variables support market segmentation, customer profiling, and behavioral analysis`,
      )
      insights.push(
        `🎨 **Visualization Ready**: Categorical data perfect for bar charts, pie charts, and heatmap visualizations`,
      )

      // Statistical tests recommendations
      if (categoricalColumns.length >= 2) {
        insights.push(
          `🧪 **Statistical Tests**: Chi-square tests, Cramér's V, and association analysis recommended for categorical relationships`,
        )
      }

      // Data quality for categorical variables
      insights.push(
        `✅ **Categorical Quality**: Categorical variables enable data validation, consistency checks, and standardization opportunities`,
      )
    } else {
      insights.push(`📊 **Categorical Analysis**: No categorical variables detected - dataset is primarily numeric`)
      insights.push(
        `🔢 **Data Structure**: Numeric-focused dataset ideal for regression analysis, correlation studies, and mathematical modeling`,
      )
      insights.push(
        `📈 **Analysis Approach**: Consider binning numeric variables to create categorical segments for additional insights`,
      )
      insights.push(
        `🎯 **Recommendation**: Explore creating categorical groups from continuous variables for enhanced segmentation`,
      )
    }

    return insights
  }

  // Enhanced Industry-Specific Insights
  const generateIndustryInsights = () => {
    if (!analysisResults) return []

    const insights = []
    let industryDetected = false

    // Use onboarding data if available
    if (onboardingData?.dataTypes && onboardingData.dataTypes.length > 0) {
      const dataTypes = onboardingData.dataTypes

      if (dataTypes.some((type) => type.toLowerCase().includes("sales"))) {
        industryDetected = true
        insights.push(
          `💰 **Sales Analytics**: Revenue optimization through sales funnel analysis and conversion tracking`,
        )
        insights.push(
          `📊 **Sales Metrics**: Track key performance indicators including conversion rates, average deal size, and sales cycle length`,
        )
        insights.push(
          `🎯 **Sales Forecasting**: Historical sales data enables predictive modeling for future revenue projections`,
        )
        insights.push(
          `👥 **Sales Team Performance**: Analyze individual and team performance metrics for coaching and optimization`,
        )
        insights.push(
          `🏆 **Sales Opportunities**: Identify high-value prospects, seasonal trends, and market expansion opportunities`,
        )
      }

      if (dataTypes.some((type) => type.toLowerCase().includes("customer"))) {
        industryDetected = true
        insights.push(`👤 **Customer Intelligence**: Deep customer behavior analysis and lifecycle management`)
        insights.push(
          `🔄 **Customer Journey**: Map customer touchpoints, engagement patterns, and satisfaction drivers`,
        )
        insights.push(
          `💎 **Customer Segmentation**: RFM analysis, behavioral clustering, and value-based customer grouping`,
        )
        insights.push(
          `📈 **Customer Retention**: Churn prediction, loyalty analysis, and retention strategy optimization`,
        )
        insights.push(
          `🎯 **Customer Acquisition**: CAC analysis, channel effectiveness, and acquisition funnel optimization`,
        )
      }

      if (dataTypes.some((type) => type.toLowerCase().includes("financial"))) {
        industryDetected = true
        insights.push(`💼 **Financial Analysis**: Comprehensive financial performance and risk assessment`)
        insights.push(`📊 **Financial Ratios**: Liquidity, profitability, efficiency, and leverage ratio calculations`)
        insights.push(
          `💹 **Budget Analysis**: Variance analysis, budget vs. actual performance, and cost center evaluation`,
        )
        insights.push(`🔍 **Financial Forecasting**: Cash flow projections, revenue forecasting, and scenario planning`)
        insights.push(
          `⚖️ **Risk Management**: Financial risk assessment, compliance monitoring, and audit trail analysis`,
        )
      }

      if (dataTypes.some((type) => type.toLowerCase().includes("marketing"))) {
        industryDetected = true
        insights.push(`📢 **Marketing Intelligence**: Campaign performance optimization and ROI maximization`)
        insights.push(
          `🎯 **Campaign Analysis**: Multi-channel attribution, conversion tracking, and engagement metrics`,
        )
        insights.push(`📊 **Marketing ROI**: Cost per acquisition, lifetime value, and return on marketing investment`)
        insights.push(`🔄 **Marketing Funnel**: Lead generation, nurturing effectiveness, and conversion optimization`)
        insights.push(
          `📱 **Digital Marketing**: Social media analytics, email performance, and content engagement analysis`,
        )
      }

      if (dataTypes.some((type) => type.toLowerCase().includes("operational"))) {
        industryDetected = true
        insights.push(`⚙️ **Operational Excellence**: Process optimization and efficiency improvement analysis`)
        insights.push(`📈 **Performance Metrics**: KPI tracking, productivity analysis, and operational benchmarking`)
        insights.push(
          `🔧 **Process Optimization**: Bottleneck identification, workflow analysis, and resource allocation`,
        )
        insights.push(
          `⏱️ **Efficiency Analysis**: Time and motion studies, capacity utilization, and throughput optimization`,
        )
        insights.push(`📊 **Quality Management**: Quality control metrics, defect analysis, and continuous improvement`)
      }
    }

    // Infer from column names if no onboarding data
    if (!industryDetected && analysisResults.fileInfo?.columnNames) {
      const columns = analysisResults.fileInfo.columnNames.map((col: string) => col.toLowerCase())

      if (columns.some((col) => col.includes("sales") || col.includes("revenue") || col.includes("price"))) {
        industryDetected = true
        insights.push(`💰 **Sales-Focused Analysis**: Revenue optimization and pricing strategy insights`)
        insights.push(`📊 **Revenue Analytics**: Price elasticity, revenue trends, and sales performance analysis`)
        insights.push(`🎯 **Pricing Strategy**: Competitive pricing analysis and profit margin optimization`)
        insights.push(`📈 **Sales Growth**: Growth rate analysis, market penetration, and expansion opportunities`)
      }

      if (columns.some((col) => col.includes("customer") || col.includes("user") || col.includes("client"))) {
        industryDetected = true
        insights.push(`👥 **Customer-Centric Analysis**: User behavior and engagement pattern analysis`)
        insights.push(`🔍 **User Experience**: Customer satisfaction, usage patterns, and experience optimization`)
        insights.push(`📊 **Customer Analytics**: Demographic analysis, preference mapping, and behavioral insights`)
        insights.push(`🎯 **Customer Success**: Onboarding effectiveness, feature adoption, and success metrics`)
      }

      if (columns.some((col) => col.includes("date") || col.includes("time") || col.includes("timestamp"))) {
        industryDetected = true
        insights.push(`📅 **Temporal Analysis**: Time-series trends and seasonal pattern identification`)
        insights.push(`📊 **Trend Analysis**: Long-term trends, cyclical patterns, and anomaly detection`)
        insights.push(`🔄 **Seasonality**: Seasonal variations, peak periods, and demand forecasting`)
        insights.push(`⏰ **Time-Based Insights**: Hourly, daily, weekly, and monthly pattern analysis`)
      }

      if (columns.some((col) => col.includes("campaign") || col.includes("channel") || col.includes("source"))) {
        industryDetected = true
        insights.push(`📢 **Marketing Analysis**: Channel performance and attribution insights`)
        insights.push(`🎯 **Channel Optimization**: Multi-channel effectiveness and budget allocation`)
        insights.push(`📊 **Attribution Modeling**: Customer journey mapping and touchpoint analysis`)
        insights.push(`💰 **Marketing ROI**: Campaign profitability and cost-effectiveness analysis`)
      }
    }

    // Generic business insights if no specific industry detected
    if (!industryDetected) {
      insights.push(`🏢 **Business Intelligence**: Cross-functional insights and comprehensive business analysis`)
      insights.push(`📊 **Data-Driven Decisions**: Evidence-based insights for strategic business planning`)
      insights.push(`🎯 **Performance Optimization**: Key performance indicators and operational efficiency metrics`)
      insights.push(`📈 **Growth Analysis**: Business growth patterns, opportunity identification, and market analysis`)
      insights.push(`🔍 **Competitive Intelligence**: Market positioning, competitive analysis, and strategic insights`)
      insights.push(
        `💡 **Innovation Opportunities**: Data-driven innovation, process improvement, and optimization potential`,
      )
    }

    // Role-specific recommendations
    if (onboardingData?.role) {
      if (onboardingData.role === "ceo") {
        insights.push(`👔 **Executive Dashboard**: C-level KPIs, strategic metrics, and board-ready insights`)
        insights.push(`🎯 **Strategic Planning**: Long-term trends, market opportunities, and competitive positioning`)
      } else if (onboardingData.role === "analyst") {
        insights.push(`🔬 **Advanced Analytics**: Statistical modeling, predictive analytics, and deep-dive analysis`)
        insights.push(
          `📊 **Data Science**: Machine learning opportunities, correlation analysis, and statistical significance`,
        )
      } else if (onboardingData.role === "marketing") {
        insights.push(
          `📢 **Marketing Optimization**: Campaign performance, audience insights, and conversion optimization`,
        )
        insights.push(`🎯 **Customer Acquisition**: Lead generation, funnel optimization, and retention strategies`)
      } else if (onboardingData.role === "product") {
        insights.push(`🚀 **Product Analytics**: Feature usage, user engagement, and product performance metrics`)
        insights.push(`📊 **Product Optimization**: User experience, feature adoption, and product-market fit analysis`)
      } else if (onboardingData.role === "operations") {
        insights.push(
          `⚙️ **Operational Excellence**: Process efficiency, resource optimization, and performance improvement`,
        )
        insights.push(`📈 **Operational KPIs**: Productivity metrics, quality indicators, and operational benchmarks`)
      }
    }

    return insights
  }

  // Create combined analysis content that includes the enhanced sections
  const getCombinedAnalysisContent = () => {
    let content = analysisResults?.langchainAnalysis || ""

    if (shouldShowEnhancedSections) {
      // Add Statistical Insights section right after main analysis
      if (analysisResults?.fileInfo) {
        content += "\n\n## Statistical Insights\n\n"
        generateStatisticalInsights().forEach((insight) => {
          // Remove emojis from insights
          const cleanInsight = insight
            .replace(
              /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|🧠|🔍|📊|✅|❌|📈|📉|💡|🎯|🔧|⚡|🚀|💰|👥|📅|🏷️|⚙️|📢|🔄|💎|🎨|🧪|💼|📋|🔢|💪|⏱️|⚖️|🏆|🔬|👔|📱|💹/gu,
              "",
            )
            .trim()
          content += `• ${cleanInsight}\n\n`
        })
      }

      // Add Categorical Distribution Analysis section
      if (analysisResults?.fileInfo) {
        content += "\n\n## Categorical Distribution Analysis\n\n"
        generateCategoricalInsights().forEach((insight) => {
          // Remove emojis from insights
          const cleanInsight = insight
            .replace(
              /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|🧠|🔍|📊|✅|❌|📈|📉|💡|🎯|🔧|⚡|🚀|💰|👥|📅|🏷️|⚙️|📢|🔄|💎|🎨|🧪|💼|📋|🔢|💪|⏱️|⚖️|🏆|🔬|👔|📱|💹/gu,
              "",
            )
            .trim()
          content += `• ${cleanInsight}\n\n`
        })
      }

      // Remove Industry-Specific Insights section (commented out)
      // if (analysisResults) {
      //   content += "\n\n## Industry-Specific Insights\n\n"
      //   generateIndustryInsights().forEach((insight) => {
      //     content += `• ${insight}\n\n`
      //   })
      // }
    }

    return content
  }

  // Determine if we should show the enhanced sections
  const shouldShowEnhancedSections = !isAnalyzing && analysisResults && !analysisResults.error

  // Extract and summarize data structure insights from Data Brain analysis
  const getDataStructureAnalysis = () => {
    if (!analysisResults?.langchainAnalysis) {
      // Enhanced fallback basic analysis with better formatting
      const columnTypes = analysisResults?.fileInfo?.columnTypes || {}
      const numericCols = Object.values(columnTypes).filter((type) => type === "number").length
      const categoricalCols = Object.values(columnTypes).filter((type) => type === "string").length
      const dateCols = Object.values(columnTypes).filter((type) => type === "date").length
      const rows = analysisResults?.fileInfo?.rows || 0
      const columns = analysisResults?.fileInfo?.columns || 0
      const quality = analysisResults?.fileInfo?.dataQualityScore || 0

      return `## Dataset Overview
This dataset contains **${rows.toLocaleString()} records** across **${columns} variables**, providing a comprehensive foundation for analytical exploration.

## Variable Composition
• **${numericCols} numeric variables** - suitable for quantitative analysis
• **${categoricalCols} categorical variables** - enabling segmentation and classification  
• **${dateCols} temporal variables** - supporting time-series analysis

## Data Quality Assessment
The dataset demonstrates **${quality > 90 ? "exceptional" : quality > 80 ? "high" : quality > 70 ? "good" : "moderate"} data quality** with **${quality.toFixed(1)}% completeness**, indicating ${quality > 90 ? "minimal data preprocessing requirements and high reliability for statistical modeling" : quality > 80 ? "minor data cleaning needs with strong analytical potential" : "some data quality considerations that should be addressed before advanced analysis"}.

## Statistical Capabilities
The **${numericCols > categoricalCols ? "quantitative-heavy structure" : categoricalCols > numericCols ? "categorical-rich composition" : "balanced variable distribution"}** enables:
• ${numericCols > categoricalCols ? "Robust statistical modeling, correlation analysis, regression techniques, and predictive analytics" : categoricalCols > numericCols ? "Comprehensive segmentation analysis, classification modeling, and categorical relationship exploration" : "Versatile analytical approaches combining both quantitative and qualitative methodologies"}

## Sample Size Analysis
With **${rows.toLocaleString()} observations**, this dataset provides:
• ${rows >= 10000 ? "Substantial statistical power for advanced machine learning algorithms" : rows >= 1000 ? "Adequate statistical power for most analytical techniques" : "Sufficient data for exploratory analysis and preliminary insights"}
• ${rows >= 10000 ? "Complex modeling techniques and reliable inference with high confidence intervals" : rows >= 1000 ? "Reliable hypothesis testing and meaningful pattern detection" : "Basic statistical testing and preliminary insights generation"}

## Variable Density Analysis
• **${Math.round((numericCols / columns) * 100)}% numeric content** ${numericCols > 5 ? "- optimal for mathematical modeling and statistical inference" : ""}
• **${Math.round((categoricalCols / columns) * 100)}% categorical content** ${categoricalCols > 3 ? "- ideal for behavioral analysis and market segmentation" : ""}
• **${Math.round((dateCols / columns) * 100)}% temporal content** ${dateCols > 0 ? "- suitable for trend analysis and forecasting" : ""}`
    }

    // Enhanced extraction from Data Brain analysis with better formatting
    const brainAnalysis = analysisResults.langchainAnalysis

    // Clean and normalize the text more thoroughly
    const cleanText = brainAnalysis
      .replace(/#{1,6}\s*/g, "") // Remove markdown headers
      .replace(/\*\*(.*?)\*\*/g, "$1") // Remove bold formatting
      .replace(/\*(.*?)\*/g, "$1") // Remove italic formatting
      .replace(/`(.*?)`/g, "$1") // Remove code formatting
      .replace(/\[(.*?)\]$$.*?$$/g, "$1") // Remove links, keep text
      .replace(
        /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]/gu,
        "",
      ) // Remove emojis
      .replace(/\n+/g, " ") // Replace newlines with spaces
      .replace(/\s+/g, " ") // Normalize whitespace
      .trim()

    // Extract comprehensive data structure content
    const structureKeywords = [
      "structure",
      "columns",
      "variables",
      "data types",
      "statistical",
      "quantitative",
      "categorical",
      "numeric",
      "sample size",
      "dataset",
      "rows",
      "completeness",
      "quality",
      "analysis",
      "methodology",
      "observations",
      "records",
      "dimensions",
      "distribution",
      "variance",
      "correlation",
      "modeling",
      "inference",
      "statistical power",
      "data integrity",
      "preprocessing",
      "validation",
    ]

    // Get all relevant sentences
    const allSentences = cleanText.split(/[.!?]+/).filter((sentence) => {
      const lowerSentence = sentence.toLowerCase()
      return (
        structureKeywords.some((keyword) => lowerSentence.includes(keyword)) &&
        sentence.trim().length > 20 &&
        !sentence.toLowerCase().includes("final answer") &&
        !sentence.toLowerCase().includes("methodology section") &&
        !sentence.toLowerCase().includes("data evidence")
      )
    })

    // Build formatted summary with sections
    const sections = []
    const usedSentences = new Set()

    // Group sentences by topic
    const topicGroups = {
      "Dataset Overview": ["structure", "dataset", "records", "observations", "rows", "columns"],
      "Data Quality": ["quality", "completeness", "validation", "integrity"],
      "Variable Analysis": ["variables", "numeric", "categorical", "quantitative", "data types"],
      "Statistical Power": ["statistical", "analysis", "modeling", "inference", "correlation"],
    }

    Object.entries(topicGroups).forEach(([topic, keywords]) => {
      const topicSentences = allSentences.filter((sentence) => {
        const lowerSentence = sentence.toLowerCase()
        return (
          keywords.some((keyword) => lowerSentence.includes(keyword)) &&
          !usedSentences.has(sentence) &&
          sentence.length > 30 &&
          sentence.length < 200
        )
      })

      if (topicSentences.length > 0) {
        const selectedSentences = topicSentences.slice(0, 2)
        sections.push(`## ${topic}\n${selectedSentences.map((s) => `• ${s.trim()}`).join("\n")}\n`)
        selectedSentences.forEach((s) => usedSentences.add(s))
      }
    })

    // If no structured content found, create basic structure
    if (sections.length === 0) {
      const columnTypes = analysisResults?.fileInfo?.columnTypes || {}
      const numericCols = Object.values(columnTypes).filter((type) => type === "number").length
      const categoricalCols = Object.values(columnTypes).filter((type) => type === "string").length
      const rows = analysisResults?.fileInfo?.rows || 0
      const quality = analysisResults?.fileInfo?.dataQualityScore || 0

      sections.push(
        `## Dataset Architecture\n• The dataset demonstrates **${numericCols > categoricalCols ? "quantitative dominance" : categoricalCols > numericCols ? "categorical richness" : "balanced composition"}** with ${numericCols} numeric and ${categoricalCols} categorical variables\n• Analysis covers **${rows.toLocaleString()} observations** across multiple dimensions\n`,
      )

      sections.push(
        `## Quality Assessment\n• Data quality score of **${quality.toFixed(1)}%** indicates ${quality > 90 ? "exceptional reliability suitable for production-level analytics" : quality > 80 ? "high confidence for most analytical applications" : "good foundation with minor preprocessing requirements"}\n• ${quality > 90 ? "Minimal data cleaning required" : quality > 80 ? "Minor preprocessing may be beneficial" : "Some data quality considerations should be addressed"}\n`,
      )

      sections.push(
        `## Analytical Capabilities\n• Statistical power analysis suggests **${rows >= 10000 ? "robust capabilities for machine learning and complex modeling" : rows >= 1000 ? "adequate sample size for reliable hypothesis testing and pattern detection" : "sufficient data for exploratory analysis and preliminary insights"}**\n• Dataset structure supports ${numericCols > 5 ? "advanced statistical modeling including regression analysis and predictive analytics" : "focused quantitative analysis with reliable statistical inference"}\n`,
      )
    }

    return sections.join("\n")
  }

  // Extract and summarize business context from Data Brain analysis
  const getBusinessContextAnalysis = () => {
    if (!analysisResults?.langchainAnalysis) {
      // Enhanced fallback business analysis
      let context = ""
      const columnNames = analysisResults?.fileInfo?.columnNames || []
      const rows = analysisResults?.fileInfo?.rows || 0
      const columns = analysisResults?.fileInfo?.columns || 0

      if (onboardingData?.dataTypes?.length > 0) {
        const dataType = onboardingData.dataTypes[0].toLowerCase()
        const role = onboardingData.role
        const goals = onboardingData.goals || []

        if (dataType.includes("sales")) {
          context = `This sales-focused dataset provides comprehensive revenue intelligence capabilities essential for ${role === "ceo" ? "executive strategic planning and board-level reporting" : role === "marketing" ? "campaign optimization and customer acquisition analysis" : role === "analyst" ? "detailed sales performance modeling and forecasting" : "sales process optimization and performance tracking"}. 

The data structure enables advanced sales analytics including revenue trend analysis, customer lifetime value calculations, sales funnel optimization, and predictive revenue modeling. With ${rows.toLocaleString()} sales records, the dataset supports robust statistical analysis for identifying high-performing segments, seasonal patterns, and growth opportunities.

Key business applications include sales forecasting with confidence intervals, customer segmentation for targeted strategies, pricing optimization analysis, and performance benchmarking across different dimensions. The analytical framework supports ${goals.includes("Increase revenue") ? "revenue growth initiatives through data-driven insights" : goals.includes("Improve efficiency") ? "sales process efficiency improvements and resource optimization" : "comprehensive sales performance enhancement strategies"}.

Advanced analytics capabilities include cohort analysis for customer retention, attribution modeling for marketing effectiveness, and predictive modeling for future sales performance. The dataset enables identification of key performance drivers, optimization of sales territories, and development of data-driven compensation strategies.`
        } else if (dataType.includes("customer")) {
          context = `This customer-centric dataset delivers comprehensive behavioral intelligence and lifecycle management capabilities crucial for ${role === "ceo" ? "strategic customer initiatives and market positioning" : role === "marketing" ? "personalized marketing campaigns and customer experience optimization" : role === "product" ? "user experience enhancement and feature adoption analysis" : "customer relationship management and retention strategies"}.

The analytical framework supports advanced customer analytics including behavioral segmentation, lifetime value modeling, churn prediction, and engagement optimization. With ${rows.toLocaleString()} customer records, the dataset enables sophisticated analysis of customer journeys, preference patterns, and satisfaction drivers.

Business intelligence applications encompass customer acquisition cost analysis, retention strategy optimization, cross-selling and upselling opportunity identification, and customer satisfaction measurement. The data supports ${goals.includes("Improve customer satisfaction") ? "customer satisfaction enhancement through data-driven experience improvements" : goals.includes("Increase revenue") ? "revenue growth through customer value optimization and retention strategies" : "comprehensive customer relationship optimization initiatives"}.

Advanced capabilities include predictive customer scoring, personalization engine development, customer health monitoring, and automated retention intervention systems. The dataset enables development of customer success metrics, loyalty program optimization, and data-driven customer service improvements.`
        } else if (dataType.includes("financial")) {
          context = `This financial dataset provides comprehensive performance analysis and risk assessment capabilities essential for ${role === "ceo" ? "strategic financial planning and investor reporting" : role === "analyst" ? "detailed financial modeling and variance analysis" : role === "operations" ? "operational cost management and budget optimization" : "financial performance monitoring and compliance"}.

The analytical framework enables advanced financial analytics including profitability analysis, cash flow forecasting, budget variance analysis, and financial ratio calculations. With ${rows.toLocaleString()} financial records, the dataset supports sophisticated analysis of revenue streams, cost structures, and financial performance drivers.

Key business applications include financial forecasting with scenario modeling, cost center analysis, profitability optimization, and risk assessment frameworks. The data supports ${goals.includes("Reduce costs") ? "cost reduction initiatives through detailed expense analysis and optimization opportunities" : goals.includes("Improve efficiency") ? "operational efficiency improvements and resource allocation optimization" : "comprehensive financial performance enhancement strategies"}.

Advanced analytics capabilities include predictive financial modeling, automated anomaly detection, compliance monitoring, and performance benchmarking. The dataset enables development of financial KPIs, budget optimization strategies, and data-driven investment decision support systems.`
        } else {
          context = `This comprehensive business dataset provides multi-dimensional analytical capabilities supporting executive decision-making and strategic planning initiatives. The analytical framework enables cross-functional insights including performance trend analysis, operational efficiency measurement, and strategic opportunity identification. With ${rows.toLocaleString()} records across ${columns} dimensions, the dataset supports sophisticated business intelligence applications and decision support systems.

Business applications encompass performance monitoring, trend analysis, competitive intelligence, and strategic planning support. The data enables ${goals.length > 0 ? `targeted initiatives aligned with stated objectives: ${goals.slice(0, 2).join(" and ")}` : "comprehensive business optimization across multiple operational dimensions"}.

Advanced capabilities include predictive analytics, automated reporting systems, performance benchmarking, and strategic decision support. The dataset enables development of business KPIs, optimization strategies, and data-driven operational improvements across the organization.`
        }
      } else {
        // Infer from column names
        const lowerColumns = columnNames.map((col: string) => col.toLowerCase())

        if (lowerColumns.some((col) => col.includes("sales") || col.includes("revenue") || col.includes("price"))) {
          context = `This revenue-focused dataset provides comprehensive sales intelligence and pricing strategy capabilities. The analytical framework enables advanced revenue optimization through sales performance analysis, pricing elasticity studies, and market penetration assessment. With ${rows.toLocaleString()} records, the dataset supports sophisticated revenue modeling, competitive analysis, and growth opportunity identification. Key applications include sales forecasting, pricing optimization, market share analysis, and revenue stream diversification strategies. Advanced analytics capabilities enable predictive revenue modeling, customer value optimization, and data-driven pricing strategies that maximize profitability while maintaining market competitiveness.`
        } else if (
          lowerColumns.some((col) => col.includes("customer") || col.includes("user") || col.includes("client"))
        ) {
          context = `This customer-intelligence dataset delivers comprehensive user behavior analysis and engagement optimization capabilities. The analytical framework supports advanced customer analytics including behavioral segmentation, engagement pattern analysis, and customer journey optimization. With ${rows.toLocaleString()} user records, the dataset enables sophisticated analysis of user preferences, interaction patterns, and satisfaction drivers. Business applications include customer experience optimization, retention strategy development, personalization engine creation, and customer success measurement. Advanced capabilities encompass predictive customer modeling, automated engagement systems, and data-driven customer relationship management strategies.`
        } else {
          context = `This comprehensive business dataset provides multi-dimensional analytical capabilities supporting strategic decision-making and operational optimization. The analytical framework enables cross-functional insights including performance analysis, trend identification, and opportunity assessment. With ${rows.toLocaleString()} records across ${columns} variables, the dataset supports sophisticated business intelligence applications and strategic planning initiatives. Key applications include performance monitoring, competitive analysis, operational efficiency measurement, and strategic opportunity identification. Advanced analytics capabilities enable predictive modeling, automated insights generation, and data-driven decision support systems across multiple business functions.`
        }
      }

      return context.substring(0, 2000)
    }

    // Enhanced extraction from Data Brain analysis
    const brainAnalysis = analysisResults.langchainAnalysis

    // Clean and normalize the text
    const cleanText = brainAnalysis
      .replace(/#{1,6}\s*/g, "") // Remove markdown headers
      .replace(/\*\*(.*?)\*\*/g, "$1") // Remove bold formatting
      .replace(/\*(.*?)\*/g, "$1") // Remove italic formatting
      .replace(/`(.*?)`/g, "$1") // Remove code formatting
      .replace(/\[(.*?)\]$$.*?$$/g, "$1") // Remove links, keep text
      .replace(
        /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]/gu,
        "",
      ) // Remove emojis
      .replace(/\n+/g, " ") // Replace newlines with spaces
      .replace(/\s+/g, " ") // Normalize whitespace
      .trim()

    // Extract business and application related content
    const businessKeywords = [
      "business",
      "insights",
      "opportunities",
      "recommendations",
      "strategy",
      "performance",
      "optimization",
      "trends",
      "patterns",
      "applications",
      "value",
      "impact",
      "sales",
      "revenue",
      "correlation",
      "findings",
      "analysis",
      "intelligence",
      "decision",
      "strategic",
      "operational",
      "efficiency",
      "growth",
      "market",
      "competitive",
      "customer",
      "engagement",
      "retention",
      "acquisition",
      "satisfaction",
      "experience",
    ]

    // Get all relevant sentences
    const allSentences = cleanText.split(/[.!?]+/).filter((sentence) => {
      const lowerSentence = sentence.toLowerCase()
      return (
        businessKeywords.some((keyword) => lowerSentence.includes(keyword)) &&
        sentence.trim().length > 25 &&
        !sentence.toLowerCase().includes("final answer") &&
        !sentence.toLowerCase().includes("methodology section") &&
        !sentence.toLowerCase().includes("data evidence")
      )
    })

    // Build comprehensive business context summary
    let summary = ""
    const usedSentences = new Set()

    // Prioritize sentences about business insights and applications
    const priorityKeywords = [
      "business",
      "insights",
      "opportunities",
      "strategy",
      "performance",
      "optimization",
      "applications",
      "value",
    ]

    priorityKeywords.forEach((keyword) => {
      const keywordSentences = allSentences.filter(
        (sentence) =>
          sentence.toLowerCase().includes(keyword) &&
          !usedSentences.has(sentence) &&
          sentence.length > 30 &&
          sentence.length < 300,
      )

      keywordSentences.slice(0, 2).forEach((sentence) => {
        if (summary.length + sentence.length < 1700) {
          summary += sentence.trim() + ". "
          usedSentences.add(sentence)
        }
      })
    })

    // Add findings and recommendations if available
    const findingsKeywords = [
      "findings",
      "reveals",
      "indicates",
      "suggests",
      "demonstrates",
      "shows",
      "correlation",
      "trend",
    ]

    findingsKeywords.forEach((keyword) => {
      const keywordSentences = allSentences.filter(
        (sentence) =>
          sentence.toLowerCase().includes(keyword) &&
          !usedSentences.has(sentence) &&
          sentence.length > 40 &&
          sentence.length < 250,
      )

      keywordSentences.slice(0, 1).forEach((sentence) => {
        if (summary.length + sentence.length < 1800) {
          summary += sentence.trim() + ". "
          usedSentences.add(sentence)
        }
      })
    })

    // If still too short, enhance with contextual business analysis
    if (summary.length < 600) {
      const columnNames = analysisResults?.fileInfo?.columnNames || []
      const rows = analysisResults?.fileInfo?.rows || 0

      summary += ` This dataset enables comprehensive business intelligence through advanced analytical capabilities across ${columnNames.length} data dimensions. The business context reveals opportunities for ${onboardingData?.role === "ceo" ? "strategic decision-making and executive-level insights" : onboardingData?.role === "marketing" ? "marketing optimization and customer engagement strategies" : onboardingData?.role === "analyst" ? "detailed statistical analysis and predictive modeling" : "operational improvements and performance optimization"}. 

With ${rows.toLocaleString()} records, the analytical framework supports sophisticated business applications including performance monitoring, trend analysis, competitive intelligence, and strategic planning. The data structure enables identification of key business drivers, optimization opportunities, and actionable insights for ${onboardingData?.goals?.length > 0 ? `achieving stated objectives: ${onboardingData.goals.slice(0, 2).join(" and ")}` : "comprehensive business improvement initiatives"}. 

Advanced business intelligence capabilities include predictive analytics for forecasting, automated insight generation for real-time decision support, and comprehensive reporting frameworks for stakeholder communication. The dataset provides foundation for data-driven strategies, performance optimization, and competitive advantage development.`
    }

    return summary.substring(0, 2000)
  }

  return (
    <>
      <div className="w-full h-full bg-white rounded-xl shadow-sm border border-border/30 flex flex-col overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <div className="px-4 pt-4">
            <div className="flex items-center justify-between mb-4">
              <TabsList className="bg-secondary">
                <TabsTrigger value="reasoning" className="flex items-center gap-2 data-[state=active]:bg-white">
                  <BrainIcon className="h-4 w-4" />
                  Data Brain
                </TabsTrigger>
                <TabsTrigger value="dashboard" className="flex items-center gap-2 data-[state=active]:bg-white">
                  <BarChart className="h-4 w-4" />
                  Dashboard
                </TabsTrigger>
                <TabsTrigger value="chat" className="flex items-center gap-2 data-[state=active]:bg-white">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                </TabsTrigger>
              </TabsList>

              {/* Export to PDF Button - only show when analysis is complete */}
              {hasAnalysisResults && (
                <Button
                  onClick={() => setShowPDFExport(true)}
                  variant="outline"
                  className="flex items-center gap-2 border-violet-200 text-violet-700 hover:bg-violet-50"
                >
                  <FileText className="h-4 w-4" />
                  Export to PDF
                </Button>
              )}
            </div>
          </div>

          <TabsContent value="dashboard" className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <BarChart className="h-5 w-5 text-primary" />
                {onboardingData ? `${onboardingData.firstName}'s Data Analysis Dashboard` : "Data Analysis Dashboard"}
              </h2>

              {!analysisResults || analysisResults.error ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-8">
                  <div className="bg-primary/10 rounded-full p-4 mb-4">
                    <BarChart className="h-12 w-12 text-violet-600" />
                  </div>
                  <h3 className="text-lg font-medium">
                    {analysisResults?.error
                      ? "Analysis Error"
                      : onboardingData
                        ? `Welcome ${onboardingData.firstName}!`
                        : "No Analysis Results Yet"}
                  </h3>
                  <p className="text-muted-foreground mt-2 max-w-lg">
                    {analysisResults?.error
                      ? "There was an issue processing your CSV file. Please check the file format and try again."
                      : getPersonalizedWelcome()}
                  </p>
                  {onboardingData && (
                    <div className="mt-4 p-4 bg-violet-50 rounded-lg border border-violet-200 max-w-md">
                      <p className="text-sm text-violet-700">
                        <strong>Your Profile:</strong>{" "}
                        {onboardingData.role === "ceo"
                          ? "CEO"
                          : onboardingData.role === "product"
                            ? "Product Manager"
                            : onboardingData.role === "analyst"
                              ? "Data Analyst"
                              : onboardingData.role === "marketing"
                                ? "Marketing Professional"
                                : onboardingData.role === "operations"
                                  ? "Operations Manager"
                                  : "Professional"}
                        {onboardingData.goals.length > 0 && (
                          <span> • Goals: {onboardingData.goals.slice(0, 2).join(", ")}</span>
                        )}
                      </p>
                    </div>
                  )}
                  {analysisResults?.insights && (
                    <div className="mt-4 text-sm text-muted-foreground max-w-md">
                      <ul className="space-y-1">
                        {analysisResults.insights.map((insight: string, index: number) => (
                          <li key={index}>• {insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {isAnalyzing && (
                    <div className="mt-4 flex items-center gap-2 text-violet-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-violet-600"></div>
                      <span className="text-sm">AI analysis in progress...</span>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  {/* Comprehensive Dataset Overview */}
                  <Card className="bg-white">
                    <CardHeader className="pb-2">
                      <CardTitle>
                        {onboardingData ? `${onboardingData.firstName}'s Dataset Overview` : "Dataset Overview"}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Basic File Information */}
                        <div className="space-y-3">
                          <h4 className="font-medium text-gray-900">File Information</h4>
                          <div className="space-y-2 text-sm">
                            <div>
                              <p className="text-muted-foreground">Filename</p>
                              <p className="font-medium">{analysisResults.fileInfo?.filename || "Unknown"}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Total Records</p>
                              <p className="font-medium text-blue-600">
                                {analysisResults.fileInfo?.rows?.toLocaleString() || "0"}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Total Columns</p>
                              <p className="font-medium text-green-600">{analysisResults.fileInfo?.columns || "0"}</p>
                            </div>
                          </div>
                        </div>

                        {/* Column Type Distribution */}
                        <div className="space-y-3">
                          <h4 className="font-medium text-gray-900">Column Types</h4>
                          <div className="space-y-2 text-sm">
                            {(() => {
                              const columnTypes = analysisResults.fileInfo?.columnTypes || {}
                              const numericCols = Object.values(columnTypes).filter((type) => type === "number").length
                              const categoricalCols = Object.values(columnTypes).filter(
                                (type) => type === "string",
                              ).length
                              const dateCols = Object.values(columnTypes).filter((type) => type === "date").length

                              return (
                                <>
                                  <div>
                                    <p className="text-muted-foreground">Numeric Columns</p>
                                    <p className="font-medium text-purple-600">{numericCols}</p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">Categorical Columns</p>
                                    <p className="font-medium text-orange-600">{categoricalCols}</p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground">Date Columns</p>
                                    <p className="font-medium text-teal-600">{dateCols}</p>
                                  </div>
                                </>
                              )
                            })()}
                          </div>
                        </div>

                        {/* Data Quality Metrics */}
                        <div className="space-y-3">
                          <h4 className="font-medium text-gray-900">Data Quality</h4>
                          <div className="space-y-2 text-sm">
                            <div>
                              <p className="text-muted-foreground">Completeness Score</p>
                              <p className="font-medium text-green-600">
                                {analysisResults.fileInfo?.dataQualityScore?.toFixed(1) || "Unknown"}%
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Quality Rating</p>
                              <p className="font-medium">
                                {(() => {
                                  const score = analysisResults.fileInfo?.dataQualityScore || 0
                                  return score > 95
                                    ? "Exceptional"
                                    : score > 90
                                      ? "Excellent"
                                      : score > 80
                                        ? "Very Good"
                                        : score > 70
                                          ? "Good"
                                          : "Fair"
                                })()}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Missing Data</p>
                              <p className="font-medium">
                                {analysisResults.insights?.some((i: string) => i.includes("No missing"))
                                  ? "None detected"
                                  : "Minor gaps"}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Statistical Summary */}
                        <div className="space-y-3">
                          <h4 className="font-medium text-gray-900">Statistical Summary</h4>
                          <div className="space-y-2 text-sm">
                            <div>
                              <p className="text-muted-foreground">Data Points</p>
                              <p className="font-medium text-indigo-600">
                                {(
                                  (analysisResults.fileInfo?.rows || 0) * (analysisResults.fileInfo?.columns || 0)
                                ).toLocaleString()}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Analysis Scope</p>
                              <p className="font-medium">
                                {(analysisResults.fileInfo?.rows || 0) >= 10000
                                  ? "Large Dataset"
                                  : (analysisResults.fileInfo?.rows || 0) >= 1000
                                    ? "Medium Dataset"
                                    : "Small Dataset"}
                              </p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Analytical Power</p>
                              <p className="font-medium">
                                {(analysisResults.fileInfo?.columns || 0) >= 10
                                  ? "High"
                                  : (analysisResults.fileInfo?.columns || 0) >= 5
                                    ? "Moderate"
                                    : "Focused"}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Column Details */}
                    </CardContent>
                  </Card>

                  {/* Enhanced Analysis Summary */}
                  <Card className="bg-white">
                    <CardHeader className="pb-2">
                      <CardTitle>
                        {onboardingData?.role === "ceo"
                          ? "Executive Summary"
                          : onboardingData?.role === "analyst"
                            ? "Statistical Analysis Summary"
                            : onboardingData?.role === "marketing"
                              ? "Marketing Analysis Summary"
                              : onboardingData?.role === "operations"
                                ? "Operations Analysis Summary"
                                : "Analysis Summary"}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              h1: ({ children }) => (
                                <h1 className="text-lg font-bold text-gray-900 mb-3 mt-4 first:mt-0">{children}</h1>
                              ),
                              h2: ({ children }) => (
                                <h2 className="text-base font-semibold text-gray-800 mb-2 mt-4 first:mt-0">
                                  {children}
                                </h2>
                              ),
                              h3: ({ children }) => (
                                <h3 className="text-sm font-medium text-gray-700 mb-2 mt-3 first:mt-0">{children}</h3>
                              ),
                              h4: ({ children }) => (
                                <h4 className="text-sm font-medium text-gray-700 mb-2 mt-3 first:mt-0">{children}</h4>
                              ),
                              p: ({ children }) => <p className="text-gray-700 mb-3 leading-relaxed">{children}</p>,
                              ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                              ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                              li: ({ children }) => <li className="text-gray-700 text-sm">{children}</li>,
                              strong: ({ children }) => (
                                <strong className="font-semibold text-gray-900">{children}</strong>
                              ),
                              em: ({ children }) => <em className="italic text-gray-600">{children}</em>,
                              blockquote: ({ children }) => (
                                <blockquote className="border-l-4 border-blue-300 pl-4 italic text-gray-600 mb-4 bg-blue-50 py-2">
                                  {children}
                                </blockquote>
                              ),
                              code: ({ children }) => (
                                <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800">
                                  {children}
                                </code>
                              ),
                              hr: () => <hr className="my-4 border-gray-200" />,
                            }}
                          >
                            {(() => {
                              const content =
                                analysisResults.langchainAnalysis ||
                                analysisResults.summary ||
                                "No analysis available yet. Please run the analysis to see LangChain-powered insights."

                              // Filter content to only show Executive Summary, Data Evidence, and Final Answer
                              const lines = content.split("\n")
                              const filteredLines = []
                              let includeSection = false

                              for (const line of lines) {
                                if (
                                  line.toLowerCase().includes("executive summary") ||
                                  line.toLowerCase().includes("data evidence") ||
                                  line.toLowerCase().includes("final answer")
                                ) {
                                  includeSection = true
                                  filteredLines.push(line)
                                } else if (line.startsWith("##") || line.startsWith("#")) {
                                  // New section header - check if we should include it
                                  includeSection = false
                                } else if (includeSection) {
                                  filteredLines.push(line)
                                }
                              }

                              return filteredLines.join("\n")
                            })()}
                          </ReactMarkdown>
                        </div>

                        {/* Context-based insights - stacked layout */}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Clean Key Insights */}

                  {/* Enhanced Visualizations with Appropriate Chart Types */}

                  {/* Enhanced Visualizations with Proper Chart Types */}
                  {analysisResults.visualizations && analysisResults.visualizations.length > 0 && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {analysisResults.visualizations.map((viz: any, index: number) => {
                        // Enhanced chart type determination
                        const columnTypes = analysisResults.fileInfo?.columnTypes || {}
                        const isNumericalData = viz.data?.datasets?.[0]?.data?.every(
                          (val: any) => typeof val === "number" && !isNaN(val),
                        )
                        const hasMultipleDataPoints = viz.data?.labels?.length > 1

                        let chartType = viz.type
                        let chartData = viz.data
                        let chartTitle = viz.title

                        // Determine optimal chart type based on data characteristics
                        if (viz.data?.labels && viz.data?.datasets?.[0]?.data) {
                          const dataValues = viz.data.datasets[0].data
                          const labels = viz.data.labels

                          // For categorical data with reasonable number of categories (2-8), use pie chart
                          if (labels.length >= 2 && labels.length <= 8 && isNumericalData) {
                            chartType = "pie"
                            chartTitle = `${viz.title} - Distribution Analysis`
                            chartData = {
                              labels: labels,
                              datasets: [
                                {
                                  data: dataValues,
                                  backgroundColor: [
                                    "rgba(59, 130, 246, 0.8)", // Blue
                                    "rgba(34, 197, 94, 0.8)", // Green
                                    "rgba(168, 85, 247, 0.8)", // Purple
                                    "rgba(251, 146, 60, 0.8)", // Orange
                                    "rgba(239, 68, 68, 0.8)", // Red
                                    "rgba(14, 165, 233, 0.8)", // Sky
                                    "rgba(139, 92, 246, 0.8)", // Violet
                                    "rgba(34, 197, 94, 0.8)", // Emerald
                                  ],
                                  borderColor: [
                                    "rgba(59, 130, 246, 1)",
                                    "rgba(34, 197, 94, 1)",
                                    "rgba(168, 85, 247, 1)",
                                    "rgba(251, 146, 60, 1)",
                                    "rgba(239, 68, 68, 1)",
                                    "rgba(14, 165, 233, 1)",
                                    "rgba(139, 92, 246, 1)",
                                    "rgba(34, 197, 94, 1)",
                                  ],
                                  borderWidth: 2,
                                },
                              ],
                            }
                          }
                          // For time-series or sequential data, use line chart
                          else if (
                            labels.some(
                              (label: string) =>
                                typeof label === "string" &&
                                (label.includes("2023") ||
                                  label.includes("2024") ||
                                  label.includes("Jan") ||
                                  label.includes("Q") ||
                                  label.match(/^\d{4}/) ||
                                  label.match(/\d{1,2}\/\d{1,2}/)),
                            )
                          ) {
                            chartType = "line"
                            chartTitle = `${viz.title} - Trend Analysis`
                            chartData = {
                              ...viz.data,
                              datasets: viz.data.datasets.map((dataset: any) => ({
                                ...dataset,
                                borderColor: "rgba(59, 130, 246, 1)",
                                backgroundColor: "rgba(59, 130, 246, 0.1)",
                                borderWidth: 3,
                                fill: true,
                                tension: 0.4,
                              })),
                            }
                          }
                          // For comparative data with many categories, use bar chart
                          else if (labels.length > 8 || !isNumericalData) {
                            chartType = "bar"
                            chartTitle = `${viz.title} - Comparative Analysis`
                            chartData = {
                              ...viz.data,
                              datasets: viz.data.datasets.map((dataset: any) => ({
                                ...dataset,
                                backgroundColor: "rgba(59, 130, 246, 0.8)",
                                borderColor: "rgba(59, 130, 246, 1)",
                                borderWidth: 2,
                              })),
                            }
                          }
                        }

                        return (
                          <Card key={index} className="bg-white">
                            <CardHeader className="pb-2">
                              <CardTitle className="flex items-center gap-2">
                                <div className="bg-primary/10 rounded-full p-1.5">{getChartIcon(chartType)}</div>
                                {chartTitle}
                                <span className="text-xs text-muted-foreground ml-auto">
                                  {chartType === "pie"
                                    ? "Distribution"
                                    : chartType === "line"
                                      ? "Trend"
                                      : chartType === "bar"
                                        ? "Comparative"
                                        : "Data"}{" "}
                                  View
                                </span>
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="h-[350px]">
                                {getChartComponent(chartType, chartData, {
                                  responsive: true,
                                  maintainAspectRatio: false,
                                  plugins: {
                                    legend: {
                                      position: chartType === "pie" ? "right" : "top",
                                      labels: {
                                        boxWidth: 12,
                                        padding: 15,
                                        usePointStyle: chartType === "pie",
                                      },
                                    },
                                    tooltip: {
                                      backgroundColor: "rgba(0, 0, 0, 0.8)",
                                      titleColor: "white",
                                      bodyColor: "white",
                                      borderColor: "rgba(255, 255, 255, 0.1)",
                                      borderWidth: 1,
                                      callbacks:
                                        chartType === "pie"
                                          ? {
                                              label: (context: any) => {
                                                const total = context.dataset.data.reduce(
                                                  (a: number, b: number) => a + b,
                                                  0,
                                                )
                                                const percentage = ((context.parsed * 100) / total).toFixed(1)
                                                return `${context.label}: ${context.parsed} (${percentage}%)`
                                              },
                                            }
                                          : undefined,
                                    },
                                  },
                                  scales:
                                    chartType !== "pie"
                                      ? {
                                          y: {
                                            beginAtZero: true,
                                            grid: {
                                              color: "rgba(0, 0, 0, 0.1)",
                                            },
                                            ticks: {
                                              color: "rgba(0, 0, 0, 0.7)",
                                            },
                                          },
                                          x: {
                                            grid: {
                                              color: "rgba(0, 0, 0, 0.05)",
                                            },
                                            ticks: {
                                              color: "rgba(0, 0, 0, 0.7)",
                                              maxRotation: 45,
                                            },
                                          },
                                        }
                                      : undefined,
                                })}
                              </div>
                            </CardContent>
                          </Card>
                        )
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          </TabsContent>

          <TabsContent value="reasoning" className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Brain className="h-5 w-5 text-violet-600" />
                {onboardingData ? `Data Brain Analysis for ${onboardingData.firstName}` : "Data Brain Analysis"}
              </h2>

              {!analysisResults?.langchainAnalysis ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-8">
                  <div className="bg-violet-100 rounded-full p-4 mb-4">
                    <Brain className="h-12 w-12 text-violet-600" />
                  </div>
                  <h3 className="text-lg font-medium">
                    {onboardingData
                      ? `No AI Analysis Available for ${onboardingData.firstName}`
                      : "No AI Analysis Available"}
                  </h3>
                  <p className="text-muted-foreground mt-2">
                    {analysisResults?.error
                      ? "AI analysis failed. Please check your OpenAI API configuration and try again."
                      : onboardingData
                        ? `Upload a CSV file and run analysis to see detailed AI reasoning tailored for your ${onboardingData.role} role`
                        : "Upload a file and run analysis to see results"}
                  </p>
                  {isAnalyzing && (
                    <div className="mt-4 flex items-center gap-2 text-violet-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-violet-600"></div>
                      <span className="text-sm">AI analysis in progress...</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Main AI Analysis */}
                  <Card className="bg-white">
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center gap-2">
                        <div className="bg-violet-100 rounded-full p-1.5">
                          <Brain className="h-4 w-4 text-violet-600" />
                        </div>
                        {onboardingData
                          ? `Personalized Data Analysis for ${onboardingData.firstName}`
                          : "Data Analysis Report"}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[400px] w-full">
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              h1: ({ children }) => (
                                <h1 className="text-2xl font-bold text-gray-900 mb-4 border-b pb-2">{children}</h1>
                              ),
                              h2: ({ children }) => (
                                <h2 className="text-xl font-semibold text-gray-800 mb-3 mt-6">{children}</h2>
                              ),
                              h3: ({ children }) => (
                                <h3 className="text-lg font-medium text-gray-700 mb-2 mt-4">{children}</h3>
                              ),
                              h4: ({ children }) => (
                                <h4 className="text-base font-medium text-gray-700 mb-2 mt-3">{children}</h4>
                              ),
                              p: ({ children }) => <p className="text-gray-700 mb-3 leading-relaxed">{children}</p>,
                              ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
                              ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
                              li: ({ children }) => <li className="text-gray-700">{children}</li>,
                              strong: ({ children }) => (
                                <strong className="font-semibold text-gray-900">{children}</strong>
                              ),
                              em: ({ children }) => <em className="italic text-gray-600">{children}</em>,
                              code: ({ children }) => (
                                <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800">
                                  {children}
                                </code>
                              ),
                              pre: ({ children }) => (
                                <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto mb-4 text-sm">
                                  {children}
                                </pre>
                              ),
                              blockquote: ({ children }) => (
                                <blockquote className="border-l-4 border-violet-300 pl-4 italic text-gray-600 mb-4">
                                  {children}
                                </blockquote>
                              ),
                              table: ({ children }) => (
                                <div className="overflow-x-auto mb-4">
                                  <table className="min-w-full border border-gray-200 rounded-lg">{children}</table>
                                </div>
                              ),
                              thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
                              tbody: ({ children }) => <tbody className="divide-y divide-gray-200">{children}</tbody>,
                              tr: ({ children }) => <tr>{children}</tr>,
                              th: ({ children }) => (
                                <th className="px-4 py-2 text-left text-sm font-medium text-gray-900 border-b">
                                  {children}
                                </th>
                              ),
                              td: ({ children }) => (
                                <td className="px-4 py-2 text-sm text-gray-700 border-b">{children}</td>
                              ),
                              hr: () => <hr className="my-6 border-gray-200" />,
                            }}
                          >
                            {getCombinedAnalysisContent()}
                          </ReactMarkdown>
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden">
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4">
                {/* CSV Context Indicator */}
                {analysisResults && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 text-sm text-blue-700">
                      <FileText className="h-4 w-4" />
                      <span className="font-medium">
                        Dataset Loaded: {analysisResults.fileInfo?.filename || "uploaded.csv"}
                      </span>
                      <span className="text-blue-600">
                        ({analysisResults.fileInfo?.rows || 0} rows × {analysisResults.fileInfo?.columns || 0} columns)
                      </span>
                    </div>
                    <p className="text-xs text-blue-600 mt-1">
                      Ask me questions about your data - I have full context of your uploaded CSV file.
                    </p>
                  </div>
                )}

                {allMessages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-8">
                    <div className="bg-primary/10 rounded-full p-4 mb-4">
                      <MessageSquare className="h-12 w-12 text-primary" />
                    </div>
                    <h3 className="text-lg font-medium">
                      {onboardingData ? `Start a Conversation, ${onboardingData.firstName}!` : "Start a Conversation"}
                    </h3>
                    <p className="text-muted-foreground mt-2">
                      {onboardingData
                        ? `Ask questions about your data and get AI-powered insights tailored for your ${onboardingData.role} role`
                        : "Ask questions about your data and get AI-powered insights"}
                    </p>
                    {analysisResults && (
                      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm text-blue-700">
                          💡 Your CSV data is loaded! Ask questions like "What are the main trends?" or
                          {onboardingData?.role === "ceo"
                            ? ' "What are the key business metrics?"'
                            : onboardingData?.role === "analyst"
                              ? ' "Show me statistical correlations"'
                              : onboardingData?.role === "marketing"
                                ? ' "How are our campaigns performing?"'
                                : ' "Show me the key insights"'}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  allMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-xl px-4 py-2 ${
                          message.role === "user" ? "bg-primary text-white" : "bg-secondary/50"
                        }`}
                      >
                        <div className="whitespace-pre-wrap prose prose-sm max-w-none">
                          {message.role === "assistant" ? (
                            <ReactMarkdown
                              components={{
                                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                                li: ({ children }) => <li className="mb-1">{children}</li>,
                                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                                code: ({ children }) => (
                                  <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                                ),
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          ) : (
                            message.content
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-xl px-4 py-2 bg-secondary/50">
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 rounded-full bg-primary animate-pulse"></div>
                        <div className="h-2 w-2 rounded-full bg-primary animate-pulse delay-150"></div>
                        <div className="h-2 w-2 rounded-full bg-primary animate-pulse delay-300"></div>
                        <span className="text-sm text-muted-foreground">AI is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <div className="p-6 flex-shrink-0">
              {/* Header */}
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Hi, what data do you want to work on today?</h2>

              {/* Sleek Input Area */}
              <form onSubmit={handleSubmit} className="relative mb-4">
                <div className="flex items-center bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                  <div className="pl-4 pr-2">
                    <Plus className="h-5 w-5 text-gray-400" />
                  </div>
                  <Input
                    value={input}
                    onChange={handleInputChange}
                    placeholder={
                      analysisResults
                        ? onboardingData
                          ? `Ask a question about your data, ${onboardingData.firstName}...`
                          : "Ask a question about your data..."
                        : "Upload and analyze a CSV file first to start chatting..."
                    }
                    disabled={isChatLoading}
                    className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-gray-700 placeholder:text-gray-400"
                    autoComplete="off"
                  />
                  <Button
                    type="submit"
                    disabled={isChatLoading || !input.trim()}
                    className="m-2 rounded-full bg-primary hover:bg-primary/90 text-white flex-shrink-0 h-10 w-10 p-0"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </form>

              {/* Suggested Questions */}
              <div className="space-y-2">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  <button
                    onClick={() => setInput("What are the key trends in my data?")}
                    className="p-3 text-left text-sm bg-white border border-gray-200 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors"
                  >
                    What are the key trends in my data?
                  </button>
                  <button
                    onClick={() => setInput("Can you identify any outliers or anomalies?")}
                    className="p-3 text-left text-sm bg-white border border-gray-200 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors"
                  >
                    Can you identify any outliers or anomalies?
                  </button>
                  <button
                    onClick={() => setInput("Show me a summary of my dataset")}
                    className="p-3 text-left text-sm bg-white border border-gray-200 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors"
                  >
                    Show me a summary of my dataset
                  </button>
                </div>
              </div>

              {chatError && (
                <div className="mt-3 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                  Chat error: {chatError}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* PDF Export Modal */}
      <PDFExport
        isOpen={showPDFExport}
        onClose={() => setShowPDFExport(false)}
        analysisResults={analysisResults}
        csvFileName={analysisResults?.fileInfo?.filename}
      />
    </>
  )
}
