"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, Download, Settings, Database, Loader2, CheckCircle, X, Eye, Edit3, ArrowLeft } from "lucide-react"
import jsPDF from "jspdf"

interface PDFExportProps {
  isOpen: boolean
  onClose: () => void
  analysisResults: any
  csvFileName?: string
}

interface ExportOptions {
  title: string
  includeExecutiveSummary: boolean
  includeInsights: boolean
  includeVisualizations: boolean
  includeLangchainAnalysis: boolean
  includeDataOverview: boolean
  includeMethodology: boolean
  customNotes: string
  authorName: string
  companyName: string
}

interface EditableContent {
  title: string
  executiveSummary: string
  dataOverview: string
  insights: string[]
  langchainAnalysis: string
  methodology: string
  customNotes: string
  authorName: string
  companyName: string
}

type ViewMode = "setup" | "preview" | "complete"

export function PDFExport({ isOpen, onClose, analysisResults, csvFileName }: PDFExportProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("setup")
  const [isExporting, setIsExporting] = useState(false)
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)

  const [options, setOptions] = useState<ExportOptions>({
    title: `Data Analysis Report - ${csvFileName || "Dataset"}`,
    includeExecutiveSummary: true,
    includeInsights: true,
    includeVisualizations: true,
    includeLangchainAnalysis: true,
    includeDataOverview: true,
    includeMethodology: false,
    customNotes: "",
    authorName: "",
    companyName: "",
  })

  const [editableContent, setEditableContent] = useState<EditableContent>({
    title: `Data Analysis Report - ${csvFileName || "Dataset"}`,
    executiveSummary: "Click 'Generate Preview' to extract content from dashboard analysis.",
    dataOverview: "Click 'Generate Preview' to extract dataset overview.",
    insights: ["Click 'Generate Preview' to extract insights from dashboard analysis."],
    langchainAnalysis: "Click 'Generate Preview' to extract AI analysis from dashboard.",
    methodology: generateMethodologyContent(),
    customNotes: "",
    authorName: "",
    companyName: "",
  })

  function generateDataOverview(): string {
    if (!analysisResults?.fileInfo) return "Dataset overview will be generated based on your uploaded file."

    const { fileInfo } = analysisResults
    let overview = `Dataset Overview:\n`
    overview += `• Filename: ${fileInfo.filename || "Unknown"}\n`
    overview += `• Total Records: ${fileInfo.rows?.toLocaleString() || "N/A"}\n`
    overview += `• Total Columns: ${fileInfo.columns || "N/A"}\n`
    overview += `• Data Quality Score: ${fileInfo.dataQualityScore?.toFixed(1) || "Unknown"}%\n\n`

    // Add column type breakdown
    if (fileInfo.columnTypes) {
      const numericCols = Object.values(fileInfo.columnTypes).filter((type) => type === "number").length
      const categoricalCols = Object.values(fileInfo.columnTypes).filter((type) => type === "string").length
      const dateCols = Object.values(fileInfo.columnTypes).filter((type) => type === "date").length

      overview += `Column Type Distribution:\n`
      overview += `• Numeric Columns: ${numericCols}\n`
      overview += `• Categorical Columns: ${categoricalCols}\n`
      overview += `• Date Columns: ${dateCols}\n\n`
    }

    // Add statistical summary
    if (fileInfo.rows && fileInfo.columns) {
      const totalDataPoints = fileInfo.rows * fileInfo.columns
      const analysisScope =
        fileInfo.rows >= 10000 ? "Large Dataset" : fileInfo.rows >= 1000 ? "Medium Dataset" : "Small Dataset"
      const analyticalPower = fileInfo.columns >= 10 ? "High" : fileInfo.columns >= 5 ? "Moderate" : "Focused"

      overview += `Statistical Summary:\n`
      overview += `• Total Data Points: ${totalDataPoints.toLocaleString()}\n`
      overview += `• Analysis Scope: ${analysisScope}\n`
      overview += `• Analytical Power: ${analyticalPower}\n`
    }

    return overview
  }

  function generateMethodologyContent(): string {
    return `Analysis Framework:
• Platform: NexDatawork AI Analytics
• AI Engine: Azure OpenAI GPT-4 with LangChain Framework
• Data Processing: Automated CSV parsing and validation
• Quality Assessment: Multi-dimensional data quality scoring
• Insight Generation: AI-powered pattern recognition and business intelligence

Analysis Steps:
• Data ingestion and validation
• Column type classification and profiling
• Quality assessment and completeness analysis
• Statistical summary generation
• AI-powered insight extraction
• Visualization recommendation and generation
• Business context integration`
  }

  const updateOption = (key: keyof ExportOptions, value: any) => {
    setOptions((prev) => ({ ...prev, [key]: value }))
  }

  const updateEditableContent = (key: keyof EditableContent, value: any) => {
    setEditableContent((prev) => ({ ...prev, [key]: value }))
  }

  const updateInsight = (index: number, value: string) => {
    setEditableContent((prev) => ({
      ...prev,
      insights: prev.insights.map((insight, i) => (i === index ? value : insight)),
    }))
  }

  const addInsight = () => {
    setEditableContent((prev) => ({
      ...prev,
      insights: [...prev.insights, "New insight"],
    }))
  }

  const removeInsight = (index: number) => {
    setEditableContent((prev) => ({
      ...prev,
      insights: prev.insights.filter((_, i) => i !== index),
    }))
  }

  const extractDashboardContent = () => {
    // Extract Executive Summary, Data Evidence, and Final Answer from dashboard
    let executiveSummary = ""
    let langchainAnalysis = ""
    let insights: string[] = []

    if (analysisResults?.langchainAnalysis) {
      const content = analysisResults.langchainAnalysis
      const lines = content.split("\n")
      const sections: { [key: string]: string[] } = {
        executiveSummary: [],
        dataEvidence: [],
        finalAnswer: [],
        other: [],
      }

      let currentSection = "other"

      for (const line of lines) {
        const lowerLine = line.toLowerCase().trim()

        if (lowerLine.includes("executive summary") || lowerLine.includes("## executive summary")) {
          currentSection = "executiveSummary"
          continue
        } else if (lowerLine.includes("data evidence") || lowerLine.includes("## data evidence")) {
          currentSection = "dataEvidence"
          continue
        } else if (lowerLine.includes("final answer") || lowerLine.includes("## final answer")) {
          currentSection = "finalAnswer"
          continue
        } else if (line.startsWith("##") || line.startsWith("#")) {
          currentSection = "other"
          continue
        }

        if (currentSection !== "other" && line.trim()) {
          sections[currentSection].push(line.trim())
        }
      }

      // Combine sections for executive summary
      const summaryParts = []
      if (sections.executiveSummary.length > 0) {
        summaryParts.push("Executive Summary:")
        summaryParts.push(...sections.executiveSummary)
      }
      if (sections.dataEvidence.length > 0) {
        summaryParts.push("\nData Evidence:")
        summaryParts.push(...sections.dataEvidence)
      }
      if (sections.finalAnswer.length > 0) {
        summaryParts.push("\nFinal Answer:")
        summaryParts.push(...sections.finalAnswer)
      }

      executiveSummary = summaryParts.join("\n").trim()

      // Full analysis for the AI Analysis section
      langchainAnalysis = content

      // Extract insights from the analysis
      const allText = summaryParts.join(" ")
      const sentences = allText.split(/[.!?]+/).filter((s) => s.trim().length > 20)
      insights = sentences
        .slice(0, 5)
        .map((s) => s.trim())
        .filter((s) => s.length > 0)
    }

    if (insights.length === 0) {
      insights = ["Key insights from dashboard analysis will be displayed here."]
    }

    return {
      executiveSummary: executiveSummary || "Executive summary from dashboard analysis.",
      dataOverview: generateDataOverview(),
      insights,
      langchainAnalysis: langchainAnalysis || "AI-powered dashboard analysis will be displayed here.",
    }
  }

  const generatePreview = async () => {
    setIsGeneratingPreview(true)

    // Extract and format content that will actually appear in PDF
    const extractedContent = extractDashboardContent()

    // Update editable content with extracted dashboard content
    setEditableContent((prev) => ({
      ...prev,
      title: options.title,
      executiveSummary: extractedContent.executiveSummary,
      dataOverview: extractedContent.dataOverview,
      insights: extractedContent.insights,
      langchainAnalysis: extractedContent.langchainAnalysis,
      customNotes: options.customNotes,
      authorName: options.authorName,
      companyName: options.companyName,
    }))

    // Simulate processing time
    await new Promise((resolve) => setTimeout(resolve, 1500))

    setIsGeneratingPreview(false)
    setViewMode("preview")
  }

  const generatePDF = () => {
    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 20
    const lineHeight = 7
    let yPosition = margin

    // Helper function to add text with word wrapping
    const addText = (text: string, fontSize = 12, isBold = false, color = "#000000") => {
      doc.setFontSize(fontSize)
      doc.setFont("helvetica", isBold ? "bold" : "normal")
      doc.setTextColor(color)

      const lines = doc.splitTextToSize(text, pageWidth - 2 * margin)

      // Check if we need a new page
      if (yPosition + lines.length * lineHeight > pageHeight - margin) {
        doc.addPage()
        yPosition = margin
      }

      doc.text(lines, margin, yPosition)
      yPosition += lines.length * lineHeight + 5
    }

    // Helper function to add a section header
    const addSectionHeader = (title: string) => {
      yPosition += 10
      addText(title, 16, true, "#7c3aed")
      yPosition += 5

      // Add a line under the header
      doc.setDrawColor(124, 58, 237)
      doc.setLineWidth(0.5)
      doc.line(margin, yPosition - 3, pageWidth - margin, yPosition - 3)
      yPosition += 5
    }

    // Helper function to add bullet points
    const addBulletPoint = (text: string) => {
      const bulletText = `• ${text}`
      addText(bulletText, 11)
    }

    // Title Page
    doc.setFontSize(24)
    doc.setFont("helvetica", "bold")
    doc.setTextColor("#7c3aed")

    const titleLines = doc.splitTextToSize(editableContent.title, pageWidth - 2 * margin)
    const titleY = pageHeight / 3
    doc.text(titleLines, margin, titleY)

    // Subtitle and metadata
    yPosition = titleY + titleLines.length * 12 + 20

    addText(
      `Generated: ${new Date().toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })}`,
      12,
      false,
      "#666666",
    )

    if (editableContent.authorName) {
      addText(`Author: ${editableContent.authorName}`, 12, false, "#666666")
    }

    if (editableContent.companyName) {
      addText(`Company: ${editableContent.companyName}`, 12, false, "#666666")
    }

    addText("Powered by: NexDatawork AI Analytics Platform", 12, false, "#666666")

    // Add new page for content
    doc.addPage()
    yPosition = margin

    // Executive Summary from Dashboard
    if (options.includeExecutiveSummary && editableContent.executiveSummary) {
      addSectionHeader("Executive Summary")

      // Use the cleaned content from editableContent
      const cleanContent = editableContent.executiveSummary
        .replace(/\*\*(.*?)\*\*/g, "$1") // Remove bold markdown
        .replace(/\*(.*?)\*/g, "$1") // Remove italic markdown
        .replace(/`(.*?)`/g, "$1") // Remove code markdown
        .trim()

      addText(cleanContent, 11)
    }

    // Dataset Overview from Dashboard
    if (options.includeDataOverview) {
      addSectionHeader("Dataset Overview")
      addText(generateDataOverview(), 11)
    }

    // Dashboard Visualizations Summary
    if (options.includeVisualizations && analysisResults?.visualizations) {
      addSectionHeader("Dashboard Visualizations")

      addText("Generated Charts and Analysis:", 12, true)
      analysisResults.visualizations.forEach((viz: any, i: number) => {
        const chartType = viz.type.charAt(0).toUpperCase() + viz.type.slice(1)
        addText(`${i + 1}. ${viz.title} (${chartType} Chart)`)

        // Add chart description based on type
        if (viz.type === "pie") {
          addText("   • Distribution analysis showing proportional relationships")
        } else if (viz.type === "line") {
          addText("   • Trend analysis revealing patterns over time")
        } else if (viz.type === "bar") {
          addText("   • Comparative analysis highlighting differences between categories")
        }
      })

      yPosition += 5
      addText(
        "Note: This PDF contains the analysis summary. Interactive visualizations are available in the dashboard.",
        10,
        false,
        "#666666",
      )
    }

    // LangChain AI Analysis
    if (options.includeLangchainAnalysis && editableContent.langchainAnalysis) {
      addSectionHeader("AI-Powered Analysis")

      // Clean up the markdown content for PDF
      const cleanAnalysis = editableContent.langchainAnalysis
        .replace(/#{1,6}\s*/g, "") // Remove markdown headers
        .replace(/\*\*(.*?)\*\*/g, "$1") // Remove bold markdown
        .replace(/\*(.*?)\*/g, "$1") // Remove italic markdown
        .replace(/`(.*?)`/g, "$1") // Remove code markdown
        .replace(/---+/g, "") // Remove horizontal rules
        .replace(/\n{3,}/g, "\n\n") // Reduce multiple newlines
        .trim()

      // Split into paragraphs and add them
      const paragraphs = cleanAnalysis.split("\n\n").filter((p) => p.trim())
      paragraphs.forEach((paragraph) => {
        if (paragraph.trim()) {
          addText(paragraph.trim(), 11)
          yPosition += 3
        }
      })
    }

    // Methodology
    if (options.includeMethodology) {
      addSectionHeader("Methodology")
      addText(editableContent.methodology, 11)
    }

    // Custom Notes
    if (editableContent.customNotes.trim()) {
      addSectionHeader("Additional Notes")
      addText(editableContent.customNotes.trim())
    }

    // Key Insights from Dashboard
    if (options.includeInsights && editableContent.insights.length > 0) {
      addSectionHeader("Key Insights")
      editableContent.insights.forEach((insight: string, i: number) => {
        if (insight.trim()) {
          addText(`${i + 1}. ${insight.trim()}`, 11)
        }
      })
    }

    // Footer on last page
    const totalPages = doc.getNumberOfPages()
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)

      // Page number
      doc.setFontSize(10)
      doc.setFont("helvetica", "normal")
      doc.setTextColor("#666666")
      doc.text(`Page ${i} of ${totalPages}`, pageWidth - margin - 20, pageHeight - 10)

      // Footer on last page
      if (i === totalPages) {
        const footerY = pageHeight - 30
        doc.setFontSize(8)
        doc.text("Generated by: NexDatawork AI Analytics Platform", margin, footerY)
        doc.text(`Export Date: ${new Date().toISOString()}`, margin, footerY + 8)
        doc.text(`Report ID: ${Date.now().toString(36).toUpperCase()}`, margin, footerY + 16)
      }
    }

    return doc
  }

  const handleExport = async () => {
    setIsExporting(true)

    try {
      // Generate PDF
      const doc = generatePDF()

      // Create filename
      const filename = `${editableContent.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}.pdf`

      // Simulate processing time for better UX
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Download the PDF
      doc.save(filename)

      setViewMode("complete")

      // Auto-close after success
      setTimeout(() => {
        setViewMode("setup")
        setIsExporting(false)
        onClose()
      }, 2000)
    } catch (error) {
      console.error("PDF export failed:", error)
      setIsExporting(false)
      // You could add error handling UI here
    }
  }

  const handleClose = () => {
    if (!isExporting && !isGeneratingPreview) {
      setViewMode("setup")
      onClose()
    }
  }

  const handleBackToSetup = () => {
    setViewMode("setup")
  }

  // Setup View
  if (viewMode === "setup") {
    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-violet-600" />
              Export Analysis Report to PDF
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Report Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Report Settings
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="title" className="text-sm font-medium">
                    Report Title
                  </Label>
                  <Input
                    id="title"
                    value={options.title}
                    onChange={(e) => {
                      updateOption("title", e.target.value)
                      updateEditableContent("title", e.target.value)
                    }}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="author" className="text-sm font-medium">
                    Author Name (Optional)
                  </Label>
                  <Input
                    id="author"
                    value={options.authorName}
                    onChange={(e) => {
                      updateOption("authorName", e.target.value)
                      updateEditableContent("authorName", e.target.value)
                    }}
                    placeholder="Your name"
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="company" className="text-sm font-medium">
                  Company Name (Optional)
                </Label>
                <Input
                  id="company"
                  value={options.companyName}
                  onChange={(e) => {
                    updateOption("companyName", e.target.value)
                    updateEditableContent("companyName", e.target.value)
                  }}
                  placeholder="Your company"
                  className="mt-1"
                />
              </div>
            </div>

            {/* Content Selection */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Database className="h-4 w-4" />
                Include in PDF Report
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="summary"
                        checked={options.includeExecutiveSummary}
                        onCheckedChange={(checked) => updateOption("includeExecutiveSummary", checked)}
                      />
                      <Label htmlFor="summary" className="text-sm font-medium">
                        Executive Summary
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="overview"
                        checked={options.includeDataOverview}
                        onCheckedChange={(checked) => updateOption("includeDataOverview", checked)}
                      />
                      <Label htmlFor="overview" className="text-sm font-medium">
                        Dataset Overview
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="insights"
                        checked={options.includeInsights}
                        onCheckedChange={(checked) => updateOption("includeInsights", checked)}
                      />
                      <Label htmlFor="insights" className="text-sm font-medium">
                        Key Insights
                      </Label>
                    </div>
                  </div>
                </Card>

                <Card className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="visualizations"
                        checked={options.includeVisualizations}
                        onCheckedChange={(checked) => updateOption("includeVisualizations", checked)}
                      />
                      <Label htmlFor="visualizations" className="text-sm font-medium">
                        Visualizations Summary
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="langchain"
                        checked={options.includeLangchainAnalysis}
                        onCheckedChange={(checked) => updateOption("includeLangchainAnalysis", checked)}
                      />
                      <Label htmlFor="langchain" className="text-sm font-medium">
                        AI Analysis
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="methodology"
                        checked={options.includeMethodology}
                        onCheckedChange={(checked) => updateOption("includeMethodology", checked)}
                      />
                      <Label htmlFor="methodology" className="text-sm font-medium">
                        Methodology
                      </Label>
                    </div>
                  </div>
                </Card>
              </div>
            </div>

            {/* Custom Notes */}
            <div className="space-y-2">
              <Label htmlFor="notes" className="text-sm font-medium">
                Additional Notes (Optional)
              </Label>
              <Textarea
                id="notes"
                value={options.customNotes}
                onChange={(e) => {
                  updateOption("customNotes", e.target.value)
                  updateEditableContent("customNotes", e.target.value)
                }}
                placeholder="Add any custom notes or observations..."
                rows={3}
                className="resize-none"
              />
            </div>

            {/* Preview Info */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="bg-blue-100 rounded-full p-2">
                    <Eye className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-900 mb-1">Preview & Edit Before Export</h4>
                    <p className="text-sm text-blue-700 mb-2">
                      Generate a preview to review and edit all content before creating the final PDF.
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {options.includeExecutiveSummary && (
                        <Badge variant="secondary" className="text-xs">
                          Summary
                        </Badge>
                      )}
                      {options.includeDataOverview && (
                        <Badge variant="secondary" className="text-xs">
                          Overview
                        </Badge>
                      )}
                      {options.includeInsights && (
                        <Badge variant="secondary" className="text-xs">
                          Insights
                        </Badge>
                      )}
                      {options.includeVisualizations && (
                        <Badge variant="secondary" className="text-xs">
                          Charts
                        </Badge>
                      )}
                      {options.includeLangchainAnalysis && (
                        <Badge variant="secondary" className="text-xs">
                          AI Analysis
                        </Badge>
                      )}
                      {options.includeMethodology && (
                        <Badge variant="secondary" className="text-xs">
                          Methodology
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t">
              <Button variant="outline" onClick={handleClose} disabled={isGeneratingPreview}>
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>

              <Button
                onClick={generatePreview}
                disabled={isGeneratingPreview || !options.title.trim()}
                className="bg-violet-600 hover:bg-violet-700"
              >
                {isGeneratingPreview ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating Preview...
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    Generate Preview
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  // Preview & Edit View
  if (viewMode === "preview") {
    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit3 className="h-5 w-5 text-violet-600" />
              Preview & Edit PDF Content
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-hidden">
            <Tabs defaultValue="content" className="h-full flex flex-col">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="content">Edit Content</TabsTrigger>
                <TabsTrigger value="preview">Preview</TabsTrigger>
              </TabsList>

              <TabsContent value="content" className="flex-1 overflow-hidden">
                <ScrollArea className="h-[60vh]">
                  <div className="space-y-6 pr-4">
                    {/* Title */}
                    <div>
                      <Label className="text-sm font-medium">Report Title</Label>
                      <Input
                        value={editableContent.title}
                        onChange={(e) => updateEditableContent("title", e.target.value)}
                        className="mt-1"
                      />
                    </div>

                    {/* Executive Summary */}
                    {options.includeExecutiveSummary && (
                      <div>
                        <Label className="text-sm font-medium">Executive Summary</Label>
                        <Textarea
                          value={editableContent.executiveSummary}
                          onChange={(e) => updateEditableContent("executiveSummary", e.target.value)}
                          rows={4}
                          className="mt-1 resize-none"
                        />
                      </div>
                    )}

                    {/* Data Overview */}
                    {options.includeDataOverview && (
                      <div>
                        <Label className="text-sm font-medium">Dataset Overview</Label>
                        <Textarea
                          value={editableContent.dataOverview}
                          onChange={(e) => updateEditableContent("dataOverview", e.target.value)}
                          rows={6}
                          className="mt-1 resize-none font-mono text-sm"
                        />
                      </div>
                    )}

                    {/* Key Insights */}
                    {options.includeInsights && (
                      <div>
                        <div className="flex items-center justify-between">
                          <Label className="text-sm font-medium">Key Insights</Label>
                          <Button type="button" variant="outline" size="sm" onClick={addInsight}>
                            Add Insight
                          </Button>
                        </div>
                        <div className="space-y-2 mt-2">
                          {editableContent.insights.map((insight, index) => (
                            <div key={index} className="flex gap-2">
                              <Input
                                value={insight}
                                onChange={(e) => updateInsight(index, e.target.value)}
                                placeholder={`Insight ${index + 1}`}
                              />
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => removeInsight(index)}
                                disabled={editableContent.insights.length <= 1}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AI Analysis */}
                    {options.includeLangchainAnalysis && (
                      <div>
                        <Label className="text-sm font-medium">AI-Powered Analysis</Label>
                        <Textarea
                          value={editableContent.langchainAnalysis}
                          onChange={(e) => updateEditableContent("langchainAnalysis", e.target.value)}
                          rows={8}
                          className="mt-1 resize-none"
                        />
                      </div>
                    )}

                    {/* Methodology */}
                    {options.includeMethodology && (
                      <div>
                        <Label className="text-sm font-medium">Methodology</Label>
                        <Textarea
                          value={editableContent.methodology}
                          onChange={(e) => updateEditableContent("methodology", e.target.value)}
                          rows={6}
                          className="mt-1 resize-none font-mono text-sm"
                        />
                      </div>
                    )}

                    {/* Custom Notes */}
                    <div>
                      <Label className="text-sm font-medium">Additional Notes</Label>
                      <Textarea
                        value={editableContent.customNotes}
                        onChange={(e) => updateEditableContent("customNotes", e.target.value)}
                        rows={3}
                        className="mt-1 resize-none"
                        placeholder="Add any custom notes or observations..."
                      />
                    </div>

                    {/* Author & Company */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-medium">Author Name</Label>
                        <Input
                          value={editableContent.authorName}
                          onChange={(e) => updateEditableContent("authorName", e.target.value)}
                          placeholder="Your name"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-sm font-medium">Company Name</Label>
                        <Input
                          value={editableContent.companyName}
                          onChange={(e) => updateEditableContent("companyName", e.target.value)}
                          placeholder="Your company"
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="preview" className="flex-1 overflow-hidden">
                <ScrollArea className="h-[60vh]">
                  <div className="space-y-6 pr-4">
                    <Card>
                      <CardHeader>
                        <h2 className="text-2xl font-bold text-violet-600">{editableContent.title}</h2>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>
                            Generated:{" "}
                            {new Date().toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </p>
                          {editableContent.authorName && <p>Author: {editableContent.authorName}</p>}
                          {editableContent.companyName && <p>Company: {editableContent.companyName}</p>}
                          <p>Powered by: NexDatawork AI Analytics Platform</p>
                        </div>
                      </CardHeader>
                    </Card>

                    {options.includeExecutiveSummary && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">Executive Summary</h3>
                        </CardHeader>
                        <CardContent>
                          <p className="whitespace-pre-wrap">{editableContent.executiveSummary}</p>
                        </CardContent>
                      </Card>
                    )}

                    {options.includeDataOverview && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">Dataset Overview</h3>
                        </CardHeader>
                        <CardContent>
                          <pre className="whitespace-pre-wrap text-sm">{editableContent.dataOverview}</pre>
                        </CardContent>
                      </Card>
                    )}

                    {options.includeInsights && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">Key Insights</h3>
                        </CardHeader>
                        <CardContent>
                          <ol className="space-y-2">
                            {editableContent.insights.map((insight, index) => (
                              <li key={index} className="flex">
                                <span className="mr-2">{index + 1}.</span>
                                <span>{insight}</span>
                              </li>
                            ))}
                          </ol>
                        </CardContent>
                      </Card>
                    )}

                    {options.includeVisualizations && analysisResults?.visualizations && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">Data Visualizations</h3>
                        </CardHeader>
                        <CardContent>
                          <p className="font-medium mb-2">Generated Charts:</p>
                          <ol className="space-y-1 mb-4">
                            {analysisResults.visualizations.map((viz: any, i: number) => {
                              const chartType = viz.type.charAt(0).toUpperCase() + viz.type.slice(1)
                              return (
                                <li key={i}>
                                  {i + 1}. {viz.title} ({chartType} Chart)
                                </li>
                              )
                            })}
                          </ol>
                          <p className="text-sm text-gray-600">
                            Note: Chart images are not included in this PDF export. Please refer to the dashboard for
                            interactive visualizations.
                          </p>
                        </CardContent>
                      </Card>
                    )}

                    {options.includeLangchainAnalysis && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">AI-Powered Analysis</h3>
                        </CardHeader>
                        <CardContent>
                          <div className="whitespace-pre-wrap">{editableContent.langchainAnalysis}</div>
                        </CardContent>
                      </Card>
                    )}

                    {options.includeMethodology && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">Methodology</h3>
                        </CardHeader>
                        <CardContent>
                          <pre className="whitespace-pre-wrap text-sm">{editableContent.methodology}</pre>
                        </CardContent>
                      </Card>
                    )}

                    {editableContent.customNotes.trim() && (
                      <Card>
                        <CardHeader>
                          <h3 className="text-lg font-semibold text-violet-600">Additional Notes</h3>
                        </CardHeader>
                        <CardContent>
                          <p className="whitespace-pre-wrap">{editableContent.customNotes}</p>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t">
            <Button variant="outline" onClick={handleBackToSetup} disabled={isExporting}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Setup
            </Button>

            <Button
              onClick={handleExport}
              disabled={isExporting || !editableContent.title.trim()}
              className="bg-violet-600 hover:bg-violet-700"
            >
              {isExporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Exporting PDF...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Export Final PDF
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  // Complete View
  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <div className="text-center py-6">
          <div className="bg-green-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">PDF Export Complete!</h3>
          <p className="text-gray-600 mb-4">Your customized analysis report has been downloaded as a PDF file.</p>
          <Button onClick={handleClose} className="bg-green-600 hover:bg-green-700">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
