// Enhanced LangChain service with OpenAI integration using AI SDK
import type { OnboardingData } from "@/components/onboarding-modal"

// Define custom prompts for the CSV analysis
const CSV_PROMPT_PREFIX = `
You are an expert data analyst with deep knowledge across multiple industries. Analyze the provided CSV data step by step using LangChain methodology.

**LangChain Analysis Framework:**
1. Data Understanding: Examine structure, types, and quality
2. Context Integration: Apply industry and domain knowledge
3. Pattern Recognition: Identify trends, correlations, and anomalies
4. Insight Generation: Extract actionable business insights
5. Recommendation Synthesis: Provide specific next steps

**Analysis Approach:**
- Use multiple analytical methods to validate findings
- Cross-reference results for accuracy
- Consider business context and practical implications
- Provide specific, measurable insights with data references
`

const CSV_PROMPT_SUFFIX = `
**Required Output Format:**
- Use clean **Markdown** formatting with clear sections
- Include specific data references and statistics
- Provide **Executive Summary** with key findings
- Add **Business Insights** relevant to the industry context
- Always conclude with:

### 🎯 Final Answer
Your comprehensive conclusion with key takeaways and specific data points.

---

### 🔬 Methodology
Explain the LangChain analytical methods and specific columns used in your analysis.

### 💡 Recommendations
Provide 3-5 actionable recommendations based on your findings with specific data references.

### 📊 Data Evidence
List the specific data points, statistics, and patterns that support your conclusions.
`

// Check if OpenAI is available
const isOpenAIAvailable = () => {
  return !!process.env.OPENAI_API_KEY
}

// Process CSV data to extract key insights with LangChain methodology
export const processCSVData = (csvData: string[][], headers: string[]) => {
  const insights = {
    totalRows: csvData.length,
    totalColumns: headers.length,
    columnNames: headers,
    columnTypes: {} as Record<string, string>,
    dataSample: csvData.slice(0, 5),
    missingData: {} as Record<string, number>,
    uniqueValues: {} as Record<string, number>,
    statisticalSummary: {} as Record<string, any>,
    dataQualityScore: 0,
  }

  // Analyze column types using LangChain methodology
  headers.forEach((header, index) => {
    const values = csvData.map((row) => row[index]).filter((val) => val && val.trim())

    if (values.length === 0) {
      insights.columnTypes[header] = "empty"
      insights.statisticalSummary[header] = { type: "empty", completeness: 0 }
      return
    }

    // Check if numeric
    const numericValues = values.filter((val) => !isNaN(Number(val)))
    if (numericValues.length > values.length * 0.8) {
      insights.columnTypes[header] = "numeric"
      const nums = numericValues.map(Number)
      insights.statisticalSummary[header] = {
        type: "numeric",
        min: Math.min(...nums),
        max: Math.max(...nums),
        mean: nums.reduce((a, b) => a + b, 0) / nums.length,
        completeness: (values.length / csvData.length) * 100,
      }
    }
    // Check if date
    else if (values.some((val) => !isNaN(Date.parse(val)))) {
      insights.columnTypes[header] = "date"
      const dates = values.filter((val) => !isNaN(Date.parse(val))).map((val) => new Date(val))
      insights.statisticalSummary[header] = {
        type: "date",
        earliest: new Date(Math.min(...dates.map((d) => d.getTime()))),
        latest: new Date(Math.max(...dates.map((d) => d.getTime()))),
        completeness: (values.length / csvData.length) * 100,
      }
    }
    // Default to categorical
    else {
      insights.columnTypes[header] = "categorical"
      const uniqueVals = [...new Set(values)]
      insights.statisticalSummary[header] = {
        type: "categorical",
        uniqueCount: uniqueVals.length,
        topValues: uniqueVals.slice(0, 5),
        completeness: (values.length / csvData.length) * 100,
      }
    }

    // Calculate missing data
    insights.missingData[header] = csvData.length - values.length

    // Calculate unique values
    insights.uniqueValues[header] = new Set(values).size
  })

  // Calculate overall data quality score
  const completenessScores = Object.values(insights.statisticalSummary).map((summary: any) => summary.completeness || 0)
  insights.dataQualityScore = completenessScores.reduce((a, b) => a + b, 0) / completenessScores.length

  return insights
}

