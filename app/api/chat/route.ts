import { type NextRequest, NextResponse } from "next/server"

// Define Message type locally
interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { messages, csvContext, onboardingData } = body

    // Check if OpenAI API key is available
    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json({ error: "OpenAI API key not configured" }, { status: 500 })
    }

    // Get the last user message
    const lastMessage = messages[messages.length - 1]
    if (!lastMessage || lastMessage.role !== "user") {
      return NextResponse.json({ error: "No user message found" }, { status: 400 })
    }

    // Build context-aware system prompt
    let systemPrompt = "You are a helpful data analyst assistant. "

    // Add CSV context if available
    if (csvContext) {
      systemPrompt += `You have access to a CSV dataset with the following information:
- Filename: ${csvContext.filename}
- Size: ${csvContext.rows} rows × ${csvContext.columns} columns
- Data Quality: ${csvContext.quality}% completeness
- Column Headers: ${csvContext.headers.join(", ")}
- Summary: ${csvContext.summary}

Key Insights:
${csvContext.insights
  .slice(0, 5)
  .map((insight: string) => `• ${insight}`)
  .join("\n")}

Use this context to provide specific, data-driven answers about the user's dataset.`
    }

    // Add personalization if onboarding data is available
    if (onboardingData) {
      const roleContext =
        {
          ceo: "executive-level strategic insights and business KPIs",
          product: "product management insights and user behavior analysis",
          analyst: "detailed statistical analysis and data patterns",
          marketing: "marketing performance and customer acquisition insights",
          operations: "operational efficiency and process optimization",
          other: "comprehensive business insights",
        }[onboardingData.role] || "business insights"

      systemPrompt += `

PERSONALIZATION CONTEXT:
- User: ${onboardingData.firstName} (${onboardingData.role})
- Focus: ${roleContext}
- Goals: ${onboardingData.goals.length > 0 ? onboardingData.goals.join(", ") : "General analysis"}
- Data Types of Interest: ${onboardingData.dataTypes.length > 0 ? onboardingData.dataTypes.join(", ") : "All types"}

Tailor your responses specifically for ${onboardingData.firstName}'s ${onboardingData.role} role and stated goals.`
    }

    // Prepare messages for OpenAI
    const openaiMessages = [
      {
        role: "system",
        content: systemPrompt,
      },
      ...messages.slice(-5).map((msg: Message) => ({
        role: msg.role,
        content: msg.content,
      })),
    ]

    // Call OpenAI API directly
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o",
        messages: openaiMessages,
        max_tokens: 1000,
        temperature: 0.7,
        stream: false,
      }),
    })

    if (!response.ok) {
      const errorData = await response.text()
      console.error("OpenAI API error:", response.status, errorData)
      return NextResponse.json({ error: `OpenAI API error: ${response.status}` }, { status: response.status })
    }

    const data = await response.json()
    const assistantMessage = data.choices?.[0]?.message?.content

    if (!assistantMessage) {
      return NextResponse.json({ error: "No response from OpenAI" }, { status: 500 })
    }

    return NextResponse.json({
      content: assistantMessage,
      success: true,
    })
  } catch (error) {
    console.error("Chat API error:", error)
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
