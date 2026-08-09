import EvidenceViewer from './components/EvidenceViewer'
import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { useImageProcessing } from './hooks/useImageProcessing'
import PipelineTimeline from './PipelineTimeline'
import './App.css'

function ProcessingState({
  label,
  detail,
  step,
  failed = false,
}) {
  return (
    <motion.div
      className={`processing-state ${failed ? 'failed' : ''}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="processing-visual">
        <div className="scan-frame">
          <span />
        </div>

        {!failed && (
          <motion.div
            className="scan-line"
            animate={{ y: [0, 110, 0] }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
      </div>

      <div className="processing-meta">
        <div className="processing-step">
          STEP {step}
        </div>

        <strong>{label}</strong>

        <span>{detail}</span>
      </div>

      <PipelineTimeline
        status={
          failed
            ? 'failed'
            : step === '01'
              ? 'uploading'
              : step === '02'
                ? 'pending'
                : 'processing'
        }
      />
    </motion.div>
  )
}

function CompletedState({ result, imageUrl }) {
  const analysis = result.analysis

  const score = analysis?.overall_score ?? 0

  const metrics = [
    {
      label: 'SHARPNESS',
      value: analysis?.blur_score,
    },
    {
      label: 'EXPOSURE',
      value: analysis?.exposure_score,
    },
    {
      label: 'CONTRAST',
      value: analysis?.contrast_score,
    },
  ]

  return (
    <motion.div
      className="completed-report"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >

      <EvidenceViewer
  result={result}
  imageUrl={imageUrl}
/>

      {/* Header */}
      <div className="report-header">
        <div>
          <div className="processing-step">
            ANALYSIS COMPLETE
          </div>

          <h2>Inspection Report</h2>
        </div>

        <div className="report-id">
          <span>PROCESSING ID</span>
          <strong>
            {result.processing_id?.slice(0, 8).toUpperCase()}
          </strong>
        </div>
      </div>

      {/* Main analysis */}
      <div className="report-main">

        {/* Score */}
        <motion.div
          className="score-panel"
          initial={{ scale: 0.96, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.4 }}
        >
          <div className="score-ring">
            <svg viewBox="0 0 120 120">
              <circle
                className="score-track"
                cx="60"
                cy="60"
                r="52"
              />

              <motion.circle
                className="score-progress"
                cx="60"
                cy="60"
                r="52"
                initial={{
                  strokeDashoffset: 327,
                }}
                animate={{
                  strokeDashoffset:
                    327 - (327 * score) / 100,
                }}
                transition={{
                  duration: 1.2,
                  ease: 'easeOut',
                  delay: 0.2,
                }}
              />
            </svg>

            <div className="score-value">
              <strong>{score.toFixed(2)}</strong>
              <span>/ 100</span>
            </div>
          </div>

          <div className="score-label">
            OVERALL QUALITY
          </div>
        </motion.div>

        {/* Metrics */}
        <div className="metrics-panel">
          <div className="panel-label">
            QUALITY COMPONENTS
          </div>

          {metrics.map((metric, index) => (
            <motion.div
              className="metric"
              key={metric.label}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                delay: 0.25 + index * 0.1,
                duration: 0.35,
              }}
            >
              <div className="metric-header">
                <span>{metric.label}</span>

                <strong>
                  {metric.value != null
                    ? metric.value.toFixed(2)
                    : '—'}
                </strong>
              </div>

              <div className="metric-track">
                <motion.div
                  className="metric-fill"
                  initial={{ width: 0 }}
                  animate={{
                    width: `${metric.value ?? 0}%`,
                  }}
                  transition={{
                    duration: 0.9,
                    delay: 0.35 + index * 0.1,
                    ease: 'easeOut',
                  }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Intelligence results */}
      <div className="intelligence-grid">

        {/* Plate */}
        <div className="intelligence-card">
          <div className="card-label">
            REGISTRATION / OCR
          </div>

          <div className="card-value">
            {analysis?.plate_detected
              ? analysis.plate_text || 'DETECTED'
              : 'NOT DETECTED'}
          </div>

          <div className="card-meta">
            {analysis?.plate_detected &&
            analysis?.plate_confidence != null
              ? `CONFIDENCE ${(analysis.plate_confidence * 100).toFixed(2)}%`
              : 'NO HIGH-CONFIDENCE REGISTRATION FOUND'}
          </div>
        </div>

        {/* Duplicate */}
<div className="intelligence-card">
  <div className="card-label">
    DUPLICATE ANALYSIS
  </div>

  <div className="card-value">
    {analysis?.exact_duplicate
      ? 'EXACT MATCH'
      : analysis?.duplicate_similarity != null &&
        analysis.duplicate_similarity >= 90
        ? 'VISUAL MATCH'
        : 'NO MATCH'}
  </div>

  <div className="card-meta">
    {analysis?.exact_duplicate
      ? 'IDENTICAL FILE CONTENT DETECTED'
      : analysis?.duplicate_similarity != null
        ? `PERCEPTUAL SIMILARITY ${analysis.duplicate_similarity.toFixed(2)}%`
        : 'NO PREVIOUS IMAGE AVAILABLE'}
  </div>
</div>
      </div>

      {/* Explanation */}
      <motion.div
        className="explanation-panel"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        <div className="panel-label">
          SYSTEM EXPLANATION
        </div>

        <p>
          {analysis?.explanation ||
            'No explanation was returned by the analysis engine.'}
        </p>
      </motion.div>

      {/* Technical metadata */}
      <div className="technical-meta">
        <span>
          FILE <strong>{result.filename}</strong>
        </span>

        <span>
          DIMENSIONS{' '}
          <strong>
            {result.width} × {result.height}
          </strong>
        </span>

        <span>
          SIZE{' '}
          <strong>
            {(result.file_size / 1024).toFixed(1)} KB
          </strong>
        </span>

        <span>
          STATUS <strong>COMPLETE</strong>
        </span>
      </div>
    </motion.div>
  )
}

function App() {
const {
  status,
  result,
  error,
  processImage,
  resetProcessing,
} = useImageProcessing()
  
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [imageUrl, setImageUrl] = useState(null)
  const resetInspection = () => {
  setSelectedFile(null)
  setImageUrl(null)
  resetProcessing()

  if (fileInputRef.current) {
    fileInputRef.current.value = ''
  }
}

const handleFile = async (file) => {
  if (!file) return

  if (!file.type.startsWith('image/')) {
    alert('Please select an image file.')
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    alert('Image must be smaller than 10 MB.')
    return
  }

  setSelectedFile(file)

  const previewUrl = URL.createObjectURL(file)
  setImageUrl(previewUrl)

  await processImage(file)
}

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)

    const file = event.dataTransfer.files?.[0]
    handleFile(file)
  }

  const handleFileInput = (event) => {
    const file = event.target.files?.[0]
    handleFile(file)
  }

  return (
    <main className="app-shell">
      {/* Navigation */}
      <nav className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <span />
            <span />
            <span />
          </div>

          <div>
            <div className="brand-name">AUTOINSPECT</div>
            <div className="brand-subtitle">VISION ANALYSIS SYSTEM</div>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          <span>SYSTEM ONLINE</span>
        </div>
      </nav>

      {/* Main hero */}
      <section className="hero-section">
        <div className="hero-grid">

          {/* Left side */}
          <motion.div
            className="hero-copy"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="eyebrow">
              <span>01</span>
              COMPUTER VISION INSPECTION
            </div>

            <h1>
              See what the
              <br />
              <span>image doesn't tell you.</span>
            </h1>

            <p className="hero-description">
              Analyze vehicle imagery for visual quality,
              registration plates, and duplicate content
              using an asynchronous computer-vision pipeline.
            </p>

            <div className="capability-row">
              <span>QUALITY</span>
              <span>OCR</span>
              <span>DUPLICATE DETECTION</span>
            </div>
          </motion.div>

          {/* Right side */}
          <motion.div
            className="inspection-panel"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.15 }}
          >
            <div className="panel-header">
              <span>IMAGE INGESTION</span>
              <span>READY</span>
            </div>

            <div
              className={`drop-zone ${isDragging ? 'dragging' : ''} ${
                selectedFile ? 'has-file' : ''
              }`}
              onDragOver={(event) => {
                event.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => {
  if (status === 'idle') {
    fileInputRef.current?.click()
  }
}}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                hidden
                onChange={handleFileInput}
              />

              {status === 'idle' && !selectedFile ? (
  <>
    <div className="inspection-frame">
      <div className="corner top-left" />
      <div className="corner top-right" />
      <div className="corner bottom-left" />
      <div className="corner bottom-right" />

      <div className="drop-icon">
        <span />
        <span />
      </div>
    </div>

    <div className="drop-content">
      <strong>
        {isDragging
          ? 'DROP IMAGE TO INSPECT'
          : 'DROP VEHICLE IMAGE'}
      </strong>

      <span>
        or select a file from your device
      </span>

      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation()
          fileInputRef.current?.click()
        }}
      >
        SELECT IMAGE
      </button>
    </div>
  </>
) : status === 'uploading' ? (
  <ProcessingState
    label="UPLOADING IMAGE"
    detail="Transmitting image to analysis engine"
    step="01"
  />
) : status === 'pending' ? (
  <ProcessingState
    label="QUEUED FOR ANALYSIS"
    detail="Waiting for image-processing worker"
    step="02"
  />
) : status === 'processing' ? (
  <ProcessingState
    label="ANALYZING IMAGE"
    detail="Computer vision pipeline is running"
    step="03"
  />
) : status === 'completed' && result ? (
  <CompletedState
  result={result}
  imageUrl={imageUrl}
/>
) : status === 'failed' ? (
  <div className="failure-state">
    <ProcessingState
      label="PROCESSING FAILED"
      detail={error || 'Something went wrong during analysis'}
      step="ERR"
      failed
    />

    <button
      type="button"
      className="retry-button"
      onClick={resetInspection}
    >
      TRY ANOTHER IMAGE
    </button>
  </div>
) : null}
            </div>

            <div className="panel-footer">
              <span>JPEG / PNG / WEBP</span>
              <span>MAX 10 MB</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Technical footer */}
      <section className="system-strip">
        <div>
          <span className="strip-label">ENGINE</span>
          <strong>IMAGE ANALYSIS</strong>
        </div>

        <div>
          <span className="strip-label">PROCESSING</span>
          <strong>ASYNCHRONOUS</strong>
        </div>

        <div>
          <span className="strip-label">DETECTION</span>
          <strong>OCR + P-HASH</strong>
        </div>

        <div>
          <span className="strip-label">STATUS</span>
          <strong className="online-text">READY</strong>
        </div>
      </section>
    </main>
  )
}

export default App