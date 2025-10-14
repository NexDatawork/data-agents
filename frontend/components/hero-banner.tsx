"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowRight, Users } from "lucide-react"

export function HeroBanner() {
  return (
    <Card className="bg-gradient-to-r from-purple-600 to-purple-700 border-0 shadow-lg overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-r from-purple-600/90 to-purple-700/90"></div>
      <div className="relative p-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="bg-white/20 rounded-full p-3">
            <Users className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white mb-1">
              Your Data Agent for All Data Work - Join Our Community
            </h2>
            <p className="text-purple-100 text-sm">
              Connect with data professionals and unlock advanced analytics features
            </p>
          </div>
        </div>
        <Button
          className="bg-white text-purple-700 hover:bg-purple-50 font-semibold px-6 py-2 shadow-md transition-all duration-200 hover:shadow-lg"
          onClick={() => {
            // Handle join now action
            console.log("Join Now clicked")
          }}
        >
          Join Now
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>

      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16"></div>
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full translate-y-12 -translate-x-12"></div>
    </Card>
  )
}
