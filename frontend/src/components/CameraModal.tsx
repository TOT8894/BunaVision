import { useRef, useState, useCallback, useEffect } from 'react'
import { Camera, SwitchCamera, X } from 'lucide-react'

interface CameraModalProps {
  onCapture: (file: File) => void
  onClose: () => void
}

export function CameraModal({ onCapture, onClose }: CameraModalProps) {
  const [cameraFacing, setCameraFacing] = useState<'environment' | 'user'>('environment')
  const [cameraError, setCameraError] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [])

  const startCamera = useCallback(
    async (facing: 'environment' | 'user') => {
      setCameraError(null)
      stopStream()
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: facing, width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        })
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      } catch {
        setCameraError(
          'Unable to access camera. Please allow camera permissions or select a photo file.',
        )
      }
    },
    [stopStream],
  )

  useEffect(() => {
    startCamera(cameraFacing)
    return () => {
      stopStream()
    }
  }, [cameraFacing, startCamera, stopStream])

  const toggleFacing = () => {
    const next = cameraFacing === 'environment' ? 'user' : 'environment'
    setCameraFacing(next)
    startCamera(next)
  }

  const capturePhoto = () => {
    if (!videoRef.current) return
    const video = videoRef.current
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const file = new File([blob], `camera_sample_${Date.now()}.jpg`, {
              type: 'image/jpeg',
            })
            stopStream()
            onCapture(file)
          }
        },
        'image/jpeg',
        0.92,
      )
    }
  }

  const handleClose = () => {
    stopStream()
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-[#231F1C] border border-[#382E26] rounded-3xl max-w-lg w-full p-6 text-[#F9F7F2] space-y-4 shadow-2xl relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Camera className="w-5 h-5 text-[#8BA470]" />
            <h3 className="font-bold text-lg font-serif">Capture Raw Green Bean Sample</h3>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="p-1.5 rounded-lg hover:bg-stone-800 text-stone-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {cameraError ? (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs space-y-2">
            <p>{cameraError}</p>
            <button
              type="button"
              onClick={() => startCamera(cameraFacing)}
              className="px-3 py-1.5 rounded-lg bg-red-600 text-white font-semibold cursor-pointer"
            >
              Retry Camera
            </button>
          </div>
        ) : (
          <div className="relative rounded-2xl overflow-hidden aspect-4/3 bg-black border border-stone-800">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-4 border border-dashed border-white/40 rounded-xl pointer-events-none flex items-center justify-center">
              <span className="text-xs uppercase font-bold text-white bg-black/70 px-3 py-1 rounded-md tracking-wider">
                Spread raw green beans flat in tray
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={toggleFacing}
            className="px-3.5 py-2 rounded-xl border border-stone-700 bg-stone-800 hover:bg-stone-700 text-xs font-semibold flex items-center space-x-1.5 cursor-pointer transition-colors"
          >
            <SwitchCamera className="w-4 h-4 text-[#8BA470]" />
            <span>Flip Lens</span>
          </button>
          <button
            type="button"
            onClick={capturePhoto}
            disabled={Boolean(cameraError)}
            className="px-6 py-2.5 rounded-xl bg-[#8BA470] hover:bg-[#78935c] text-white font-bold text-sm flex items-center space-x-2 shadow-lg hover:scale-105 transition-all cursor-pointer disabled:opacity-50"
          >
            <Camera className="w-4 h-4" />
            <span>Snap Photograph</span>
          </button>
        </div>
      </div>
    </div>
  )
}
