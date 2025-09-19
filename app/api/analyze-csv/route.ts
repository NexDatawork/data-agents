import { type NextRequest, NextResponse } from "next/server"
import { analyzeCsvWithLangChain } from "@/lib/langchain-service"
import type { OnboardingData } from "@/components/onboarding-modal"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const {
      csvData,
      headers,
      question,
      industry = "",
      topic = "",
      requirement = "",
      customRequirement = "",
      filename = "uploaded.csv",
      onboardingData,
    } = body

    // Validate required fields
    if (!csvData || !headers || !Array.isArray(csvData) || !Array.isArray(headers)) {
      return NextResponse.json(
        {
          success: false,
          error: "Invalid CSV data format. Please ensure csvData and headers are arrays.",
        },
        { status: 400 },
      )
    }

    if (csvData.length === 0 || headers.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Empty CSV data. Please upload a file with data.",
        },
        { status: 400 },
      )
    }

    console.log("🚀 Starting CSV analysis:", {
      filename,
      rows: csvData.length,
      columns: headers.length,
      industry,
      topic,
      hasOnboarding: !!onboardingData,
      hasCustomRequirement: !!customRequirement,
    })

    // Call the LangChain analysis service
    const result = await analyzeCsvWithLangChain(
      csvData,
      headers,
      question,
      industry,
      topic,
      requirement,
      customRequirement,
      filename,
      onboardingData as OnboardingData | null,
    )

    if (!result.success) {
      console.error("❌ Analysis failed:", result.error)
      return NextResponse.json(
        {
          success: false,
          error: result.error || "Analysis failed",
        },
        { status: 500 },
      )
    }

    console.log("✅ Analysis completed successfully")

    return NextResponse.json({
      success: true,
      analysis: result.analysis,
      reasoning: result.reasoning,
      error: result.error || null,
    })
  } catch (error) {
    console.error("❌ CSV Analysis API error:", error)

    return NextResponse.json(
      {
        success: false,
        error: "Internal server error during analysis",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
