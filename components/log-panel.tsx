"use client"

import { useState } from "react"
import {
  FileText,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  Play,
  Pause,
  MoreHorizontal,
  Eye,
  Download,
  RefreshCw,
  Send,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function LogPanel() {
  const [activeTab, setActiveTab] = useState("insights")

  // Mock data for recent insights
  const recentInsights = [
    {
      id: 1,
      title: "Sales Performance Analysis",
      summary: "Revenue increased by 15% YoY with strong performance in Q4",
      timestamp: "2 hours ago",
      type: "analysis",
      charts: ["bar", "line"],
      insights: [
        "Product Category A shows highest growth rate",
        "Customer retention improved by 8%",
        "Regional performance varies significantly",
      ],
    },
    {
      id: 2,
      title: "Customer Segmentation Report",
      summary: "Identified 4 distinct customer segments with varying behaviors",
      timestamp: "5 hours ago",
      type: "segmentation",
      charts: ["pie", "scatter"],
      insights: [
        "Premium segment shows 40% higher LTV",
        "Budget segment represents 60% of volume",
        "Seasonal patterns detected in purchasing",
      ],
    },
    {
      id: 3,
      title: "Trend Forecasting",
      summary: "Predictive model shows 12% growth potential for next quarter",
      timestamp: "1 day ago",
      type: "forecast",
      charts: ["line", "area"],
      insights: [
        "Upward trend in digital channels",
        "Seasonal adjustment needed for Q1",
        "Market expansion opportunities identified",
      ],
    },
  ]

  // Mock data for active workflows
  const activeWorkflows = [
    {
      id: 1,
      name: "Daily Sales Analytics",
      status: "running",
      progress: 75,
      lastRun: "10 minutes ago",
      nextRun: "in 50 minutes",
      type: "scheduled",
    },
    {
      id: 2,
      name: "Customer Behavior Pipeline",
      status: "completed",
      progress: 100,
      lastRun: "2 hours ago",
      nextRun: "in 22 hours",
      type: "scheduled",
    },
    {
      id: 3,
      name: "Inventory Optimization",
      status: "paused",
      progress: 45,
      lastRun: "1 day ago",
      nextRun: "manual",
      type: "manual",
    },
    {
      id: 4,
      name: "Marketing Attribution",
      status: "error",
      progress: 30,
      lastRun: "3 hours ago",
      nextRun: "retry pending",
      type: "triggered",
    },
  ]

  // Mock data for agent logs
  const agentLogs = [
    {
      id: 1,
      timestamp: "2024-01-15 14:30:25",
      level: "info",
      message: "Data analysis completed successfully",
      agent: "DataAnalyzer",
      duration: "2.3s",
      details: "Processed 1,245 records across 18 fields",
    },
    {
      id: 2,
      timestamp: "2024-01-15 14:28:12",
      level: "warning",
      message: "Missing values detected in dataset",
      agent: "DataValidator",
      duration: "0.8s",
      details: "12 missing values in 'customer_age' column",
    },
    {
      id: 3,
      timestamp: "2024-01-15 14:25:45",
      level: "info",
      message: "Model training initiated",
      agent: "MLTrainer",
      duration: "45.2s",
      details: "Random Forest model with 100 estimators",
    },
    {
      id: 4,
      timestamp: "2024-01-15 14:20:33",
      level: "error",
      message: "API rate limit exceeded",
      agent: "DataFetcher",
      duration: "0.1s",
      details: "External API returned 429 status code",
    },
    {
      id: 5,
      timestamp: "2024-01-15 14:15:18",
      level: "info",
      message: "Visualization generated",
      agent: "ChartGenerator",
      duration: "1.5s",
      details: "Created bar chart with 5 categories",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-blue-100 text-blue-800"
      case "completed":
        return "bg-green-100 text-green-800"
      case "paused":
        return "bg-yellow-100 text-yellow-800"
      case "error":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case "info":
        return "bg-blue-100 text-blue-800"
      case "warning":
        return "bg-yellow-100 text-yellow-800"
      case "error":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="w-full h-full bg-white rounded-xl shadow-sm border border-border/30 flex flex-col overflow-hidden">
      <div className="px-4 pt-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            System Logs & Analytics
          </h2>
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full justify-start bg-secondary">
            <TabsTrigger value="insights" className="flex items-center gap-2 data-[state=active]:bg-white">
              <TrendingUp className="h-4 w-4" />
              Recent Insights
            </TabsTrigger>
            <TabsTrigger value="workflows" className="flex items-center gap-2 data-[state=active]:bg-white">
              <Activity className="h-4 w-4" />
              Active Workflows
            </TabsTrigger>
            <TabsTrigger value="logs" className="flex items-center gap-2 data-[state=active]:bg-white">
              <FileText className="h-4 w-4" />
              Agent Logs
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2 data-[state=active]:bg-white">
              <Activity className="h-4 w-4" />
              Chat
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <Tabs value={activeTab} className="h-full">
          {/* Recent Insights Tab */}
          <TabsContent value="insights" className="space-y-4 mt-0">
            {recentInsights.map((insight) => (
              <Card key={insight.id} className="bg-white border border-border/30">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <div className="bg-primary/10 rounded-full p-1.5">
                          <TrendingUp className="h-4 w-4 text-primary" />
                        </div>
                        {insight.title}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">{insight.summary}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {insight.type}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{insight.timestamp}</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-sm font-medium mb-2">Key Insights</h4>
                      <ul className="space-y-1">
                        {insight.insights.map((item, index) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Charts:</span>
                        {insight.charts.map((chart, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {chart}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4 mr-1" />
                          Export
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* Active Workflows Tab */}
          <TabsContent value="workflows" className="space-y-4 mt-0">
            {activeWorkflows.map((workflow) => (
              <Card key={workflow.id} className="bg-white border border-border/30">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <div className="bg-primary/10 rounded-full p-1.5">
                        <Activity className="h-4 w-4 text-primary" />
                      </div>
                      {workflow.name}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge className={getStatusColor(workflow.status)}>{workflow.status}</Badge>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="font-medium">{workflow.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all duration-300"
                        style={{ width: `${workflow.progress}%` }}
                      ></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Last Run:</span>
                        <p className="font-medium">{workflow.lastRun}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Next Run:</span>
                        <p className="font-medium">{workflow.nextRun}</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t">
                      <Badge variant="outline" className="text-xs">
                        {workflow.type}
                      </Badge>
                      <div className="flex items-center gap-2">
                        {workflow.status === "running" ? (
                          <Button variant="ghost" size="sm">
                            <Pause className="h-4 w-4 mr-1" />
                            Pause
                          </Button>
                        ) : (
                          <Button variant="ghost" size="sm">
                            <Play className="h-4 w-4 mr-1" />
                            Run
                          </Button>
                        )}
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4 mr-1" />
                          Details
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* Agent Logs Tab */}
          <TabsContent value="logs" className="space-y-2 mt-0">
            <div className="space-y-2">
              {agentLogs.map((log) => (
                <Card key={log.id} className="bg-white border border-border/30">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={getLogLevelColor(log.level)}>{log.level.toUpperCase()}</Badge>
                          <span className="text-sm font-medium">{log.agent}</span>
                          <span className="text-xs text-muted-foreground">{log.duration}</span>
                        </div>
                        <p className="text-sm font-medium mb-1">{log.message}</p>
                        <p className="text-xs text-muted-foreground">{log.details}</p>
                      </div>
                      <div className="text-xs text-muted-foreground text-right">
                        <Clock className="h-3 w-3 inline mr-1" />
                        {log.timestamp}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat" className="mt-0 h-full">
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {/* User message */}
                <div className="bg-blue-50 rounded-lg p-3 ml-auto max-w-[80%]">
                  <p className="text-sm text-blue-900">Tell me about this dataset</p>
                </div>

                {/* AI response with exact formatting from the image */}
                <div className="bg-white border rounded-lg p-4 max-w-[90%]">
                  <div className="space-y-4">
                    {/* Header with checkmark */}
                    <div className="flex items-center gap-2">
                      <span className="text-green-600 text-lg">✅</span>
                      <h3 className="font-semibold text-lg">Azure OpenAI Analysis Complete!</h3>
                    </div>

                    {/* File info section */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span>📊</span>
                        <span>
                          <strong>File:</strong> Walmart_Sales.csv
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span>📏</span>
                        <span>
                          <strong>Size:</strong> 6,435 rows × 8 columns
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span>🧠</span>
                        <span>
                          <strong>AI Analysis:</strong> Advanced reasoning with Azure OpenAI
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span>👤</span>
                        <span>
                          <strong>Personalized for:</strong> General analysis
                        </span>
                      </div>
                    </div>

                    {/* Key insights section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span>🔍</span>
                        <h4 className="font-semibold">Key Insights for analysis:</h4>
                      </div>

                      <div className="space-y-1 ml-6">
                        <div className="flex items-start gap-2">
                          <span className="text-xs mt-1.5">•</span>
                          <span>Dataset contains 6435 records with 8 columns</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-xs mt-1.5">•</span>
                          <span>Found 7 numeric columns: Store, Weekly_Sales, Holiday_Flag...</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-xs mt-1.5">•</span>
                          <span>Found 1 categorical columns: Date</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-xs mt-1.5">•</span>
                          <span>No missing data detected - dataset is complete</span>
                        </div>
                        <div className="flex items-start gap-2">
                          <span className="text-xs mt-1.5">•</span>
                          <span>Column 'Date' has 143 unique values</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Chat input */}
              <div className="border-t pt-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Ask about your data..."
                    className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Button size="sm">
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
