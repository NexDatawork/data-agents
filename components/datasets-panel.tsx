"use client"

import { useState, useEffect } from "react"
import { FileText, Download, Trash2, Calendar, HardDrive } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/hooks/use-toast"
import { getUserFiles, deleteUserFile, type FileMetadata } from "@/lib/storage"
import { getSupabaseClient } from "@/lib/supabase"

export function DatasetsPanel() {
  const [files, setFiles] = useState<FileMetadata[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [deletingFileId, setDeletingFileId] = useState<string | null>(null)
  const { toast } = useToast()

  const loadFiles = async () => {
    try {
      setIsLoading(true)

      const supabase = getSupabaseClient()
      if (!supabase) {
        toast({
          title: "Configuration Error",
          description: "Supabase is not configured.",
          variant: "destructive",
        })
        return
      }

      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser()

      if (userError || !user) {
        toast({
          title: "Authentication Error",
          description: "Please sign in to view your datasets.",
          variant: "destructive",
        })
        return
      }

      const result = await getUserFiles(user.id)

      if (!result.success) {
        toast({
          title: "Error Loading Files",
          description: result.error || "Failed to load your datasets.",
          variant: "destructive",
        })
        return
      }

      setFiles(result.data || [])
    } catch (error) {
      console.error("Error loading files:", error)
      toast({
        title: "Error",
        description: "An unexpected error occurred while loading files.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  const handleDownload = (file: FileMetadata) => {
    window.open(file.url, "_blank")
  }

  const handleDelete = async (file: FileMetadata) => {
    if (!file.id) return

    try {
      setDeletingFileId(file.id)

      const supabase = getSupabaseClient()
      if (!supabase) {
        toast({
          title: "Configuration Error",
          description: "Supabase is not configured.",
          variant: "destructive",
        })
        return
      }

      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser()

      if (userError || !user) {
        toast({
          title: "Authentication Error",
          description: "Please sign in to delete files.",
          variant: "destructive",
        })
        return
      }

      const result = await deleteUserFile(file.id, user.id)

      if (!result.success) {
        toast({
          title: "Delete Failed",
          description: result.error || "Failed to delete the file.",
          variant: "destructive",
        })
        return
      }

      // Remove file from local state
      setFiles((prev) => prev.filter((f) => f.id !== file.id))

      toast({
        title: "File Deleted",
        description: `${file.name} has been deleted successfully.`,
      })
    } catch (error) {
      console.error("Error deleting file:", error)
      toast({
        title: "Error",
        description: "An unexpected error occurred while deleting the file.",
        variant: "destructive",
      })
    } finally {
      setDeletingFileId(null)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Your Datasets
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3 flex-1">
                <Skeleton className="h-10 w-10 rounded" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-8 w-8" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Your Datasets
          {files.length > 0 && (
            <Badge variant="secondary" className="ml-2">
              {files.length}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {files.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No datasets found</h3>
            <p className="text-gray-500 mb-4">Upload your first CSV file to get started with data analysis.</p>
            <Button variant="outline" onClick={loadFiles}>
              Refresh
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="h-5 w-5 text-blue-600" />
                    </div>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 truncate">{file.name}</h4>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{file.created_at ? formatDate(file.created_at) : "Unknown date"}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        <HardDrive className="h-3 w-3" />
                        <span>{formatFileSize(file.size)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(file)}
                    className="flex items-center gap-1"
                  >
                    <Download className="h-3 w-3" />
                    Download
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(file)}
                    disabled={deletingFileId === file.id}
                    className="flex items-center gap-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-3 w-3" />
                    {deletingFileId === file.id ? "Deleting..." : "Delete"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