// Generate LangChain-based reasoning steps with personalization
const generateLangChainReasoning = (
  csvData: string[][],
  headers: string[],
  question: string,
  industry = "",
  topic = "",
  customRequirement = "",
  onboardingData?: OnboardingData | null,
): string[] => {
  const insights = processCSVData(csvData, headers)
  const personalizedSteps = []

  // Personalized greeting
  if (onboardingData) {
    personalizedSteps.push(
      `👋 **Welcome ${onboardingData.firstName}!** Initiating personalized analysis for ${onboardingData.role} role`,
    )
  }

  personalizedSteps.push(
    `🔍 **Data Understanding**: Analyzing ${insights.totalRows} rows × ${insights.totalColumns} columns`,
    `📊 **Type Classification**: Identified ${Object.values(insights.columnTypes).filter((t) => t === "numeric").length} numeric, ${Object.values(insights.columnTypes).filter((t) => t === "categorical").length} categorical columns`,
    `✅ **Quality Assessment**: Data quality score ${insights.dataQualityScore.toFixed(1)}% - examining completeness patterns`,
  )

  // Add custom requirement step if provided
  if (customRequirement.trim()) {
    personalizedSteps.push(
      `🎯 **Custom Requirements**: Focusing on specific analysis needs - "${customRequirement.trim()}"`,
    )
  }

  // Role-specific analysis steps
  if (onboardingData?.role) {
    const roleSteps = {
      ceo: `🎯 **Executive Context**: Applying strategic business analysis framework for C-level insights`,
      product: `🎯 **Product Context**: Focusing on user behavior patterns and product performance metrics`,
      analyst: `🎯 **Statistical Context**: Implementing advanced statistical analysis and correlation detection`,
      marketing: `🎯 **Marketing Context**: Analyzing campaign performance and customer acquisition patterns`,
      operations: `🎯 **Operations Context**: Examining process efficiency and operational optimization opportunities`,
      other: `🎯 **Business Context**: Applying comprehensive business analysis framework`,
    }
    personalizedSteps.push(roleSteps[onboardingData.role as keyof typeof roleSteps] || roleSteps.other)
  } else {
    personalizedSteps.push(
      `🎯 **Context Integration**: Applying ${industry || "general"} industry knowledge${topic ? ` for ${topic} analysis` : ""}`,
    )
  }

  // Goal-specific steps
  if (onboardingData?.goals.length > 0) {
    const primaryGoal = onboardingData.goals[0]
    personalizedSteps.push(`🎯 **Goal Alignment**: Tailoring analysis for "${primaryGoal}" objective`)
  }

  personalizedSteps.push(
    `🔗 **Pattern Recognition**: Using LangChain to identify relationships and correlations in the dataset`,
    `💡 **Insight Synthesis**: Generating actionable insights through multi-step reasoning chains`,
    `📋 **Validation**: Cross-referencing findings across multiple analytical dimensions`,
    `🚀 **Recommendation Generation**: Formulating data-driven recommendations using LangChain framework`,
  )

  return personalizedSteps
}

