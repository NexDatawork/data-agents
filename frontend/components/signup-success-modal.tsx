"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle, ArrowRight } from "lucide-react"

interface SignupSuccessModalProps {
  isOpen: boolean
  onRedirect: () => void
}

export function SignupSuccessModal({ isOpen, onRedirect }: SignupSuccessModalProps) {
  const [countdown, setCountdown] = useState(20)

  useEffect(() => {
    if (!isOpen) return

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          onRedirect()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isOpen, onRedirect])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8 text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-gray-900">Account Created Successfully!</h2>
            <p className="text-gray-600">
              Welcome to NexDatawork! You're ready to start exploring NexDatawork data agent!
            </p>
          </div>

          <div className="space-y-4">
            <p className="text-sm text-gray-500">Redirecting to Login in {countdown} seconds...</p>

            <Button
              onClick={onRedirect}
              className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90"
            >
              Go to Login Now
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
