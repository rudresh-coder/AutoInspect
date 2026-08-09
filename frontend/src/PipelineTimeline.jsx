import { useEffect, useState } from 'react'

const stages = [
  {
    id: '01',
    label: 'IMAGE INGESTION',
    detail: 'File received',
  },
  {
    id: '02',
    label: 'QUALITY ANALYSIS',
    detail: 'Sharpness / exposure / contrast',
  },
  {
    id: '03',
    label: 'PLATE + OCR',
    detail: 'Registration analysis',
  },
  {
    id: '04',
    label: 'DUPLICATE ANALYSIS',
    detail: 'SHA-256 + perceptual hash',
  },
  {
    id: '05',
    label: 'INSPECTION REPORT',
    detail: 'Results assembled',
  },
]

function getStageState(status, activeStage, index) {
  if (status === 'uploading') {
    return index === 0 ? 'active' : 'waiting'
  }

  if (status === 'pending') {
    if (index === 0) return 'complete'
    if (index === 1) return 'active'
    return 'waiting'
  }

  if (status === 'processing') {
    if (index < activeStage) return 'complete'
    if (index === activeStage) return 'active'
    return 'waiting'
  }

  if (status === 'completed') {
    return 'complete'
  }

  if (status === 'failed') {
    if (index < activeStage) return 'complete'
    if (index === activeStage) return 'failed'
    return 'waiting'
  }

  return 'waiting'
}

export default function PipelineTimeline({ status }) {
  const [processingStage, setProcessingStage] = useState(2)

  useEffect(() => {
    if (status !== 'processing') {
      return
    }

    // Once the worker starts, visually progress through
    // the analysis stages while the backend processes the image.
    const stageTimer = setTimeout(() => {
      setProcessingStage(3)
    }, 2500)

    const initialStageTimer = setTimeout(() => {
      setProcessingStage(2)
    }, 0)

    return () => {
      clearTimeout(stageTimer)
      clearTimeout(initialStageTimer)
    }
  }, [status])

  const currentStage =
    status === 'processing'
      ? processingStage
      : status === 'pending'
        ? 1
        : status === 'uploading'
          ? 0
          : status === 'completed'
            ? 4
            : 2

  return (
    <div className="pipeline-panel">
      <div className="pipeline-header">
        <div>
          <span className="pipeline-kicker">
            ANALYSIS PIPELINE
          </span>

          <strong>
            PROCESS EXECUTION
          </strong>
        </div>

        <span className="pipeline-mode">
          ASYNCHRONOUS
        </span>
      </div>

      <div className="pipeline-track">
        {stages.map((stage, index) => {
          const state = getStageState(
            status,
            currentStage,
            index
          )

          return (
            <div
              className={`pipeline-stage ${state}`}
              key={stage.id}
            >
              <div className="pipeline-node">
                {state === 'complete' ? (
                  '✓'
                ) : state === 'failed' ? (
                  '×'
                ) : (
                  stage.id
                )}
              </div>

              {index < stages.length - 1 && (
                <div
                  className={`pipeline-connector ${
                    state === 'complete'
                      ? 'complete'
                      : ''
                  }`}
                />
              )}

              <div className="pipeline-content">
                <span className="pipeline-stage-id">
                  {stage.id}
                </span>

                <strong>
                  {stage.label}
                </strong>

                <span>
                  {stage.detail}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      <div className="pipeline-status">
        <span className="pipeline-status-dot" />

        <span>
          {status === 'uploading'
            ? 'TRANSMITTING SOURCE IMAGE'
            : status === 'pending'
              ? 'AWAITING PROCESSING WORKER'
              : status === 'processing'
                ? currentStage === 2
                  ? 'PLATE + OCR ENGINE ACTIVE'
                  : currentStage === 3
                    ? 'DUPLICATE ANALYSIS ACTIVE'
                    : 'COMPUTER VISION ENGINE ACTIVE'
                : status === 'completed'
                  ? 'ANALYSIS PIPELINE COMPLETE'
                  : status === 'failed'
                    ? 'PIPELINE EXECUTION FAILED'
                    : 'PIPELINE READY'}
        </span>

        <span className="pipeline-status-line" />
      </div>
    </div>
  )
}