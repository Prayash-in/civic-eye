import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { createReport } from '../api'
import Icon, { ISSUE_ICONS } from '../components/icons'
import ReportMap from '../components/ReportMap'
import { IssueBadge, SeverityBadge } from '../components/Badge'
import Alert from '../components/Alert'

const STEPS = [
  { n: 1, label: 'Capture' },
  { n: 2, label: 'Describe' },
  { n: 3, label: 'Locate' },
  { n: 4, label: 'Review' },
  { n: 5, label: 'Complete' },
]

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
const MAX_SIZE = 10 * 1024 * 1024
const MAX_DESC = 600

const ANALYSIS_STAGES = [
  { label: 'Image uploaded', icon: 'camera' },
  { label: 'AI analyzing image', icon: 'sparkle' },
  { label: 'Structuring civic issue', icon: 'list' },
  { label: 'Saving report', icon: 'check' },
]

function formatSize(bytes) {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${Math.max(1, Math.round(bytes / 1024))} KB`
}

export default function ReportPage() {
  const [step, setStep] = useState(1)
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState('')
  const [fileName, setFileName] = useState('')
  const [fileSize, setFileSize] = useState(0)
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [coords, setCoords] = useState({ lat: '', lng: '' })
  const [locationStatus, setLocationStatus] = useState('none')
  const [locationSource, setLocationSource] = useState('none') // 'gps' | 'map' | 'manual' | 'none'
  const [geoError, setGeoError] = useState('')
  const [phase, setPhase] = useState('wizard')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [analysisStage, setAnalysisStage] = useState(0)
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef(null)
  const stageTimerRef = useRef(null)
  const previewRef = useRef('')

  const clearStageTimer = useCallback(() => {
    if (stageTimerRef.current) {
      clearInterval(stageTimerRef.current)
      stageTimerRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      clearStageTimer()
      if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    }
  }, [clearStageTimer])

  function acceptFile(file) {
    if (!file) return
    if (!ACCEPTED.includes(file.type)) {
      setError('Unsupported file type. Please use JPG, PNG, or WEBP.')
      return
    }
    if (file.size > MAX_SIZE) {
      setError('Image is too large (max 10 MB).')
      return
    }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    const url = URL.createObjectURL(file)
    previewRef.current = url
    setImage(file)
    setPreview(url)
    setFileName(file.name)
    setFileSize(file.size)
    setError('')
  }

  function onFileChange(event) {
    acceptFile(event.target.files?.[0])
    event.target.value = ''
  }

  function onDrop(event) {
    event.preventDefault()
    setDragging(false)
    acceptFile(event.dataTransfer.files?.[0])
  }

  useEffect(() => {
    if (step !== 1) return
    function onPaste(event) {
      const items = event.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type && item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            acceptFile(file)
            return
          }
        }
      }
    }
    document.addEventListener('paste', onPaste)
    return () => document.removeEventListener('paste', onPaste)
  }, [step])

  function useMyLocation() {
    setGeoError('')
    if (!navigator.geolocation) {
      setLocationStatus('unavailable')
      setLocationSource('none')
      setGeoError('Browser geolocation is not available. You can pick a location on the map or enter coordinates manually.')
      return
    }
    setLocationStatus('locating')
    setLocationSource('none')
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude
        const lng = position.coords.longitude
        // Never override with Guwahati defaults — use exact GPS coordinates
        console.log('[Civic Eye] GPS coordinates received:', `latitude=${lat}, longitude=${lng}`, `accuracy=${position.coords.accuracy}m`)
        setCoords({
          lat: lat.toFixed(6),
          lng: lng.toFixed(6),
        })
        setLocationStatus('detected')
        setLocationSource('gps')
        setGeoError('')
      },
      (error) => {
        setLocationStatus('unavailable')
        setLocationSource('none')
        if (error.code === 1) {
          // PERMISSION_DENIED
          setGeoError('Location permission was denied. You can select your location on the map or enter coordinates manually.')
        } else if (error.code === 2) {
          setGeoError('Location unavailable (position unavailable). You can still submit without it or pick a spot on the map.')
        } else if (error.code === 3) {
          setGeoError('Location request timed out. Try again or pick a spot on the map.')
        } else {
          setGeoError('Location unavailable. You can still submit without it or pick a spot on the map.')
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    )
  }

  function onPickLocation(lat, lng) {
    console.log('[Civic Eye] Map-selected location:', `latitude=${lat}, longitude=${lng}`)
    setCoords({ lat: lat.toFixed(6), lng: lng.toFixed(6) })
    setLocationStatus('selected')
    setLocationSource('map')
    setGeoError('')
  }

  function onManualCoord(field, value) {
    setCoords((prev) => {
      const next = { ...prev, [field]: value }
      if (next.lat !== '' && next.lng !== '') {
        setLocationStatus('selected')
        setLocationSource('manual')
      } else if (next.lat === '' && next.lng === '') {
        setLocationStatus('none')
        setLocationSource('none')
      } else {
        // partial — treat as manual but not yet complete
        setLocationSource('manual')
      }
      return next
    })
  }

  function validateStep() {
    if (step === 1 && !image) {
      setError('Please add a photo of the issue.')
      return false
    }
    if (step === 2 && !description.trim()) {
      setError('Please describe what is happening.')
      return false
    }
    setError('')
    return true
  }

  function goNext() {
    if (!validateStep()) return
    setStep((s) => s + 1)
  }

  function goBack() {
    setError('')
    setStep((s) => Math.max(1, s - 1))
  }

  async function submit() {
    if (!image || !description.trim()) return

    const formData = new FormData()
    formData.append('image', image)
    formData.append('description', description.trim())
    if (category.trim()) formData.append('category', category.trim())
    if (coords.lat !== '' && coords.lng !== '') {
      formData.append('latitude', String(coords.lat))
      formData.append('longitude', String(coords.lng))
    }

    setError('')
    setPhase('analyzing')
    setAnalysisStage(0)
    clearStageTimer()
    stageTimerRef.current = setInterval(() => {
      setAnalysisStage((s) => (s < ANALYSIS_STAGES.length - 1 ? s + 1 : s))
    }, 1800)

    try {
      const report = await createReport(formData)
      clearStageTimer()
      setResult(report)
      setPhase('result')
    } catch (err) {
      clearStageTimer()
      setError(err.message)
      setPhase('wizard')
    }
  }

  function reset() {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = ''
    setImage(null)
    setPreview('')
    setFileName('')
    setFileSize(0)
    setDescription('')
    setCategory('')
    setCoords({ lat: '', lng: '' })
    setLocationStatus('none')
    setLocationSource('none')
    setGeoError('')
    setError('')
    setResult(null)
    setPhase('wizard')
    setStep(1)
  }

  if (phase === 'analyzing') {
    return (
      <div className="analyzing-page">
        <div className="analyzing-card">
          <h2>Analyzing your report</h2>
          <p className="analyzing-sub">
            Running local AI classification. This can take up to a minute.
          </p>
          <div className="analyzing-stages">
            {ANALYSIS_STAGES.map((stage, i) => {
              const done = i < analysisStage
              const current = i === analysisStage
              return (
                <div
                  key={stage.label}
                  className={`analyzing-stage${done ? ' done' : ''}${current ? ' current' : ''}`}
                >
                  <span className="analyzing-stage-icon">
                    {done ? (
                      <Icon name="check" size={16} />
                    ) : (
                      <Icon name={stage.icon} size={16} />
                    )}
                  </span>
                  <span className="analyzing-stage-label">{stage.label}</span>
                  {current && <span className="analyzing-stage-spinner" aria-hidden="true" />}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  if (phase === 'result' && result) {
    const failed = result.analysis_status === 'failed'
    const pending = result.analysis_status === 'pending'
    const hasVerdict = !failed && (result.issue_type || result.severity != null)
    const reportId = `CIV-${String(result.id).padStart(4, '0')}`
    const confidence = Math.round((result.confidence || 0) * 100)

    return (
      <div className="result-page">
        <div className="result-hero">
          <span className="result-hero-icon">
            <Icon name="check" size={28} />
          </span>
          <h1>Report Submitted</h1>
          <p className="result-id">
            Report ID: <strong>{reportId}</strong>
          </p>
        </div>

        {failed ? (
          <Alert variant="warning" title="AI analysis is temporarily unavailable. Please try again.">
            Your report was saved and can still be reviewed.
          </Alert>
        ) : hasVerdict ? (
          <div className="verdict-card">
            <div className="verdict-head">
              <span className="verdict-kicker">
                <Icon name="sparkle" size={15} /> Civic Eye analysis
              </span>
              <IssueBadge issueType={result.issue_type} />
            </div>

            <div className="verdict-main">
              <span className={`verdict-glyph severity-${result.severity || 'unknown'}`}>
                <Icon name={ISSUE_ICONS[result.issue_type] || 'report'} size={34} />
              </span>
              <div className="verdict-issue">
                <span className="verdict-label">Issue</span>
                <span className="verdict-value">{result.issue_type || 'Unclassified'}</span>
                {result.severity != null && (
                  <span className="verdict-confidence">
                    {confidence}% AI confidence
                  </span>
                )}
              </div>
              <div className="verdict-severity">
                <span className="verdict-label">Severity</span>
                <SeverityBadge severity={result.severity} />
                {result.severity != null && (
                  <span className="confidence-meter" aria-hidden="true">
                    <span style={{ width: `${confidence}%` }} />
                  </span>
                )}
              </div>
            </div>

            {result.explanation && (
              <div className="verdict-why">
                <span className="verdict-label">Why</span>
                <p>“{result.explanation}”</p>
              </div>
            )}

            <div className="verdict-meta">
              <span>
                <Icon name="pin" size={14} />
                {result.latitude != null && result.longitude != null
                  ? `${result.latitude.toFixed(4)}, ${result.longitude.toFixed(4)}`
                  : 'Location not provided'}
              </span>
              <span>
                <Icon name="clock" size={14} />
                {new Date(result.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        ) : pending ? (
          <Alert variant="info" title="Analysis is still running.">
            Your report was saved. Check back shortly for the AI result.
          </Alert>
        ) : null}

        <div className="result-actions">
          <Link to={`/reports/${result.id}`} className="btn btn-primary btn-lg">
            View Report
          </Link>
          {failed && (
            <button type="button" className="btn btn-secondary btn-lg" onClick={submit}>
              Try Again
            </button>
          )}
          <button type="button" className="btn btn-ghost btn-lg" onClick={reset}>
            Report Another Issue
          </button>
        </div>
      </div>
    )
  }

  const mapLat = coords.lat !== '' ? Number(coords.lat) : null
  const mapLng = coords.lng !== '' ? Number(coords.lng) : null
  const hasCoords = mapLat != null && mapLng != null && !Number.isNaN(mapLat) && !Number.isNaN(mapLng)

  const locationSourceLabel =
    locationSource === 'gps'
      ? 'GPS location'
      : locationSource === 'map'
        ? 'Map-selected location'
        : locationSource === 'manual'
          ? 'Manual coordinates'
          : ''

  const locationStatusText =
    locationStatus === 'detected'
      ? 'Location detected — GPS location'
      : locationStatus === 'selected'
        ? locationSourceLabel || 'Location selected'
        : locationStatus === 'locating'
          ? 'Detecting location…'
          : locationSourceLabel

  return (
    <div className="report-page">
      <div className="stepper" aria-label="Report progress">
        {STEPS.map((s) => {
          const state = s.n === step ? 'current' : s.n < step ? 'done' : 'todo'
          const isComplete = s.n === 5 && phase === 'result'
          return (
            <div
              key={s.n}
              className={`stepper-step ${state}${isComplete ? ' done' : ''}`}
              aria-current={s.n === step ? 'step' : undefined}
            >
              <span className="stepper-dot">
                {state === 'done' || isComplete ? (
                  <Icon name="check" size={14} />
                ) : (
                  <span className="stepper-num">0{s.n}</span>
                )}
              </span>
              <span className="stepper-label">{s.label}</span>
            </div>
          )
        })}
      </div>

      <div className="wizard-card">
        {step === 1 && (
          <div className="wizard-step">
            <h2>
              <span className="step-heading-num">01</span> Capture the issue
            </h2>
            <p className="step-hint">
              Add a photo of the problem. JPG, PNG, or WEBP, up to 10 MB.
            </p>

            <div
              className={`dropzone${dragging ? ' dragging' : ''}${preview ? ' has-image' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  fileInputRef.current?.click()
                }
              }}
              aria-label="Upload an image of the issue"
            >
              {preview ? (
                <>
                  <img src={preview} alt="Preview of the reported issue" className="dropzone-preview" />
                  <div className="dropzone-meta">
                    <span className="dropzone-file">
                      <Icon name="image" size={16} />
                      {fileName}
                    </span>
                    <span className="dropzone-size">{formatSize(fileSize)}</span>
                  </div>
                  <span className="dropzone-replace">
                    <Icon name="camera" size={14} /> Replace
                  </span>
                </>
              ) : (
                <div className="dropzone-empty">
                  <span className="dropzone-icon">
                    <Icon name="camera" size={26} />
                  </span>
                  <strong>Click to upload</strong>
                  <span>or drag &amp; drop, or paste an image</span>
                  <span className="dropzone-capture">Use camera on mobile</span>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                capture="environment"
                onChange={onFileChange}
                hidden
              />
            </div>

            {preview && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={(e) => {
                  e.stopPropagation()
                  if (previewRef.current) URL.revokeObjectURL(previewRef.current)
                  previewRef.current = ''
                  setImage(null)
                  setPreview('')
                  setFileName('')
                  setFileSize(0)
                }}
              >
                <Icon name="close" size={14} /> Remove image
              </button>
            )}

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="wizard-actions">
              <button type="button" className="btn btn-primary" onClick={goNext} disabled={!image}>
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-step">
            <h2>
              <span className="step-heading-num">02</span> Describe the problem
            </h2>

            <label className="field-label" htmlFor="report-description">
              What is happening?
            </label>
            <textarea
              id="report-description"
              className="description-input"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={5}
              maxLength={MAX_DESC}
              placeholder="e.g. A deep pothole on the main road near the market is causing traffic to swerve and damaging vehicles."
            />
            <div className="char-counter" aria-live="polite">
              {description.length}/{MAX_DESC}
            </div>

            <label className="field-label" htmlFor="report-category">
              Category <span className="optional">(optional)</span>
            </label>
            <input
              id="report-category"
              className="text-input"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              placeholder="e.g. road, sanitation, lighting"
            />

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={goBack}>
                <Icon name="chevron-left" size={16} /> Back
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={goNext}
                disabled={!description.trim()}
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="wizard-step">
            <h2>
              <span className="step-heading-num">03</span> Set the location
            </h2>
            <p className="step-hint">Optional — but it helps authorities respond faster.</p>

            <div className="location-actions">
              <button
                type="button"
                className={`btn ${hasCoords ? 'btn-secondary' : 'btn-primary'}`}
                onClick={useMyLocation}
                disabled={locationStatus === 'locating'}
              >
                <Icon name="gps" size={16} />
                {locationStatus === 'locating' ? 'Detecting…' : 'Use my location'}
              </button>
              <span className="location-status">
                {locationStatusText && (
                  <>
                    <Icon name="pin" size={14} /> {locationStatusText}
                  </>
                )}
              </span>
            </div>

            {geoError && <Alert variant="warning">{geoError}</Alert>}

            {hasCoords && (
              <div className="coords-display" style={{ margin: '10px 0', padding: '10px 14px', background: 'var(--surface-muted)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <Icon name="pin" size={14} /> Current Location
                </div>
                <div style={{ fontSize: '0.85rem' }}>
                  Latitude: {coords.lat}<br />
                  Longitude: {coords.lng}
                </div>
                {locationSourceLabel && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Source: {locationSourceLabel}
                  </div>
                )}
                {locationSource === 'gps' && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--success)', fontWeight: 600, marginTop: '2px' }}>
                    Location detected successfully.
                  </div>
                )}
              </div>
            )}

            <div className="coords-row">
              <div className="coords-field">
                <label className="field-label" htmlFor="lat-input">
                  Latitude
                </label>
                <input
                  id="lat-input"
                  className="text-input"
                  type="number"
                  step="any"
                  placeholder="e.g. 26.430000 (Mangaldai)"
                  value={coords.lat}
                  onChange={(event) => onManualCoord('lat', event.target.value)}
                />
              </div>
              <div className="coords-field">
                <label className="field-label" htmlFor="lng-input">
                  Longitude
                </label>
                <input
                  id="lng-input"
                  className="text-input"
                  type="number"
                  step="any"
                  placeholder="e.g. 92.040000 (Mangaldai)"
                  value={coords.lng}
                  onChange={(event) => onManualCoord('lng', event.target.value)}
                />
              </div>
            </div>

            <p className="step-hint">Or click anywhere on the map to set the location.</p>
            <ReportMap
              latitude={mapLat}
              longitude={mapLng}
              severity={undefined}
              onPick={onPickLocation}
            />

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={goBack}>
                <Icon name="chevron-left" size={16} /> Back
              </button>
              <button type="button" className="btn btn-primary" onClick={goNext}>
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="wizard-step">
            <h2>
              <span className="step-heading-num">04</span> Review &amp; submit
            </h2>

            <div className="review-card">
              {preview ? (
                <img src={preview} alt="Report preview" className="review-image" />
              ) : (
                <div className="review-image review-image-empty">
                  <Icon name="image" size={24} />
                </div>
              )}
              <div className="review-details">
                <div className="review-row">
                  <span className="review-label">Description</span>
                  <span className="review-value">{description}</span>
                </div>
                <div className="review-row">
                  <span className="review-label">Location</span>
                  <span className="review-value">
                    {hasCoords ? `${coords.lat}, ${coords.lng}` : 'Not provided'}
                  </span>
                </div>
                {category.trim() && (
                  <div className="review-row">
                    <span className="review-label">Category</span>
                    <span className="review-value">{category}</span>
                  </div>
                )}
              </div>
            </div>

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={goBack}>
                <Icon name="chevron-left" size={16} /> Back
              </button>
              <button type="button" className="btn btn-primary btn-lg" onClick={submit}>
                <Icon name="check" size={16} /> Submit Report
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}