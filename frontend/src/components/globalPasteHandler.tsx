import { useEffect, useRef, useState } from 'react'
import { useRouter } from '@tanstack/react-router'
import { createUrl } from '#/server-fns/urls'

function isEditableTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false
  return (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  )
}

function parseHttpUrl(value: string) {
  try {
    const url = new URL(value.trim())
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
    return url.toString()
  } catch {
    return null
  }
}

function getClipboardFiles(dataTransfer: DataTransfer | null) {
  if (!dataTransfer) return []

  return Array.from(dataTransfer.files).filter(
    (file) =>
      file.type.startsWith('image/') ||
      file.type.startsWith('video/') ||
      file.type === 'application/pdf'
  )
}

async function describeUploadFailure(res: Response) {
  try {
    const body = (await res.json()) as { detail?: unknown; message?: unknown }
    const detail = body.detail ?? body.message
    if (typeof detail === 'string') return detail
  } catch {
    // response body wasn't JSON, fall through to the status-based message
  }
  return `upload failed (${res.status})`
}

function describePasteError(error: unknown) {
  if (error instanceof TypeError) {
    // fetch throws a TypeError for network-level failures (offline, DNS, CORS)
    return 'Could not reach the server. Check your connection.'
  }
  if (error instanceof Error && error.message) {
    return `Could not add reference: ${error.message}`
  }
  return 'Could not add reference'
}

export function GlobalPasteHandler() {
  const router = useRouter()
  const [status, setStatus] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const busyRef = useRef(false)

  function clearPendingTimer() {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }

  // `autoDismissMs: null` keeps the message visible until the next call to
  // showStatus replaces it — used for in-progress states so they persist
  // until the request actually settles instead of a fixed timer.
  function showStatus(message: string, autoDismissMs: number | null = 2400) {
    clearPendingTimer()
    setStatus(message)
    if (autoDismissMs !== null) {
      timerRef.current = setTimeout(() => setStatus(null), autoDismissMs)
    }
  }

  useEffect(() => {
    async function onPaste(event: ClipboardEvent) {
      if (isEditableTarget(event.target)) return

      const files = getClipboardFiles(event.clipboardData)
      const text = event.clipboardData?.getData('text/plain')
      const url = text ? parseHttpUrl(text) : null
      if (files.length === 0 && !url) return

      event.preventDefault()

      if (busyRef.current) {
        showStatus('Already uploading...')
        return
      }

      busyRef.current = true
      try {
        if (files.length > 0) {
          showStatus(
            files.length === 1
              ? 'Uploading file...'
              : `Uploading ${files.length} files...`,
            null
          )

          let uploadedCount = 0
          let firstFailure: string | null = null

          for (const file of files) {
            try {
              const form = new FormData()
              form.append('file', file, file.name)
              const res = await fetch('/api/upload', {
                method: 'POST',
                body: form,
              })
              if (!res.ok) throw new Error(await describeUploadFailure(res))
              uploadedCount += 1
            } catch (error) {
              console.error('File upload failed', error)
              firstFailure ??=
                error instanceof Error ? error.message : 'upload failed'
            }
          }

          if (uploadedCount > 0) {
            await router.invalidate()
          }

          if (firstFailure) {
            showStatus(
              uploadedCount > 0
                ? `${uploadedCount} of ${files.length} files added, ${firstFailure}`
                : `Could not add reference: ${firstFailure}`
            )
          } else {
            showStatus(
              uploadedCount === 1 ? 'File added' : `${uploadedCount} files added`
            )
          }
          return
        }

        if (!url) return

        showStatus('Adding reference...', null)
        await createUrl({ data: { originalUrl: url } })
        await router.invalidate()
        showStatus('Reference added')
      } catch (error) {
        console.error('Paste failed', error)
        showStatus(describePasteError(error))
      } finally {
        busyRef.current = false
      }
    }

    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [router])

  useEffect(() => {
    return () => clearPendingTimer()
  }, [])

  if (!status) return null

  return (
    <div className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md border bg-popover px-3 py-2 text-sm text-popover-foreground shadow-sm">
      {status}
    </div>
  )
}
