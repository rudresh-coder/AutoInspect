import { useCallback, useEffect, useRef, useState } from 'react'
import { getImageStatus, uploadImage } from '../api/images'

export function useImageProcessing() {
  const [status, setStatus] = useState('idle')
  const [processingId, setProcessingId] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const pollingRef = useRef(null)
  const latestRequestIdRef = useRef(0)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearTimeout(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const pollStatus = useCallback(
    async (id, requestId) => {
      try {
        const data = await getImageStatus(id)

        // Ignore stale responses from older uploads
        if (latestRequestIdRef.current !== requestId) {
          return
        }

        setResult(data)
        setStatus(data.status)

        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling()
          return
        }

        pollingRef.current = setTimeout(() => {
          pollStatus(id, requestId)
        }, 1500)
      } catch (err) {
        if (latestRequestIdRef.current !== requestId) {
          return
        }

        console.error(err)
        setError('Unable to retrieve processing status.')
        setStatus('failed')
        stopPolling()
      }
    },
    [stopPolling]
  )

  const startPolling = useCallback(
    (id) => {
      stopPolling()

      const requestId = Date.now()
      latestRequestIdRef.current = requestId

      setStatus('pending')
      pollStatus(id, requestId)
    },
    [pollStatus, stopPolling]
  )

  const processImage = useCallback(
    async (file) => {
      try {
        stopPolling()
        setError(null)
        setResult(null)
        setProcessingId(null)
        setStatus('uploading')

        const data = await uploadImage(file)

        setProcessingId(data.processing_id)
        setStatus(data.status)

        startPolling(data.processing_id)
      } catch (err) {
        console.error(err)

        const message =
          err.response?.data?.detail?.message ||
          err.response?.data?.detail ||
          'Unable to upload image.'

        setError(message)
        setStatus('failed')
        stopPolling()
      }
    },
    [startPolling, stopPolling]
  )

useEffect(() => {
  return () => stopPolling()
}, [stopPolling])

const resetProcessing = useCallback(() => {
  stopPolling()
  setStatus('idle')
  setProcessingId(null)
  setResult(null)
  setError(null)
}, [stopPolling])

return {
  status,
  processingId,
  result,
  error,
  processImage,
  resetProcessing,
}
}