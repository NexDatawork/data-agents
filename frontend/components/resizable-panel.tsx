"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface ResizablePanelProps {
  children: React.ReactNode
  defaultWidth: string
  minWidth: string
  maxWidth: string
  id: string
  className?: string
  onWidthChange?: (width: string) => void
}

export function ResizablePanel({
  children,
  defaultWidth,
  minWidth,
  maxWidth,
  id,
  className,
  onWidthChange,
}: ResizablePanelProps) {
  const [width, setWidth] = useState(defaultWidth)
  const [isDragging, setIsDragging] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const dragHandleRef = useRef<HTMLDivElement>(null)

  // Store the initial width and mouse position when dragging starts
  const dragInfo = useRef({
    startX: 0,
    startWidth: 0,
    parentWidth: 0,
  })

  // Handle mouse down on the drag handle
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)

    if (panelRef.current && panelRef.current.parentElement) {
      const parentWidth = panelRef.current.parentElement.getBoundingClientRect().width
      const currentWidth = panelRef.current.getBoundingClientRect().width

      dragInfo.current = {
        startX: e.clientX,
        startWidth: currentWidth,
        parentWidth: parentWidth,
      }
    }
  }

  // Handle mouse move to resize the panel
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return

    const deltaX = e.clientX - dragInfo.current.startX
    const newWidth = dragInfo.current.startWidth + deltaX

    // Calculate percentage width
    const percentWidth = (newWidth / dragInfo.current.parentWidth) * 100

    // Convert min and max width from string to number (removing the % sign)
    const minWidthNum = Number.parseFloat(minWidth)
    const maxWidthNum = Number.parseFloat(maxWidth)

    // Clamp the width between min and max
    const clampedWidth = Math.max(minWidthNum, Math.min(maxWidthNum, percentWidth))
    const newWidthStr = `${clampedWidth}%`

    setWidth(newWidthStr)
    if (onWidthChange) {
      onWidthChange(newWidthStr)
    }
  }

  // Handle mouse up to stop dragging
  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // Add and remove event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
    } else {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isDragging])

  useEffect(() => {
    setWidth(defaultWidth)
  }, [defaultWidth])

  return (
    <div ref={panelRef} id={id} className={cn("relative flex-shrink-0", className)} style={{ width }}>
      {children}
      <div
        ref={dragHandleRef}
        className={cn(
          "absolute top-0 right-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/30 transition-colors z-10",
          isDragging ? "bg-primary/50" : "bg-transparent",
        )}
        onMouseDown={handleMouseDown}
        aria-hidden="true"
        title="Drag to resize panel"
      />
    </div>
  )
}
