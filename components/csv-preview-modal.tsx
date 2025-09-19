"use client"
import { FileText, Database, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"

interface CSVPreviewModalProps {
  isOpen: boolean
  onClose: () => void
  onProceed: () => void
  csvData: string[][]
  fileName: string
  fileSize: number
  totalRows: number
  totalColumns: number
  isUploading?: boolean
}

export function CSVPreviewModal({
  isOpen,
  onClose,
  onProceed,
  csvData,
  fileName,
  fileSize,
  totalRows,
  totalColumns,
  isUploading = false,
}: CSVPreviewModalProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  // Show first 10 rows and 10 columns
  const previewData = csvData.slice(0, 10).map((row) => row.slice(0, 10))
  const headers = previewData[0] || []
  const rows = previewData.slice(1)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            CSV Data Preview
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col">
          {/* File Info */}
          <div className="flex-shrink-0 bg-gray-50 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">{fileName}</h3>
              <Badge variant="secondary">{formatFileSize(fileSize)}</Badge>
            </div>
            <div className="flex gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Database className="h-4 w-4" />
                <span>{totalRows.toLocaleString()} rows</span>
              </div>
              <div className="flex items-center gap-1">
                <Database className="h-4 w-4" />
                <span>{totalColumns} columns</span>
              </div>
            </div>
          </div>

          {/* Data Preview */}
          <div className="flex-1 overflow-auto border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  {headers.map((header, index) => (
                    <th
                      key={index}
                      className="px-3 py-2 text-left font-medium text-gray-900 border-r border-gray-200 min-w-[120px]"
                    >
                      {header || `Column ${index + 1}`}
                    </th>
                  ))}
                  {totalColumns > 10 && (
                    <th className="px-3 py-2 text-left font-medium text-gray-500">
                      ... +{totalColumns - 10} more columns
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, rowIndex) => (
                  <tr key={rowIndex} className="border-b border-gray-100 hover:bg-gray-50">
                    {row.map((cell, cellIndex) => (
                      <td
                        key={cellIndex}
                        className="px-3 py-2 border-r border-gray-100 max-w-[200px] truncate"
                        title={cell}
                      >
                        {cell}
                      </td>
                    ))}
                    {totalColumns > 10 && <td className="px-3 py-2 text-gray-500">...</td>}
                  </tr>
                ))}
                {totalRows > 10 && (
                  <tr>
                    <td
                      colSpan={Math.min(totalColumns, 10) + (totalColumns > 10 ? 1 : 0)}
                      className="px-3 py-2 text-center text-gray-500"
                    >
                      ... +{totalRows - 10} more rows
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Actions */}
          <div className="flex-shrink-0 flex items-center justify-between pt-4">
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>CSV format validated successfully</span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose} disabled={isUploading}>
                Cancel
              </Button>
              <Button onClick={onProceed} disabled={isUploading} className="bg-primary hover:bg-primary/90">
                {isUploading ? "Uploading..." : "Proceed with Configuration"}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