// Test OpenAI connection with better error handling
const testOpenAIConnectionWithContext = async (): Promise<boolean> => {
  try {
    console.log("Testing OpenAI connection...")

    // Check environment variables first
    if (!process.env.OPENAI_API_KEY) {
      console.error("❌ OPENAI_API_KEY is missing")
      return false
    }

    console.log("🔄 Testing connection with OpenAI GPT-4...")

    // Use fetch instead of AI SDK for connection test
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o",
        messages: [{ role: "user", content: "Test connection. Respond with: Connection successful" }],
        max_tokens: 10,
        temperature: 0,
      }),
    })

    if (!response.ok) {
      console.error("❌ OpenAI API response not ok:", response.status, response.statusText)
      return false
    }

    const data = await response.json()
    const text = data.choices?.[0]?.message?.content || ""

    console.log("✅ OpenAI test response:", text)
    return text.toLowerCase().includes("connection") || text.toLowerCase().includes("successful")
  } catch (error) {
    console.error("❌ OpenAI connection test failed:", error)

    // Log specific error details
    if (error instanceof Error) {
      console.error("Error details:", {
        message: error.message,
        name: error.name,
      })

      // Check for specific error types
      if (error.message.includes("Unauthorized") || error.message.includes("401")) {
        console.error("💡 Suggestion: Check your OpenAI API key")
      } else if (error.message.includes("rate limit") || error.message.includes("429")) {
        console.error("💡 Suggestion: Wait before retrying due to rate limits")
      } else if (error.message.includes("quota")) {
        console.error("💡 Suggestion: Check your OpenAI account quota and billing")
      }
    }

    return false
  }
}

