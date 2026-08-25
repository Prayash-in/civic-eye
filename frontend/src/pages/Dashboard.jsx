import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStats, listReports } from '../api'
import Icon, { ISSUE_ICONS } from '../components/icons'
import { IssueBadge, SeverityBadge, ISSUE_LABELS } from '../components/Badge'
import Skeleton from '../components/Skeleton'
import ErrorNote from '../components/ErrorNote'
import EmptyNote from '../components/EmptyNote'

const SEVERITY_ORDER = ['low', 'medium', 'high', 'critical']

function Bar({ label, value, total, tone }) {
  const pct = total ? Math.round((value / total) * 100) : 0
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className={`bar-fill${tone ? ` bar-fill-${tone}` : ''}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="bar-value">{value}</span>
    </div>
  )
}

function Kpi({ value, label, icon, tone }) {
  return (
    <div className={`kpi-card${tone ? ` kpi-${tone}` : ''}`}>
      <span className="kpi-icon">
        <Icon name={icon} size={22} />
      </span>
      <div className="kpi-body">
        <span className="kpi-value">{value}</span>
        <span className="kpi-label">{label}</span>
      </div>
    </div>
  )
}

function Donut({ data, total }) {
  const size = 180
  const radius = size / 2 - 14
  const circumference = 2 * Math.PI * radius
  let acc = 0

  return (
    <div className="donut-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="donut" role="img" aria-label={`Severity distribution. ${total} total reports.`}>
        <circle className="donut-bg" cx={size / 2} cy={size / 2} r={radius} />
        {data.map(([key, value]) => {
          const frac = total ? value / total : 0
          const dash = frac * circumference
          const element = (
            <circle
              key={key}
              className={`donut-seg severity-${key}`}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              strokeDasharray={`${dash} ${circumference - dash}`}
              strokeDashoffset={-acc}
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
          )
          acc += dash
          return element
        })}
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central" className="donut-center">
          {total}
        </text>
      </svg>
      <ul className="donut-legend">
        {data.map(([key, value]) => (
          <li key={key}>
            <span className={`legend-dot severity-${key}`} aria-hidden="true" />
            <span className="legend-name">{key}</span>
            <span className="legend-value">{value}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [analyzed, setAnalyzed] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    Promise.all([getStats(), listReports({ limit: 500 })])
      .then(([statsData, reports]) => {
        if (cancelled) return
        setStats(statsData)
        setAnalyzed(reports.filter((r) => r.analysis_status === 'completed').length)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <section className="page">
        <ErrorNote message={error} />
      </section>
    )
  }

  if (!stats) {
    return (
      <div className="dashboard-page">
        <Skeleton width="45%" height={34} />
        <div className="kpi-grid">
          {[0, 1, 2, 3].map((i) => (
            <div className="kpi-card" key={i}>
              <Skeleton width={44} height={44} radius={12} />
              <Skeleton width={70} height={30} />
            </div>
          ))}
        </div>
        <div className="dashboard-grid">
          <div className="panel"><Skeleton height={220} /></div>
          <div className="panel"><Skeleton height={220} /></div>
        </div>
      </div>
    )
  }

  const total = stats.total || 0
  const byIssueType = stats.by_issue_type || {}
  const bySeverity = stats.by_severity || {}
  const byStatus = stats.by_status || {}
  const recent = stats.recent || []
  const civic = stats.civic_response || {}
  const civicByAuthority = civic.by_authority || {}
  const civicNotifications = civic.notifications || {}
  const recentNotifications = civic.recent_notifications || []

  const highCritical = (bySeverity.high || 0) + (bySeverity.critical || 0)
  const resolved = byStatus.resolved || 0
  const notifiedSent = civicNotifications.sent || 0

  const authorityRows = Object.entries(civicByAuthority)
    .map(([key, value]) => ({ key, label: key, value }))
    .sort((a, b) => b.value - a.value)

  const notificationRows = Object.entries(civicNotifications)
    .map(([key, value]) => ({ key, label: key.replace(/_/g, ' '), value }))

  const issueRows = Object.entries(byIssueType)
    .map(([key, value]) => ({
      key,
      label: ISSUE_LABELS[key] || key,
      value,
    }))
    .sort((a, b) => b.value - a.value)

  const severityData = SEVERITY_ORDER.filter((key) => bySeverity[key]).map((key) => [
    key,
    bySeverity[key],
  ])

  return (
    <div className="dashboard-page">
      <div className="page-head">
        <h1>Civic Intelligence Dashboard</h1>
        <p className="page-sub">Live overview of reports analyzed by Civic Eye.</p>
      </div>

      <div className="kpi-grid">
        <Kpi value={total} label="Total reports" icon="report" tone="primary" />
        <Kpi value={analyzed ?? '—'} label="Issues analyzed" icon="sparkle" tone="accent" />
        <Kpi value={highCritical} label="High / critical" icon="alert" tone="danger" />
        <Kpi value={resolved} label="Resolved" icon="check" tone="success" />
      </div>

      <div className="kpi-grid">
        <Kpi value={civic.routed ?? 0} label="Routed to authority" icon="building" tone="primary" />
        <Kpi value={civic.unrouted ?? 0} label="Awaiting routing" icon="clock" tone="muted" />
        <Kpi
          value={
            (civic.jurisdiction && civic.jurisdiction.resolved) || 0
          }
          label="Jurisdiction resolved"
          icon="pin"
          tone="accent"
        />
        <Kpi value={notifiedSent} label="Demo notifications sent" icon="send" tone="success" />
      </div>

      <div className="quick-actions">
        <Link to="/report" className="btn btn-primary">
          <Icon name="plus" size={16} /> Report Issue
        </Link>
        <Link to="/map" className="btn btn-secondary">
          <Icon name="map" size={16} /> Explore Map
        </Link>
        <Link to="/reports" className="btn btn-secondary">
          <Icon name="list" size={16} /> View Reports
        </Link>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <h2>Issue Distribution</h2>
          {issueRows.length ? (
            issueRows.map((row) => (
              <Bar key={row.key} label={row.label} value={row.value} total={total} />
            ))
          ) : (
            <EmptyNote message="No issue data yet." icon="report" />
          )}
        </div>

        <div className="panel">
          <h2>Severity Distribution</h2>
          {severityData.length ? (
            <Donut data={severityData} total={total} />
          ) : (
            <EmptyNote message="No severity data yet." icon="report" />
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <h2>Authority Routing</h2>
          {authorityRows.length ? (
            authorityRows.map((row) => (
              <Bar
                key={row.key}
                label={row.label}
                value={row.value}
                total={civic.routed || row.value}
              />
            ))
          ) : (
            <EmptyNote
              message="No routed reports yet."
              hint="Reports with a location are routed to a responsible department."
              icon="building"
            />
          )}
        </div>

        <div className="panel">
          <h2>Authority Notifications</h2>
          {notificationRows.length ? (
            notificationRows.map((row) => (
              <Bar
                key={row.key}
                label={row.label}
                value={row.value}
                total={total}
                tone={row.key === 'sent' ? 'success' : undefined}
              />
            ))
          ) : (
            <EmptyNote message="No notifications recorded yet." icon="send" />
          )}
          {recentNotifications.length > 0 && (
            <ul className="notify-recent">
              {recentNotifications.map((entry) => (
                <li key={entry.id}>
                  <span className={`notify-dot notify-${entry.status}`} aria-hidden="true" />
                  <Link to={`/reports/${entry.report_id}`} className="notify-link">
                    CIV-{String(entry.report_id).padStart(4, '0')}
                  </Link>
                  <span className="notify-dept">{entry.department || '—'}</span>
                  <span className="notify-status">{entry.status.replace(/_/g, ' ')}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="panel recent-panel">
        <h2>Recent Reports</h2>
        {recent.length ? (
          <ul className="recent-list">
            {recent.map((report) => (
              <li key={report.id}>
                {report.image_url ? (
                  <img
                    src={report.image_url}
                    alt=""
                    className="recent-thumb"
                    loading="lazy"
                  />
                ) : (
                  <span className="recent-thumb recent-thumb-empty">
                    <Icon name="image" size={16} />
                  </span>
                )}
                <div className="recent-info">
                  <div className="recent-top">
                    <IssueBadge issueType={report.issue_type} />
                    <SeverityBadge severity={report.severity} />
                  </div>
                  <span className="recent-loc">
                    <Icon name="pin" size={13} />
                    {report.latitude != null
                      ? `${report.latitude.toFixed(4)}, ${report.longitude.toFixed(4)}`
                      : 'No location'}
                  </span>
                </div>
                <span className="recent-time">{new Date(report.created_at).toLocaleString()}</span>
                <Link
                  to={`/reports/${report.id}`}
                  className="recent-link"
                  aria-label={`View report ${report.id}`}
                >
                  <Icon name="chevron-right" size={16} />
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyNote message="No reports yet." hint="Submit your first report to see it here." icon="report" />
        )}
      </div>
    </div>
  )
}