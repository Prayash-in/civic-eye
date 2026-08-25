import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getReport } from '../api'
import Icon, { ISSUE_ICONS } from '../components/icons'
import { IssueBadge, SeverityBadge, StatusBadge } from '../components/Badge'
import Loading from '../components/Loading'
import ErrorNote from '../components/ErrorNote'
import EmptyNote from '../components/EmptyNote'
import Alert from '../components/Alert'
import ReportMap from '../components/ReportMap'

function TimelineStep({ label, state, detail }) {
  return (
    <div className={`timeline-step ${state}`}>
      <span className="timeline-dot">
        {state === 'done' ? <Icon name="check" size={14} /> : <Icon name="clock" size={14} />}
      </span>
      <div>
        <span className="timeline-label">{label}</span>
        {detail && <span className="timeline-detail">{detail}</span>}
      </div>
    </div>
  )
}

export default function ReportDetail() {
  const { id } = useParams()
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    let cancelled = false
    setReport(null)
    setError('')
    setNotFound(false)

    getReport(id)
      .then((data) => {
        if (!cancelled) setReport(data)
      })
      .catch((err) => {
        if (cancelled) return
        if (/not found/i.test(err.message)) setNotFound(true)
        else setError(err.message)
      })

    return () => {
      cancelled = true
    }
  }, [id])

  if (error) {
    return (
      <section className="page">
        <ErrorNote message={error} />
        <Link to="/reports" className="btn btn-secondary">
          Back to reports
        </Link>
      </section>
    )
  }

  if (notFound) {
    return (
      <section className="page">
        <EmptyNote
          icon="search"
          message="Report not found."
          hint="It may have been removed or the link is incorrect."
        />
        <Link to="/reports" className="btn btn-primary">
          Browse reports
        </Link>
      </section>
    )
  }

  if (!report) {
    return (
      <section className="page">
        <Loading />
      </section>
    )
  }

  const failed = report.analysis_status === 'failed'
  const pending = report.analysis_status === 'pending'
  const hasCoords = report.latitude != null && report.longitude != null
  const confidence =
    report.confidence != null ? Math.round(report.confidence * 100) : null
  const reportId = `CIV-${String(report.id).padStart(4, '0')}`

  const jurisdiction = report.jurisdiction || {}
  const representatives = report.representatives || {}
  const authority = report.authority || {}
  const notification = report.notification || {}
  const assembly = jurisdiction.assembly_constituency || {}
  const lokSabha = jurisdiction.lok_sabha_constituency || {}

  // Derive human location label from actual jurisdiction, never hardcoded Guwahati
  const locationLabel = (() => {
    if (assembly.name) {
      const district = assembly.district || ''
      if (district) {
        if (district === 'Kamrup Metropolitan') return `${assembly.name}, Guwahati, Assam`
        return `${assembly.name}, ${district}, Assam`
      }
      if (['Mangaldai', 'Sipajhar', 'Dalgaon'].includes(assembly.name)) return `${assembly.name}, Darrang, Assam`
      return `${assembly.name}, Assam`
    }
    if (assembly.district) return `${assembly.district}, Assam`
    if (hasCoords) return `Assam (${report.latitude.toFixed(4)}, ${report.longitude.toFixed(4)})`
    return ''
  })()

  const lokSabhaLabel = (() => {
    if (!lokSabha.id) return 'Lok Sabha'
    if (lokSabha.id === 'GUWAHATI') return 'Guwahati Lok Sabha'
    if (lokSabha.id === 'DARRANG_UDALGURI') return 'Darrang-Udalguri (Mangaldai) Lok Sabha'
    return lokSabha.name ? `${lokSabha.name} Lok Sabha` : 'Lok Sabha'
  })()

  const jurisStatus = jurisdiction.status || report.jurisdiction_status || 'pending'
  const jurisDone = jurisStatus === 'resolved'
  const jurisWarn = jurisStatus === 'unavailable' || jurisStatus === 'outside_supported_area'
  const jurisDetail = jurisDone
    ? `${assembly.name || 'Unknown'} · ${lokSabhaLabel}`
    : jurisStatus === 'unavailable'
      ? 'No location provided'
      : jurisStatus === 'outside_supported_area'
        ? 'Outside supported boundaries'
        : 'Pending'

  const noteStatus = notification.status || 'not_sent'
  const notified = noteStatus === 'sent'
  const noteWarn = noteStatus === 'failed' || noteStatus === 'not_configured'
  const noteDetail = notified
    ? `Email sent${notification.sent_at ? ` · ${new Date(notification.sent_at).toLocaleString()}` : ''}`
    : noteStatus === 'not_configured'
      ? 'Demo mailbox not configured'
      : noteStatus === 'failed'
        ? 'Delivery failed'
        : 'Not sent'

  const mla = representatives.mla && representatives.mla.name ? representatives.mla : null
  const mp = representatives.mp && representatives.mp.name ? representatives.mp : null
  const approximateBoundaries = jurisDone && jurisdiction.method === 'approximate_locality'

  const timeline = [
    { label: 'Report Submitted', state: 'done', detail: new Date(report.created_at).toLocaleString() },
    {
      label: 'AI Analyzed',
      state: failed ? 'warn' : report.analysis_status === 'completed' ? 'done' : 'todo',
      detail: failed
        ? 'Analysis unavailable'
        : report.analysis_status === 'completed'
          ? `${confidence}% confidence`
          : 'Pending',
    },
    {
      label: 'Jurisdiction Identified',
      state: jurisDone ? 'done' : jurisWarn ? 'warn' : 'todo',
      detail: jurisDetail,
    },
    {
      label: 'Authority Notified',
      state: notified ? 'done' : noteWarn ? 'warn' : 'todo',
      detail: noteDetail,
    },
    {
      label: 'Under Review',
      state: report.status === 'reviewed' || report.status === 'resolved' ? 'done' : 'todo',
    },
    { label: 'Resolved', state: report.status === 'resolved' ? 'done' : 'todo' },
  ]

  return (
    <div className="detail-page">
      <Link to="/reports" className="back-link">
        <Icon name="chevron-left" size={16} /> Back to reports
      </Link>

      <div className="detail-head">
        <div>
          <h1>Report {reportId}</h1>
          <div className="detail-badges">
            <StatusBadge status={report.status} />
            <span className={`badge badge-analysis analysis-${report.analysis_status || 'pending'}`}>
              {report.analysis_status === 'completed'
                ? 'Analyzed'
                : report.analysis_status === 'failed'
                  ? 'Analysis failed'
                  : 'Analysis pending'}
            </span>
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-media">
          {report.image_url ? (
            <div className="detail-image-wrap">
              <img src={report.image_url} alt={`Report ${reportId} photo`} className="detail-image" />
              <SeverityBadge severity={report.severity} />
            </div>
          ) : (
            <div className="detail-image-wrap detail-image-missing">
              <Icon name="image" size={40} />
              <span>No image provided</span>
            </div>
          )}
          <p className="detail-desc">{report.description}</p>
        </div>

        <div className="detail-side">
          {failed ? (
            <Alert variant="warning" title="AI analysis is temporarily unavailable. Please try again.">
              Your report was saved. The issue and severity could not be determined.
            </Alert>
          ) : (
            <div className="verdict-card">
              <div className="verdict-head">
                <span className="verdict-kicker">
                  <Icon name="sparkle" size={15} /> Civic Eye analysis
                </span>
                <IssueBadge issueType={report.issue_type} />
              </div>

              <div className="verdict-main">
                <span className={`verdict-glyph severity-${report.severity || 'unknown'}`}>
                  <Icon name={ISSUE_ICONS[report.issue_type] || 'report'} size={34} />
                </span>
                <div className="verdict-issue">
                  <span className="verdict-label">Issue</span>
                  <span className="verdict-value">{report.issue_type || 'Unclassified'}</span>
                  {confidence != null && (
                    <span className="verdict-confidence">{confidence}% AI confidence</span>
                  )}
                </div>
                <div className="verdict-severity">
                  <span className="verdict-label">Severity</span>
                  <SeverityBadge severity={report.severity} />
                  {confidence != null && (
                    <span className="confidence-meter" aria-hidden="true">
                      <span style={{ width: `${confidence}%` }} />
                    </span>
                  )}
                </div>
              </div>

              {report.explanation && (
                <div className="verdict-why">
                  <span className="verdict-label">Why</span>
                  <p>“{report.explanation}”</p>
                </div>
              )}
            </div>
          )}

          <div className="civ-card">
            <span className="civ-card-kicker">
              <Icon name="building" size={15} /> Responsible Authority
            </span>
            <div className="civ-card-body">
              <span className="civ-card-title">{authority.department || 'Not available'}</span>
              <span className="civ-card-sub">{authority.name || '—'}</span>
              {authority.reason ? (
                <p className="civ-card-note">{authority.reason}</p>
              ) : (
                <p className="civ-card-note">Routing based on report location and issue type.</p>
              )}
              {authority.department && assembly.name && (
                <p className="civ-card-note" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Jurisdiction: {assembly.name} {assembly.id ? `(${assembly.id})` : ''} {assembly.district ? `· ${assembly.district}` : ''}
                </p>
              )}
            </div>
          </div>

          <div className="civ-card">
            <span className="civ-card-kicker">
              <Icon name="users" size={15} /> Local Representation
            </span>
            <div className="civ-card-body civ-reps">
              {mla ? (
                <div className="civ-rep-row">
                  <span className="civ-rep-role">MLA</span>
                  <div>
                    <span className="civ-card-title">{mla.name}</span>
                    {assembly.name && (
                      <span className="civ-card-sub">
                        {assembly.name}
                        {assembly.id ? ` (${assembly.id})` : ''}
                      </span>
                    )}
                    {mla.party && <span className="civ-card-party">{mla.party}</span>}
                  </div>
                </div>
              ) : (
                <div className="civ-rep-row">
                  <span className="civ-rep-role">MLA</span>
                  <div>
                    <span className="civ-card-title">Not available</span>
                    <span className="civ-card-sub">
                      {jurisStatus === 'unavailable'
                        ? 'No location provided'
                        : jurisStatus === 'outside_supported_area'
                          ? 'Outside supported boundaries'
                          : 'Jurisdiction not resolved'}
                    </span>
                  </div>
                </div>
              )}
              {mp ? (
                <div className="civ-rep-row">
                  <span className="civ-rep-role">MP</span>
                  <div>
                    <span className="civ-card-title">{mp.name}</span>
                    <span className="civ-card-sub">{lokSabhaLabel}</span>
                    {mp.party && <span className="civ-card-party">{mp.party}</span>}
                  </div>
                </div>
              ) : (
                <div className="civ-rep-row">
                  <span className="civ-rep-role">MP</span>
                  <div>
                    <span className="civ-card-title">Not available</span>
                    <span className="civ-card-sub">
                      {jurisStatus === 'unavailable'
                        ? 'No location provided'
                        : jurisStatus === 'outside_supported_area'
                          ? 'Outside supported boundaries'
                          : 'Jurisdiction not resolved'}
                    </span>
                  </div>
                </div>
              )}
              {approximateBoundaries && (
                <p className="civ-card-disclaimer">
                  Constituency resolved using approximate boundary data.
                  Representatives are shown for information only.
                </p>
              )}
              {!jurisDone && (
                <p className="civ-card-disclaimer">
                  MLA/MP information is informational and location-based. No location was provided for this report.
                </p>
              )}
            </div>
          </div>

          <div className={`civ-card civ-notify notify-${noteStatus}`}>
            <span className="civ-card-kicker">
              <Icon name="send" size={15} /> Authority Notification
            </span>
            <div className="civ-card-body">
              <span className={`notify-badge notify-${noteStatus}`}>
                {notified && 'Sent to demo mailbox'}
                {noteStatus === 'failed' && 'Delivery failed'}
                {noteStatus === 'not_configured' && 'Demo mailbox not configured'}
                {noteStatus === 'not_sent' && 'Not sent'}
                {!['sent', 'failed', 'not_configured', 'not_sent'].includes(noteStatus) &&
                  noteStatus}
              </span>
              {notification.channel && (
                <span className="civ-card-sub">Channel: {notification.channel}</span>
              )}
              {notified && notification.sent_at && (
                <span className="civ-card-sub">
                  {new Date(notification.sent_at).toLocaleString()}
                </span>
              )}
              {noteStatus === 'not_configured' && (
                <p className="civ-card-note">
                  Set demo recipient emails on the server to enable notifications.
                </p>
              )}
            </div>
          </div>

          <div className="meta-panel">
            <h2>Details</h2>
            <dl className="detail-meta">
              <div>
                <dt>Report ID</dt>
                <dd>{reportId}</dd>
              </div>
              <div>
                <dt>Submitted</dt>
                <dd>{new Date(report.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>
                  {hasCoords ? (
                    <>
                      {locationLabel && <span>{locationLabel}<br /></span>}
                      <span style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{report.latitude}, {report.longitude}</span>
                    </>
                  ) : 'Not provided'}
                </dd>
              </div>
              <div>
                <dt>Latitude</dt>
                <dd>{hasCoords ? report.latitude.toFixed(6) : '—'}</dd>
              </div>
              <div>
                <dt>Longitude</dt>
                <dd>{hasCoords ? report.longitude.toFixed(6) : '—'}</dd>
              </div>
              <div>
                <dt>Category</dt>
                <dd>{report.category || '—'}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={report.status} />
                </dd>
              </div>
            </dl>
          </div>

          <div className="timeline-panel">
            <h2>Progress</h2>
            {timeline.map((step) => (
              <TimelineStep
                key={step.label}
                label={step.label}
                state={step.state}
                detail={step.detail}
              />
            ))}
          </div>
        </div>
      </div>

      {hasCoords ? (
        <div className="detail-map-block">
          <h2>📍 Report Location — {locationLabel || 'Assam'}</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '6px 0 10px' }}>
            Latitude: {report.latitude.toFixed(6)} — Longitude: {report.longitude.toFixed(6)}
            {jurisDone && assembly.name && ` — ${assembly.name} (${assembly.id})`}
          </p>
          <ReportMap
            latitude={report.latitude}
            longitude={report.longitude}
            severity={report.severity}
            interactive={false}
          />
        </div>
      ) : (
        pending && (
          <Alert variant="info">Analysis is still running. Check back shortly.</Alert>
        )
      )}
    </div>
  )
}