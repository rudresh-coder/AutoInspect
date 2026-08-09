export default function EvidenceViewer({ result, imageUrl }) {
  if (!result) return null

  const {
    filename,
    width,
    height,
    file_size,
    analysis,
  } = result

  const hasPlate = analysis?.plate_detected === true
  const confidence = analysis?.plate_confidence

  const confidencePercent =
    typeof confidence === 'number'
      ? confidence * 100
      : null

  return (
    <section className="evidence-panel">
      <div className="section-heading">
        <span>02 / IMAGE EVIDENCE</span>
        <span className="section-line" />
        <span className="section-meta">VISION VIEWPORT</span>
      </div>

      <div className="evidence-shell">

        {/* IMAGE INFORMATION */}
        <div className="evidence-toolbar">
          <div>
            <span className="evidence-label">SOURCE</span>
            <span className="evidence-value">
              {filename}
            </span>
          </div>

          <div>
            <span className="evidence-label">RESOLUTION</span>
            <span className="evidence-value">
              {width} × {height}
            </span>
          </div>

          <div>
            <span className="evidence-label">SIZE</span>
            <span className="evidence-value">
              {file_size
                ? `${(file_size / 1024).toFixed(1)} KB`
                : '—'}
            </span>
          </div>
        </div>

        {/* IMAGE VIEWPORT */}
        <div className="evidence-viewport">

          <div className="viewport-grid" />

          <div className="viewport-corner corner-tl" />
          <div className="viewport-corner corner-tr" />
          <div className="viewport-corner corner-bl" />
          <div className="viewport-corner corner-br" />

          {/* Status */}
          <div className="viewport-status">
            <span className="status-dot" />
            IMAGE ANALYSIS COMPLETE
          </div>

          <div className="viewport-index">
            FRAME / 01
          </div>

          {/* Actual uploaded image */}
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={`Vehicle inspection evidence - ${filename}`}
              className="evidence-image"
            />
          ) : (
            <div className="evidence-placeholder">
              <span>IMAGE EVIDENCE</span>
              <small>
                {width} × {height}
              </small>
            </div>
          )}

          {/* Scan line */}
          <div className="viewport-scan-line" />

          {/* Detection status */}
          {hasPlate && (
            <div className="detection-status">
              <span className="detection-tag">
                PLATE CANDIDATE
              </span>

              {confidencePercent !== null && (
                <span className="detection-confidence">
                  OCR {confidencePercent.toFixed(1)}%
                </span>
              )}
            </div>
          )}

        </div>

        {/* FOOTER */}
        <div className="evidence-footer">

          <div>
            <span className="evidence-label">
              ANALYSIS MODE
            </span>

            <span className="evidence-value">
              COMPUTER VISION / OCR
            </span>
          </div>

          <div>
            <span className="evidence-label">
              FRAME STATUS
            </span>

            <span className="evidence-value">
              VERIFIED
            </span>
          </div>

          <div className="evidence-coordinate">
            X 0000 &nbsp; Y 0000
          </div>

        </div>

      </div>
    </section>
  )
}