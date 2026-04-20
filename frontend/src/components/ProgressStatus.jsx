export default function ProgressStatus({ phase, labels }) {
  if (!phase || !labels) return null

  const transitionMap = {
    uploading: 'width 1s ease-out',
    processing: 'width 4s ease-in-out',
    done: 'width 0.3s',
  }

  const label =
    phase === 'uploading' ? labels.uploading
    : phase === 'processing' ? labels.processing
    : null

  const valueMap = { uploading: 45, processing: 90, done: 100 }
  const value = valueMap[phase] ?? 0

  return (
    <div className="progress-status" role="status" aria-live="polite">
      <div
        className="progress-bar-track"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="progress-bar-fill"
          style={{
            width: `${value}%`,
            transition: transitionMap[phase] ?? 'none',
          }}
        />
      </div>
      {label && <p className="progress-label">{label}</p>}
    </div>
  )
}
