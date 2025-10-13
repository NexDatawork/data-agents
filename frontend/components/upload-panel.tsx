"use client"

import type React from "react"
import { useState, useEffect, useRef } from "react"
import { BarChart3, Upload, Database, FileText, TrendingUp, ChevronLeft, ChevronRight, X, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { CSVPreviewModal } from "./csv-preview-modal"
import { uploadFileToStorage } from "@/lib/storage"
import { getSupabaseClient } from "@/lib/supabase"
import { useToast } from "@/hooks/use-toast"
import { Textarea } from "@/components/ui/textarea"

interface UploadPanelProps {
  onFileUpload: (files: File[]) => void
  onIndustryChange: (value: string) => void
  onTopicChange: (value: string) => void
  onRequirementChange: (value: string) => void
  onCustomRequirementChange: (value: string) => void
  onRunAnalysis: () => void
  onCollapseChange: (collapsed: boolean) => void
  onViewChange: (view: "dashboard" | "log" | "datasets") => void
  onWidthChange?: (width: number) => void
  files: File[]
  industry: string
  topic: string
  requirement: string
  customRequirement: string
}

export function UploadPanel({
  onFileUpload,
  onIndustryChange,
  onTopicChange,
  onRequirementChange,
  onCustomRequirementChange,
  onRunAnalysis,
  onCollapseChange,
  onViewChange,
  onWidthChange,
  files,
  industry,
  topic,
  requirement,
  customRequirement,
}: UploadPanelProps) {
  const [dragActive, setDragActive] = useState(false)
  const [activeItem, setActiveItem] = useState("dashboard")
  const [collapsed, setCollapsed] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const { toast } = useToast()
  const [customRequirementState, setCustomRequirement] = useState<string>("")

  // CSV Preview Modal states
  const [showPreview, setShowPreview] = useState(false)
  const [csvData, setCsvData] = useState<string[][]>([])
  const [previewFile, setPreviewFile] = useState<File | null>(null)
  const [totalRows, setTotalRows] = useState(0)
  const [totalColumns, setTotalColumns] = useState(0)

  // Multiple selection states
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([])
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [selectedRequirements, setSelectedRequirements] = useState<string[]>([])

  // Resize functionality state and refs
  const [isResizing, setIsResizing] = useState(false)
  const resizeRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  // Initialize with any existing selections
  useEffect(() => {
    if (industry) setSelectedIndustries([industry])
    if (topic) setSelectedTopics([topic])
    if (requirement) setSelectedRequirements([requirement])
  }, [industry, topic, requirement])

  // Update parent component when selections change
  useEffect(() => {
    if (selectedIndustries.length > 0) onIndustryChange(selectedIndustries[0])
    else onIndustryChange("")
  }, [selectedIndustries, onIndustryChange])

  useEffect(() => {
    if (selectedTopics.length > 0) onTopicChange(selectedTopics[0])
    else onTopicChange("")
  }, [selectedTopics, onTopicChange])

  useEffect(() => {
    if (selectedRequirements.length > 0) onRequirementChange(selectedRequirements[0])
    else onRequirementChange("")
  }, [selectedRequirements, onRequirementChange])

  useEffect(() => {
    onCustomRequirementChange(customRequirementState)
  }, [customRequirementState, onCustomRequirementChange])

  // Parse CSV file for preview
  const parseCSVFile = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      if (text) {
        try {
          // Simple CSV parsing - split by lines and commas
          const lines = text.split("\n").filter((line) => line.trim() !== "")
          const parsedData = lines.map((line) => {
            // Handle quoted fields and commas within quotes
            const result = []
            let current = ""
            let inQuotes = false

            for (let i = 0; i < line.length; i++) {
              const char = line[i]
              if (char === '"') {
                inQuotes = !inQuotes
              } else if (char === "," && !inQuotes) {
                result.push(current.trim())
                current = ""
              } else {
                current += char
              }
            }
            result.push(current.trim())
            return result
          })

          setCsvData(parsedData)
          setTotalRows(parsedData.length)
          setTotalColumns(parsedData[0]?.length || 0)
          setPreviewFile(file)
          setShowPreview(true)
        } catch (error) {
          console.error("Error parsing CSV:", error)
          toast({
            title: "Error parsing CSV",
            description: "Please check the file format and try again.",
            variant: "destructive",
          })
        }
      }
    }
    reader.readAsText(file)
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files)
      // Show preview for the first CSV file
      const csvFile = newFiles.find((file) => file.name.toLowerCase().endsWith(".csv"))
      if (csvFile) {
        parseCSVFile(csvFile)
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      // Show preview for the first CSV file
      const csvFile = newFiles.find((file) => file.name.toLowerCase().endsWith(".csv"))
      if (csvFile) {
        parseCSVFile(csvFile)
      }
    }
  }

  const handleFileUploadClick = () => {
    const fileInput = document.createElement("input")
    fileInput.type = "file"
    fileInput.multiple = true
    fileInput.accept = ".csv"
    fileInput.onchange = (e) => {
      const target = e.target as HTMLInputElement
      if (target.files && target.files.length > 0) {
        const newFiles = Array.from(target.files)
        // Show preview for the first CSV file
        const csvFile = newFiles.find((file) => file.name.toLowerCase().endsWith(".csv"))
        if (csvFile) {
          parseCSVFile(csvFile)
        }
      }
    }
    fileInput.click()
  }

  const handlePreviewProceed = async () => {
    if (!previewFile) return

    setIsUploading(true)
    try {
      // Get current user
      const supabase = getSupabaseClient()
      if (!supabase) {
        toast({
          title: "Configuration Error",
          description: "Supabase is not configured. File will be processed locally.",
          variant: "destructive",
        })
        // Add the file to the files list for local processing
        onFileUpload([previewFile])
        setActiveItem("upload")
        setShowPreview(false)
        return
      }

      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser()

      if (userError || !user) {
        toast({
          title: "Authentication Error",
          description: "Please sign in to upload files to storage.",
          variant: "destructive",
        })
        // Add the file to the files list for local processing
        onFileUpload([previewFile])
        setActiveItem("upload")
        setShowPreview(false)
        return
      }

      // Upload file to Supabase Storage
      const uploadResult = await uploadFileToStorage(previewFile, user.id)

      if (!uploadResult.success) {
        toast({
          title: "Upload Failed",
          description: uploadResult.error || "Failed to upload file to storage.",
          variant: "destructive",
        })
        // Fall back to local processing
        onFileUpload([previewFile])
        setActiveItem("upload")
        setShowPreview(false)
        return
      }

      toast({
        title: "File Uploaded Successfully",
        description: `${previewFile.name} has been saved to your datasets.`,
      })

      // Add the file to the files list for analysis
      onFileUpload([previewFile])
      setActiveItem("upload") // Switch to upload tab for configuration
    } catch (error) {
      console.error("Error uploading file:", error)
      toast({
        title: "Upload Error",
        description: "An unexpected error occurred. File will be processed locally.",
        variant: "destructive",
      })
      // Fall back to local processing
      onFileUpload([previewFile])
      setActiveItem("upload")
    } finally {
      setIsUploading(false)
      setShowPreview(false)
    }
  }

  const handlePreviewCancel = () => {
    setShowPreview(false)
    setPreviewFile(null)
    setCsvData([])
  }

  const toggleIndustry = (value: string) => {
    setSelectedIndustries((prev) => (prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value]))
  }

  const toggleTopic = (value: string) => {
    setSelectedTopics((prev) => (prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value]))
  }

  const toggleRequirement = (value: string) => {
    setSelectedRequirements((prev) => (prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value]))
  }

  const menuItems = [
    { id: "dashboard", label: "Home", icon: BarChart3, active: true },
    { id: "upload", label: "Data Upload", icon: Upload },
    { id: "analysis", label: "Analysis", icon: TrendingUp },
    { id: "log", label: "Log", icon: FileText },
    { id: "reports", label: "Reports", icon: FileText },
    { id: "datasets", label: "Datasets", icon: Database },
  ]

  const industries = [
    { value: "retail", label: "Retail" },
    { value: "finance", label: "Finance" },
    { value: "healthcare", label: "Healthcare" },
    { value: "technology", label: "Technology" },
    { value: "manufacturing", label: "Manufacturing" },
    { value: "education", label: "Education" },
  ]

  const topics = [
    { value: "sales", label: "Sales Analysis" },
    { value: "customer", label: "Customer Behavior" },
    { value: "operations", label: "Operations" },
    { value: "marketing", label: "Marketing" },
    { value: "financial", label: "Financial" },
    { value: "predictive", label: "Predictive" },
  ]

  const requirements = [
    { value: "trends", label: "Trend Analysis" },
    { value: "forecasting", label: "Forecasting" },
    { value: "segmentation", label: "Segmentation" },
    { value: "correlation", label: "Correlation" },
    { value: "anomalies", label: "Anomaly Detection" },
    { value: "optimization", label: "Optimization" },
  ]

  // Resize handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing || !panelRef.current) return

    const newWidth = (e.clientX / window.innerWidth) * 100

    // Constrain width between 20% and 50%
    const constrainedWidth = Math.min(Math.max(newWidth, 20), 50)

    if (onWidthChange) {
      onWidthChange(constrainedWidth)
    }
  }

  const handleMouseUp = () => {
    setIsResizing(false)
  }

  // Resize event listeners
  useEffect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = "col-resize"
      document.body.style.userSelect = "none"
    } else {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
  }, [isResizing, onWidthChange])

  return (
    <>
      <div
        ref={panelRef}
        className={cn(
          "bg-gray-100 rounded-none shadow-none border-r border-border/30 transition-all duration-300 flex flex-col overflow-hidden h-full relative",
          collapsed ? "w-16" : "w-full",
        )}
      >
        {/* Header with collapse button */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0 bg-gray-100">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full flex items-center justify-center bg-violet-700">
                <BarChart3 className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-purple-700">NexDatawork</span>
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center mx-auto">
              <BarChart3 className="h-4 w-4 text-white" />
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => {
              const newCollapsed = !collapsed
              setCollapsed(newCollapsed)
              onCollapseChange(newCollapsed)
            }}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        {/* Sidebar content - takes remaining space */}
        <div className="flex-1 overflow-y-auto flex flex-col min-h-0 bg-gray-100">
          {/* Navigation */}
          <div className="p-3 flex-shrink-0">
            {!collapsed && (
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 px-3">Menu</h3>
            )}
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = item.id === activeItem
                return (
                  <div key={item.id}>
                    <button
                      onClick={() => {
                        if (item.id === "upload") {
                          // Toggle upload configuration
                          setActiveItem(activeItem === "upload" ? "dashboard" : "upload")
                        } else {
                          setActiveItem(item.id)
                          if (item.id === "dashboard" || item.id === "log" || item.id === "datasets") {
                            onViewChange(item.id as "dashboard" | "log" | "datasets")
                          }
                        }
                      }}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                        isActive
                          ? "bg-primary/20 text-primary font-medium"
                          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                        collapsed && "justify-center",
                      )}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      {!collapsed && <span className="font-medium">{item.label}</span>}
                    </button>

                    {/* Show configuration immediately after Data Upload item */}
                    {item.id === "upload" && !collapsed && activeItem === "upload" && (
                      <div className="mt-2 mb-4 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
                          Configuration
                        </h4>

                        {/* File Upload */}
                        <div className="mb-4">
                          <Label className="text-sm font-medium text-gray-700 mb-2 block">Upload Files</Label>
                          <div
                            className={cn(
                              "border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-all",
                              dragActive ? "border-primary/50 bg-primary/5" : "border-gray-200 hover:border-gray-300",
                            )}
                            onDragEnter={handleDrag}
                            onDragOver={handleDrag}
                            onDragLeave={handleDrag}
                            onDrop={handleDrop}
                            onClick={handleFileUploadClick}
                          >
                            <Upload className="h-6 w-6 mx-auto mb-2 text-gray-400" />
                            <p className="text-xs text-gray-500">Drop or click to upload multiple CSV files</p>
                          </div>

                          {/* File list */}
                          {files.length > 0 && (
                            <div className="mt-3 space-y-2">
                              {files.map((file, index) => (
                                <div
                                  key={index}
                                  className="flex items-center justify-between bg-white rounded-md p-2 text-sm border"
                                >
                                  <span className="truncate max-w-[160px]">{file.name}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      const newFiles = [...files]
                                      newFiles.splice(index, 1)
                                      onFileUpload(newFiles)
                                    }}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Industry Multi-Select */}
                        <div className="mb-4">
                          <Label className="text-sm font-medium text-gray-700 mb-2 block">Industries (Optional)</Label>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-between h-9 px-3 text-sm bg-transparent"
                                size="sm"
                              >
                                {selectedIndustries.length === 0
                                  ? "Select industries..."
                                  : `${selectedIndustries.length} selected`}
                                <Plus className="h-3 w-3 opacity-50" />
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-full p-0" align="start">
                              <Command>
                                <CommandInput placeholder="Search industries..." className="h-9" />
                                <CommandList>
                                  <CommandEmpty>No industries found.</CommandEmpty>
                                  <CommandGroup>
                                    {industries.map((industry) => (
                                      <CommandItem
                                        key={industry.value}
                                        onSelect={() => toggleIndustry(industry.value)}
                                        className="cursor-pointer"
                                      >
                                        <div
                                          className={cn(
                                            "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                            selectedIndustries.includes(industry.value)
                                              ? "bg-primary text-primary-foreground"
                                              : "opacity-50 [&_svg]:invisible",
                                          )}
                                        >
                                          <svg
                                            className="h-3 w-3"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                          >
                                            <path
                                              strokeLinecap="round"
                                              strokeLinejoin="round"
                                              strokeWidth={2}
                                              d="M5 13l4 4L19 7"
                                            />
                                          </svg>
                                        </div>
                                        {industry.label}
                                      </CommandItem>
                                    ))}
                                  </CommandGroup>
                                </CommandList>
                              </Command>
                            </PopoverContent>
                          </Popover>
                          {selectedIndustries.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {selectedIndustries.map((industryValue) => {
                                const industryLabel =
                                  industries.find((i) => i.value === industryValue)?.label || industryValue
                                return (
                                  <Badge key={industryValue} variant="secondary" className="text-xs">
                                    {industryLabel}
                                    <button
                                      onClick={() => toggleIndustry(industryValue)}
                                      className="ml-1 hover:bg-gray-300 rounded-full"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </Badge>
                                )
                              })}
                            </div>
                          )}
                        </div>

                        {/* Topic Multi-Select */}
                        <div className="mb-4">
                          <Label className="text-sm font-medium text-gray-700 mb-2 block">Topics (Optional)</Label>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-between h-9 px-3 text-sm bg-transparent"
                                size="sm"
                              >
                                {selectedTopics.length === 0 ? "Select topics..." : `${selectedTopics.length} selected`}
                                <Plus className="h-3 w-3 opacity-50" />
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-full p-0" align="start">
                              <Command>
                                <CommandInput placeholder="Search topics..." className="h-9" />
                                <CommandList>
                                  <CommandEmpty>No topics found.</CommandEmpty>
                                  <CommandGroup>
                                    {topics.map((topic) => (
                                      <CommandItem
                                        key={topic.value}
                                        onSelect={() => toggleTopic(topic.value)}
                                        className="cursor-pointer"
                                      >
                                        <div
                                          className={cn(
                                            "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                            selectedTopics.includes(topic.value)
                                              ? "bg-primary text-primary-foreground"
                                              : "opacity-50 [&_svg]:invisible",
                                          )}
                                        >
                                          <svg
                                            className="h-3 w-3"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                          >
                                            <path
                                              strokeLinecap="round"
                                              strokeLinejoin="round"
                                              strokeWidth={2}
                                              d="M5 13l4 4L19 7"
                                            />
                                          </svg>
                                        </div>
                                        {topic.label}
                                      </CommandItem>
                                    ))}
                                  </CommandGroup>
                                </CommandList>
                              </Command>
                            </PopoverContent>
                          </Popover>
                          {selectedTopics.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {selectedTopics.map((topicValue) => {
                                const topicLabel = topics.find((t) => t.value === topicValue)?.label || topicValue
                                return (
                                  <Badge key={topicValue} variant="secondary" className="text-xs">
                                    {topicLabel}
                                    <button
                                      onClick={() => toggleTopic(topicValue)}
                                      className="ml-1 hover:bg-gray-300 rounded-full"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </Badge>
                                )
                              })}
                            </div>
                          )}
                        </div>

                        {/* Requirements Multi-Select */}
                        <div className="mb-4">
                          <Label className="text-sm font-medium text-gray-700 mb-2 block">
                            Requirements (Optional)
                          </Label>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-between h-9 px-3 text-sm bg-transparent"
                                size="sm"
                              >
                                {selectedRequirements.length === 0
                                  ? "Select requirements..."
                                  : `${selectedRequirements.length} selected`}
                                <Plus className="h-3 w-3 opacity-50" />
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-full p-0" align="start">
                              <Command>
                                <CommandInput placeholder="Search requirements..." className="h-9" />
                                <CommandList>
                                  <CommandEmpty>No requirements found.</CommandEmpty>
                                  <CommandGroup>
                                    {requirements.map((requirement) => (
                                      <CommandItem
                                        key={requirement.value}
                                        onSelect={() => toggleRequirement(requirement.value)}
                                        className="cursor-pointer"
                                      >
                                        <div
                                          className={cn(
                                            "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                            selectedRequirements.includes(requirement.value)
                                              ? "bg-primary text-primary-foreground"
                                              : "opacity-50 [&_svg]:invisible",
                                          )}
                                        >
                                          <svg
                                            className="h-3 w-3"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                          >
                                            <path
                                              strokeLinecap="round"
                                              strokeLinejoin="round"
                                              strokeWidth={2}
                                              d="M5 13l4 4L19 7"
                                            />
                                          </svg>
                                        </div>
                                        {requirement.label}
                                      </CommandItem>
                                    ))}
                                  </CommandGroup>
                                </CommandList>
                              </Command>
                            </PopoverContent>
                          </Popover>
                          {selectedRequirements.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {selectedRequirements.map((requirementValue) => {
                                const requirementLabel =
                                  requirements.find((r) => r.value === requirementValue)?.label || requirementValue
                                return (
                                  <Badge key={requirementValue} variant="secondary" className="text-xs">
                                    {requirementLabel}
                                    <button
                                      onClick={() => toggleRequirement(requirementValue)}
                                      className="ml-1 hover:bg-gray-300 rounded-full"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </Badge>
                                )
                              })}
                            </div>
                          )}
                        </div>

                        {/* Custom Analysis Requirements Chatbox */}
                        <div className="mb-4">
                          <Label className="text-sm font-medium text-gray-700 mb-2 block">
                            Custom Analysis Requirements (Optional)
                          </Label>
                          <div className="space-y-2">
                            <Textarea
                              placeholder="Describe your specific analysis needs... "
                              value={customRequirementState}
                              onChange={(e) => setCustomRequirement(e.target.value)}
                              className="min-h-[80px] text-sm resize-none"
                              maxLength={500}
                            />
                            <div className="flex justify-between items-center text-xs text-gray-500">
                              <span>Be specific about what insights you're looking for</span>
                              <span>{customRequirementState.length}/500</span>
                            </div>
                          </div>
                        </div>

                        {/* Run Analysis Button */}
                        <Button
                          onClick={onRunAnalysis}
                          disabled={files.length === 0}
                          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
                          size="sm"
                        >
                          <TrendingUp className="h-4 w-4 mr-2" />
                          Run Analysis
                        </Button>
                      </div>
                    )}
                  </div>
                )
              })}
            </nav>
          </div>
        </div>

        {/* Resize handle */}
        {!collapsed && (
          <div
            ref={resizeRef}
            className="absolute top-0 right-0 w-1 h-full cursor-col-resize bg-transparent hover:bg-purple-300 transition-colors z-10 group"
            onMouseDown={handleMouseDown}
          >
            <div className="absolute top-1/2 right-0 transform -translate-y-1/2 w-3 h-8 bg-gray-300 group-hover:bg-purple-400 rounded-l-md opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        )}
      </div>

      {/* CSV Preview Modal */}
      <CSVPreviewModal
        isOpen={showPreview}
        onClose={handlePreviewCancel}
        onProceed={handlePreviewProceed}
        csvData={csvData}
        fileName={previewFile?.name || ""}
        totalRows={totalRows}
        totalColumns={totalColumns}
        isUploading={isUploading}
      />
    </>
  )
}
