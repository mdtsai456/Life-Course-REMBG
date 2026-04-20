import { useEffect, useRef, useState } from 'react'
import { removeBackground } from '../services/api'
import { IMAGE_ACCEPT_STRING } from '../constants'
import { validateImageFile } from '../utils/validateImageFile'
import { revokeResultUrl } from '../utils/revokeResultUrl'
import useAsyncSubmit from '../hooks/useAsyncSubmit'
import { useDerivedObjectUrl, useManagedObjectUrl } from '../hooks/useObjectUrl'
import LoadingButton from './LoadingButton'
import ProgressStatus from './ProgressStatus'

const UPLOAD_PROGRESS_LABELS = { uploading: '上傳圖片中...', processing: '移除背景中...' }

export default function ImageUploader({ visible = true }) {
  const [file, setFile] = useState(null)
  const originalUrl = useDerivedObjectUrl(file)
  const [resultUrl, setResultUrl] = useManagedObjectUrl()
  const [isDragOver, setIsDragOver] = useState(false)

  const { execute, loading, error, setError, phase, reset } = useAsyncSubmit()
  const dragCounterRef = useRef(0)
  const applyFileRef = useRef(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => reset()
  }, [reset])

  // Abort in-flight requests and reset loading state when tab becomes hidden
  useEffect(() => {
    if (visible) return
    reset()
    dragCounterRef.current = 0
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional cleanup on visibility change
    setIsDragOver(false)
  }, [visible, reset])

  function applyFile(selected) {
    if (loading) return
    setError('')
    setResultUrl(null)

    if (!selected) {
      setFile(null)
      return
    }

    const validation = validateImageFile(selected)
    if (validation) {
      setError(validation.error)
      setFile(null)
      return
    }

    setFile(selected)
  }

  useEffect(() => { applyFileRef.current = applyFile })

  function handleFileChange(e) {
    applyFile(e.target.files?.[0] ?? null)
  }

  function handleDragLeave() {
    dragCounterRef.current = Math.max(0, dragCounterRef.current - 1)
    if (dragCounterRef.current === 0) setIsDragOver(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    dragCounterRef.current = 0
    setIsDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) applyFile(dropped)
  }

  // Paste listener — only active when this tab is visible
  useEffect(() => {
    if (!visible) return
    function handlePaste(e) {
      const items = e.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.kind === 'file') {
          e.preventDefault()
          applyFileRef.current(item.getAsFile())
          return
        }
      }
    }
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [visible])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setResultUrl(null)

    execute(
      (signal) => removeBackground(file, signal),
      {
        onSuccess: ({ url }) => setResultUrl(url),
        onAbortCleanup: revokeResultUrl,
      },
    )
  }

  return (
    <div
      className={`uploader${isDragOver ? ' drag-over' : ''}`}
      onDragEnter={(e) => {
        e.preventDefault()
        if (!Array.from(e.dataTransfer?.types ?? []).includes('Files')) return
        dragCounterRef.current++
        setIsDragOver(true)
      }}
      onDragOver={(e) => {
        if (Array.from(e.dataTransfer?.types ?? []).includes('Files')) e.preventDefault()
      }}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <form className="upload-form" onSubmit={handleSubmit}>
        <label htmlFor="image-upload" className="file-label">
          <input
            id="image-upload"
            type="file"
            accept={IMAGE_ACCEPT_STRING}
            onChange={handleFileChange}
            disabled={loading}
            className="file-input"
          />
          <span className="file-button">選擇圖片</span>
          <span className="file-name">
            {file ? file.name : '未選擇檔案'}
          </span>
        </label>
        <LoadingButton
          type="submit"
          disabled={!file || loading}
          className="submit-button"
          loading={loading}
          loadingText="處理中…"
        >
          移除背景
        </LoadingButton>
        <ProgressStatus phase={phase} labels={UPLOAD_PROGRESS_LABELS} />
      </form>

      {error && <p className="error-message" role="alert">{error}</p>}

      {!file && !loading && !error && (
        <p className="drop-hint">可拖曳圖片到此，或直接貼上剪貼簿圖片</p>
      )}

      {(originalUrl || resultUrl) && (
        <div className="preview-grid">
          {originalUrl && (
            <div className="preview-card">
              <h3 className="preview-title">原圖</h3>
              <img src={originalUrl} alt="原圖" className="preview-image" />
            </div>
          )}
          {resultUrl && (
            <div className="preview-card">
              <h3 className="preview-title">去背結果</h3>
              <img src={resultUrl} alt="去背結果" className="preview-image checkerboard" />
              <a
                href={resultUrl}
                download={file ? file.name.replace(/(\.[^.]+)$/, '_no_bg$1').replace(/\.[^.]+$/, '.png') : 'background-removed.png'}
                className="download-button"
              >
                下載
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