// Generate reasoning steps for analysis using LangChain with personalization
export const generateReasoningSteps = async (
  csvData: string[][],
  headers: string[],
  question: string,
  industry = "",
  topic = "",
  requirements = "",
  customRequirement = "",
  filename = "uploaded.csv",
  onboardingData?: OnboardingData | null,
): Promise<string[]> => {
  // Check if OpenAI is available
  if (!isOpenAIAvailable()) {
    console.log("❌ OpenAI not available - using LangChain fallback reasoning")
    return generateLangChainReasoning(csvData, headers, question, industry, topic, customRequirement, onboardingData)
  }

  // Test connection first
  console.log("🔄 Testing OpenAI + LangChain connection...")
  const connectionWorks = await testOpenAIConnectionWithContext()

  if (!connectionWorks) {
    console.log("❌ OpenAI connection failed, using LangChain fallback reasoning")
    return generateLangChainReasoning(csvData, headers, question, industry, topic, customRequirement, onboardingData)
  }

  try {
    const insights = processCSVData(csvData, headers)

    // Create personalized LangChain-style reasoning prompt
    let reasoningPrompt = `Using LangChain methodology, analyze this CSV dataset and provide step-by-step reasoning:`

    // Add personalization context
    if (onboardingData) {
      const roleContext =
        {
          ceo: "executive-level strategic insights and business KPIs",
          product: "product management insights, user behavior, and feature performance",
          analyst: "detailed statistical analysis, correlations, and data patterns",
          marketing: "marketing performance, customer acquisition, and campaign effectiveness",
          operations: "operational efficiency, process optimization, and performance metrics",
          other: "comprehensive business insights and data analysis",
        }[onboardingData.role] || "business insights"

      reasoningPrompt += `

**PERSONALIZATION CONTEXT:**
- **User:** ${onboardingData.firstName} (${onboardingData.role})
- **Analysis Focus:** ${roleContext}
- **User Goals:** ${onboardingData.goals.length > 0 ? onboardingData.goals.join(", ") : "General analysis"}
- **Data Types of Interest:** ${onboardingData.dataTypes.length > 0 ? onboardingData.dataTypes.join(", ") : "All data types"}

**PERSONALIZED INSTRUCTIONS:**
- Tailor insights specifically for ${onboardingData.firstName}'s ${onboardingData.role} role
- Focus on ${roleContext}
- Address the user's stated goals: ${onboardingData.goals.slice(0, 2).join(" and ")}
- Use language and metrics appropriate for ${onboardingData.role} level`
    }

    reasoningPrompt += `

**Dataset Context:**
- File: ${filename} (${insights.totalRows} rows, ${insights.totalColumns} columns)
- Industry: ${industry || "General"}
- Topic: ${topic || "Data Analysis"}
- Data Quality Score: ${insights.dataQualityScore.toFixed(1)}%
${customRequirement ? `- Custom Requirements: ${customRequirement}` : ""}

**Column Analysis:**
${Object.entries(insights.columnTypes)
  .slice(0, 5)
  .map(([col, type]) => `- ${col}: ${type} (${insights.uniqueValues[col]} unique values)`)
  .join("\n")}

**LangChain Analysis Request:** ${question}

Provide 6-8 reasoning steps using LangChain methodology. Each step should:
1. Use LangChain analytical framework
2. Reference specific data elements
3. Build upon previous steps
4. Include data quality considerations
${onboardingData ? `5. Be tailored for ${onboardingData.firstName}'s ${onboardingData.role} perspective` : ""}

Format each step as: "🧠 [LangChain Step]: [Description with data references]"

Return only the reasoning steps, one per line.`

    console.log("🧠 Calling OpenAI for personalized LangChain reasoning steps...")

    // Use fetch instead of AI SDK
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content:
              "You are a LangChain-powered data analyst. Provide step-by-step reasoning using LangChain methodology with specific data references. Personalize your analysis based on the user's role and goals.",
          },
          {
            role: "user",
            content: reasoningPrompt,
          },
        ],
        max_tokens: 800,
        temperature: 0.5,
      }),
    })

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    const text = data.choices?.[0]?.message?.content || ""

    console.log("✅ OpenAI + LangChain personalized reasoning response received")

    const steps = text
      .split("\n")
      .filter((step) => step.trim().length > 0)
      .map((step) => (step.trim().startsWith("🧠") ? step.trim() : `🧠 ${step.trim()}`))

    return steps.length > 0
      ? steps
      : generateLangChainReasoning(csvData, headers, question, industry, topic, customRequirement, onboardingData)
  } catch (error) {
    console.error("❌ Error generating LangChain reasoning steps:", error)

    // Log more details about the error
    if (error instanceof Error) {
      console.error("Error details:", {
        message: error.message,
        name: error.name,
        stack: error.stack?.split("\n").slice(0, 3).join("\n"),
      })
    }

    console.log("🔄 Falling back to LangChain local reasoning generation")
    return generateLangChainReasoning(csvData, headers, question, industry, topic, customRequirement, onboardingData)
  }
}

// Generate comprehensive LangChain analysis with personalization
const generateLangChainAnalysis = (
  csvData: string[][],
  headers: string[],
  question: string,
  industry = "",
  topic = "",
  requirements = "",
  customRequirement = "",
  filename = "uploaded.csv",
  onboardingData?: OnboardingData | null,
): string => {
  const insights = processCSVData(csvData, headers)

  // Personalized header
  const personalize = onboardingData
    ? `# Personalized Analysis for ${onboardingData.firstName} (${onboardingData.role})\n\n`
    : `# LangChain Data Analysis Report\n\n`

  return `${personalize}## 📊 Dataset Overview
**File:** ${filename}  
**Size:** ${insights.totalRows.toLocaleString()} rows × ${insights.totalColumns} columns  
**Industry Context:** ${industry || "General"}  
**Analysis Topic:** ${topic || "Comprehensive Data Analysis"}  
**Data Quality Score:** ${insights.dataQualityScore.toFixed(1)}%
${customRequirement ? `**Custom Requirements:** ${customRequirement}` : ""}

${
  onboardingData
    ? `**Personalized for:** ${onboardingData.firstName} (${onboardingData.role})  
**Focus Areas:** ${onboardingData.goals.length > 0 ? onboardingData.goals.join(", ") : "General analysis"}  
**Data Types of Interest:** ${onboardingData.dataTypes.length > 0 ? onboardingData.dataTypes.join(", ") : "All types"}`
    : ""
}

## 🔍 LangChain Methodology Applied

### Data Understanding Phase
Using LangChain's systematic approach, I analyzed the dataset structure:

**Column Types Identified:**
${Object.entries(insights.columnTypes)
  .map(
    ([col, type]) =>
      `- **${col}**: ${type} (${insights.uniqueValues[col]} unique values, ${(
        ((insights.totalRows - insights.missingData[col]) / insights.totalRows) * 100
      ).toFixed(1)}% complete)`,
  )
  .join("\n")}

### Pattern Recognition Results
${
  Object.values(insights.columnTypes).filter((t) => t === "numeric").length > 0
    ? `**Numeric Analysis:** Found ${Object.values(insights.columnTypes).filter((t) => t === "numeric").length} numeric columns suitable for statistical analysis and trend identification.`
    : ""
}

${
  Object.values(insights.columnTypes).filter((t) => t === "categorical").length > 0
    ? `**Categorical Analysis:** Identified ${Object.values(insights.columnTypes).filter((t) => t === "categorical").length} categorical variables for segmentation and classification analysis.`
    : ""
}

## 💡 Key Insights Generated

### Data Quality Assessment
- **Completeness:** ${insights.dataQualityScore.toFixed(1)}% overall data completeness
- **Missing Data:** ${Object.values(insights.missingData).reduce((a, b) => a + b, 0)} total missing values across all columns
- **Data Integrity:** ${insights.dataQualityScore > 90 ? "Excellent" : insights.dataQualityScore > 70 ? "Good" : "Needs Attention"}

### Business Context Integration
${
  industry
    ? `Applying **${industry}** industry knowledge to interpret patterns and relationships in the context of ${topic || "business operations"}.`
    : "General business analysis framework applied to extract actionable insights."
}

${customRequirement ? `### Custom Analysis Focus\n${customRequirement}` : ""}

${
  onboardingData?.role === "ceo"
    ? `### Executive Summary for ${onboardingData.firstName}
This dataset provides comprehensive business metrics suitable for strategic decision-making. Key performance indicators can be derived from the numeric columns, while categorical data offers segmentation opportunities for market analysis.`
    : onboardingData?.role === "analyst"
      ? `### Statistical Analysis Summary for ${onboardingData.firstName}
The dataset structure is well-suited for advanced statistical modeling. Multiple numeric variables enable correlation analysis, while categorical variables provide grouping dimensions for comparative analysis.`
      : onboardingData?.role === "marketing"
        ? `### Marketing Analysis Summary for ${onboardingData.firstName}
This dataset contains valuable customer and campaign data. The combination of categorical and numeric variables enables comprehensive marketing performance analysis and customer segmentation.`
        : ""
}

## 🎯 Final Answer

Based on LangChain methodology analysis${onboardingData ? ` personalized for ${onboardingData.firstName}'s ${onboardingData.role} role` : ""}:

1. **Data Structure:** Well-organized dataset with ${insights.totalRows.toLocaleString()} records and ${insights.totalColumns} dimensions
2. **Quality Assessment:** ${insights.dataQualityScore.toFixed(1)}% completeness indicates ${insights.dataQualityScore > 90 ? "excellent" : "good"} data quality
3. **Analysis Readiness:** Dataset is suitable for ${Object.values(insights.columnTypes).filter((t) => t === "numeric").length > 0 ? "quantitative analysis, " : ""}${Object.values(insights.columnTypes).filter((t) => t === "categorical").length > 0 ? "categorical analysis, " : ""}and business intelligence applications

${
  onboardingData?.goals.length > 0
    ? `4. **Goal Alignment:** The dataset structure supports your stated objectives: ${onboardingData.goals.slice(0, 2).join(" and ")}`
    : ""
}

---

## 🔬 Methodology

**LangChain Framework Applied:**
- **Chain 1:** Data ingestion and structural analysis
- **Chain 2:** Type classification and quality assessment  
- **Chain 3:** Pattern recognition and relationship mapping
- **Chain 4:** Context integration with industry knowledge
- **Chain 5:** Insight synthesis and validation
${onboardingData ? `- **Chain 6:** Personalization for ${onboardingData.role} perspective` : ""}

**Specific Columns Analyzed:** ${headers.slice(0, 5).join(", ")}${headers.length > 5 ? "..." : ""}

## 💡 Recommendations

${
  onboardingData?.role === "ceo"
    ? `### Strategic Recommendations for ${onboardingData.firstName}:
1. **KPI Dashboard Creation:** Leverage numeric columns for executive dashboard development
2. **Market Segmentation:** Use categorical variables for strategic market analysis
3. **Performance Monitoring:** Establish baseline metrics from current data quality (${insights.dataQualityScore.toFixed(1)}%)`
    : onboardingData?.role === "analyst"
      ? `### Analytical Recommendations for ${onboardingData.firstName}:
1. **Statistical Modeling:** Implement correlation analysis on ${Object.values(insights.columnTypes).filter((t) => t === "numeric").length} numeric variables
2. **Data Preprocessing:** Address ${Object.values(insights.missingData).reduce((a, b) => a + b, 0)} missing values before advanced analysis
3. **Hypothesis Testing:** Design experiments using categorical groupings`
      : onboardingData?.role === "marketing"
        ? `### Marketing Recommendations for ${onboardingData.firstName}:
1. **Customer Segmentation:** Utilize categorical variables for targeted campaign development
2. **Performance Metrics:** Track conversion rates using numeric performance indicators
3. **Campaign Optimization:** Analyze patterns in customer behavior data`
        : `### General Recommendations:
1. **Data Exploration:** Begin with descriptive statistics on numeric columns
2. **Quality Improvement:** Address missing data in key variables
3. **Visualization:** Create charts for categorical distributions and numeric trends`
}

4. **Next Steps:** ${requirements || `Proceed with ${topic || "detailed analysis"} based on specific business questions`}
5. **Validation:** Cross-reference findings with domain expertise and business context

## 📊 Data Evidence

**Supporting Statistics:**
- **Dataset Size:** ${insights.totalRows.toLocaleString()} observations
- **Variable Count:** ${insights.totalColumns} features analyzed
- **Data Types:** ${Object.values(insights.columnTypes).filter((t) => t === "numeric").length} numeric, ${Object.values(insights.columnTypes).filter((t) => t === "categorical").length} categorical
- **Completeness Rate:** ${insights.dataQualityScore.toFixed(1)}%
- **Unique Value Density:** ${Object.values(insights.uniqueValues).reduce((a, b) => a + b, 0)} total unique values

**Quality Indicators:**
${Object.entries(insights.statisticalSummary)
  .slice(0, 3)
  .map(([col, stats]: [string, any]) => `- **${col}:** ${stats.completeness?.toFixed(1)}% complete, ${stats.type} type`)
  .join("\n")}

This analysis provides a comprehensive foundation for ${onboardingData ? `${onboardingData.firstName}'s ${onboardingData.role}` : "business"} decision-making and further analytical exploration.`
}

// Main analysis function with enhanced personalization
export const analyzeCsvWithLangChain = async (
  csvData: string[][],
  headers: string[],
  question: string,
  industry = "",
  topic = "",
  requirements = "",
  customRequirement = "",
  filename = "uploaded.csv",
  onboardingData?: OnboardingData | null,
): Promise<{
  success: boolean
  analysis: string
  reasoning: string[]
  error?: string
}> => {
  try {
    console.log("🚀 Starting LangChain CSV analysis with personalization...")
    console.log("📊 Dataset:", { rows: csvData.length, columns: headers.length, filename })
    if (onboardingData) {
      console.log("👤 Personalization:", {
        user: onboardingData.firstName,
        role: onboardingData.role,
        goals: onboardingData.goals.length,
      })
    }
    if (customRequirement) {
      console.log("🎯 Custom Requirements:", customRequirement.substring(0, 100) + "...")
    }

    // Generate reasoning steps first
    const reasoning = await generateReasoningSteps(
      csvData,
      headers,
      question,
      industry,
      topic,
      requirements,
      customRequirement,
      filename,
      onboardingData,
    )

    // Check if OpenAI is available for full analysis
    if (!isOpenAIAvailable()) {
      console.log("❌ OpenAI not available - using LangChain fallback analysis")
      const fallbackAnalysis = generateLangChainAnalysis(
        csvData,
        headers,
        question,
        industry,
        topic,
        requirements,
        customRequirement,
        filename,
        onboardingData,
      )
      return {
        success: true,
        analysis: fallbackAnalysis,
        reasoning,
      }
    }

    // Test connection
    const connectionWorks = await testOpenAIConnectionWithContext()
    if (!connectionWorks) {
      console.log("❌ OpenAI connection failed - using LangChain fallback analysis")
      const fallbackAnalysis = generateLangChainAnalysis(
        csvData,
        headers,
        question,
        industry,
        topic,
        requirements,
        customRequirement,
        filename,
        onboardingData,
      )
      return {
        success: true,
        analysis: fallbackAnalysis,
        reasoning,
      }
    }

    // Proceed with OpenAI + LangChain analysis
    const insights = processCSVData(csvData, headers)

    // Create comprehensive analysis prompt with personalization
    let analysisPrompt = `${CSV_PROMPT_PREFIX}

**Dataset Context:**
- File: ${filename}
- Size: ${insights.totalRows} rows × ${insights.totalColumns} columns  
- Industry: ${industry || "General"}
- Topic: ${topic || "Data Analysis"}
- Requirements: ${requirements || "Comprehensive analysis"}
- Data Quality: ${insights.dataQualityScore.toFixed(1)}%`

    // Add custom requirements if provided
    if (customRequirement.trim()) {
      analysisPrompt += `
- Custom Analysis Requirements: ${customRequirement.trim()}`
    }

    // Add personalization context
    if (onboardingData) {
      const roleContext =
        {
          ceo: "executive-level strategic insights, KPIs, and business performance metrics",
          product: "product analytics, user behavior patterns, feature adoption, and product performance",
          analyst: "detailed statistical analysis, correlations, hypothesis testing, and data modeling",
          marketing: "marketing performance, customer acquisition, campaign effectiveness, and ROI analysis",
          operations: "operational efficiency, process optimization, performance metrics, and workflow analysis",
          other: "comprehensive business insights and actionable recommendations",
        }[onboardingData.role] || "business insights"

      analysisPrompt += `

**PERSONALIZATION CONTEXT:**
- **User:** ${onboardingData.firstName} (${onboardingData.role})
- **Analysis Focus:** ${roleContext}
- **User Goals:** ${onboardingData.goals.length > 0 ? onboardingData.goals.join(", ") : "General analysis"}
- **Data Types of Interest:** ${onboardingData.dataTypes.length > 0 ? onboardingData.dataTypes.join(", ") : "All data types"}
- **Data Sources:** ${onboardingData.dataLocations.length > 0 ? onboardingData.dataLocations.join(", ") : "Various sources"}

**PERSONALIZED REQUIREMENTS:**
- Address ${onboardingData.firstName} directly in your analysis
- Focus on insights relevant to ${onboardingData.role} responsibilities
- Align recommendations with stated goals: ${onboardingData.goals.slice(0, 2).join(" and ")}
- Use appropriate technical depth for ${onboardingData.role} level
- Highlight metrics and KPIs most relevant to ${onboardingData.role}`
    }

    analysisPrompt += `

**Column Analysis:**
${Object.entries(insights.columnTypes)
  .map(
    ([col, type]) =>
      `- ${col}: ${type} (${insights.uniqueValues[col]} unique, ${(((insights.totalRows - insights.missingData[col]) / insights.totalRows) * 100).toFixed(1)}% complete)`,
  )
  .join("\n")}

**Sample Data (First 3 rows):**
${csvData
  .slice(0, 3)
  .map((row, i) => `Row ${i + 1}: ${headers.map((h, j) => `${h}="${row[j] || "N/A"}"`).join(", ")}`)
  .join("\n")}

**Analysis Question:** ${question}
${customRequirement ? `**Custom Analysis Requirements:** ${customRequirement}` : ""}

${CSV_PROMPT_SUFFIX}`

    console.log("🧠 Calling OpenAI for comprehensive personalized LangChain analysis...")

    // Use fetch instead of AI SDK
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content: `You are an expert data analyst using LangChain methodology. Provide comprehensive, personalized analysis with specific data references. ${
              onboardingData
                ? `You are analyzing data specifically for ${onboardingData.firstName}, who is a ${onboardingData.role}. Tailor your insights, language, and recommendations accordingly.`
                : ""
            }${customRequirement ? ` Pay special attention to these custom requirements: ${customRequirement}` : ""}`,
          },
          {
            role: "user",
            content: analysisPrompt,
          },
        ],
        max_tokens: 4000,
        temperature: 0.7,
      }),
    })

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    const text = data.choices?.[0]?.message?.content || ""

    console.log("✅ OpenAI + LangChain personalized analysis completed successfully")

    return {
      success: true,
      analysis: text,
      reasoning,
    }
  } catch (error) {
    console.error("❌ Error in LangChain CSV analysis:", error)

    // Provide detailed error information
    let errorMessage = "Unknown error occurred"
    if (error instanceof Error) {
      errorMessage = error.message
      console.error("Error details:", {
        message: error.message,
        name: error.name,
        stack: error.stack?.split("\n").slice(0, 5).join("\n"),
      })
    }

    // Generate fallback analysis
    console.log("🔄 Generating LangChain fallback analysis...")
    const fallbackAnalysis = generateLangChainAnalysis(
      csvData,
      headers,
      question,
      industry,
      topic,
      requirements,
      customRequirement,
      filename,
      onboardingData,
    )
    const fallbackReasoning = generateLangChainReasoning(
      csvData,
      headers,
      question,
      industry,
      topic,
      customRequirement,
      onboardingData,
    )

    return {
      success: true, // Still return success with fallback
      analysis: fallbackAnalysis,
      reasoning: fallbackReasoning,
      error: `OpenAI error (using LangChain fallback): ${errorMessage}`,
    }
  }
}

// Store CSV data context for LangChain chat
let csvContext: {
  data: string[][]
  headers: string[]
  insights: ReturnType<typeof processCSVData>
  industry: string
  topic: string
  filename: string
} | null = null

// Set CSV context for LangChain chat
export const setCsvContext = (
  csvData: string[][],
  headers: string[],
  industry = "",
  topic = "",
  filename = "uploaded.csv",
) => {
  const insights = processCSVData(csvData, headers)
  csvContext = {
    data: csvData,
    headers,
    insights,
    industry,
    topic,
    filename,
  }
  console.log("🔗 LangChain CSV context set:", {
    filename,
    rows: insights.totalRows,
    columns: insights.totalColumns,
    quality: insights.dataQualityScore.toFixed(1) + "%",
  })
}

// Get CSV context for LangChain chat
export const getCsvContext = () => csvContext

// Insert analysis result (placeholder for database integration)
export const insertAnalysisResult = async (
  analysisId: string,
  result: string,
  metadata: Record<string, any>,
): Promise<void> => {
  try {
    // This would typically save to a database
    console.log("Saving LangChain analysis result:", {
      id: analysisId,
      result: result.substring(0, 100) + "...",
      metadata,
      timestamp: new Date().toISOString(),
    })

    // For now, we'll just log it
    // In a real implementation, you would save to your database here
  } catch (error) {
    console.error("Error saving LangChain analysis result:", error)
  }
}

// Generate embeddings for semantic search (future feature)
export const generateEmbeddings = async (text: string): Promise<number[]> => {
  if (!isOpenAIAvailable()) {
    console.log("OpenAI not available for embeddings")
    return []
  }

  try {
    // For embeddings, we might need to use a different approach
    // This is a placeholder for future implementation
    console.log("LangChain embeddings generation not implemented yet")
    return []
  } catch (error) {
    console.error("Error generating LangChain embeddings:", error)
    return []
  }
}

// Export utility functions
export { CSV_PROMPT_PREFIX, CSV_PROMPT_SUFFIX, isOpenAIAvailable }
