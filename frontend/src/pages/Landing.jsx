import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStats, listReports } from '../api'
import Icon, { ISSUE_ICONS } from '../components/icons'
import { ISSUE_LABELS, SEVERITY_LABELS } from '../components/Badge'
import Skeleton from '../components/Skeleton'

const SHOWCASE = [
  { key: 'pothole' },
  { key: 'damaged_road' },
  { key: 'garbage_overflow' },
  { key: 'water_leakage' },
  { key: 'broken_streetlight' },
  { key: 'blocked_drain' },
]

function Stat({ value, label, icon }) {
  return (
    <div className="stat">
      <span className="stat-icon">
        <Icon name={icon} size={20} />
      </span>
      <div>
        <span className="stat-value">{value}</span>
        <span className="stat-label">{label}</span>
      </div>
    </div>
  )
}

export default function Landing() {
  const [stats, setStats] = useState(null)
  const [analyzed, setAnalyzed] = useState(null)
  const [statsError, setStatsError] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([getStats(), listReports({ limit: 500 })])
      .then(([statsData, reports]) => {
        if (cancelled) return
        setStats(statsData)
        setAnalyzed(reports.filter((r) => r.analysis_status === 'completed').length)
      })
      .catch(() => {
        if (!cancelled) setStatsError(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const total = stats ? stats.total : null
  const categories = stats ? Object.keys(stats.by_issue_type || {}).length : null
  const highCritical = stats
    ? (stats.by_severity.high || 0) + (stats.by_severity.critical || 0)
    : null

  return (
    <section className="landing">
      <div className="hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">
              <Icon name="sparkle" size={14} />
              Civic intelligence, powered by local AI
            </span>
            <h1>
              See a problem.
              <br />
              Report it.
              <br />
              <span className="gradient-text">Let AI do the rest.</span>
            </h1>
            <p className="hero-sub">
              Civic Eye turns citizen reports into structured, actionable civic intelligence —
              classified, prioritized, and mapped in seconds.
            </p>
            <div className="hero-actions">
              <Link to="/report" className="btn btn-primary btn-lg">
                <Icon name="plus" size={18} />
                Report an Issue
              </Link>
              <Link to="/reports" className="btn btn-secondary btn-lg">
                <Icon name="list" size={18} />
                Explore Reports
              </Link>
            </div>

            <div className="hero-stats">
              {statsError ? (
                <>
                  <Stat value="—" label="Total reports" icon="report" />
                  <Stat value="—" label="Issues analyzed" icon="sparkle" />
                  <Stat value="—" label="High / critical" icon="alert" />
                  <Stat value="—" label="Categories" icon="list" />
                  <p className="stats-unavailable">Live statistics are temporarily unavailable.</p>
                </>
              ) : !stats ? (
                <>
                  {[0, 1, 2, 3].map((i) => (
                    <div key={i} className="stat stat-skeleton">
                      <Skeleton width={40} height={40} radius={12} />
                      <Skeleton width={90} height={34} />
                    </div>
                  ))}
                </>
              ) : (
                <>
                  <Stat value={total} label="Total reports" icon="report" />
                  <Stat value={analyzed ?? '—'} label="Issues analyzed" icon="sparkle" />
                  <Stat value={highCritical} label="High / critical" icon="alert" />
                  <Stat value={categories} label="Categories" icon="list" />
                </>
              )}
            </div>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <div className="visual-card visual-photo">
              <span className="visual-photo-glyph">
                <Icon name="camera" size={26} />
              </span>
              <span className="visual-photo-hint">Capture</span>
            </div>
            <div className="visual-line" />
            <div className="visual-card visual-ai">
              <span className="visual-ai-spark">
                <Icon name="sparkle" size={16} />
              </span>
              <span className="visual-ai-text">
                <strong>AI</strong> analyzing…
              </span>
              <span className="visual-ai-bar" />
            </div>
            <div className="visual-line" />
            <div className="visual-card visual-pin">
              <span className="visual-pin-glyph">
                <Icon name="pin" size={24} />
              </span>
              <span className="visual-pin-text">Mapped</span>
            </div>
            <span className="visual-orb visual-orb-1" />
            <span className="visual-orb visual-orb-2" />
          </div>
        </div>
      </div>

      <div className="how-section">
        <h2 className="section-title">How Civic Eye works</h2>
        <div className="steps">
          <div className="step">
            <span className="step-num">01</span>
            <span className="step-icon">
              <Icon name="camera" size={22} />
            </span>
            <h3>Capture</h3>
            <p>Snap a photo of the problem and add a short description.</p>
          </div>
          <div className="step">
            <span className="step-num">02</span>
            <span className="step-icon">
              <Icon name="sparkle" size={22} />
            </span>
            <h3>Analyze</h3>
            <p>Local AI classifies the issue type and assesses its severity.</p>
          </div>
          <div className="step">
            <span className="step-num">03</span>
            <span className="step-icon">
              <Icon name="map" size={22} />
            </span>
            <h3>Act</h3>
            <p>Reports are mapped and ranked so the right people can respond.</p>
          </div>
        </div>
      </div>

      <div className="showcase-section">
        <h2 className="section-title">Issues we detect</h2>
        <div className="showcase-grid">
          {SHOWCASE.map(({ key }) => (
            <div className="showcase-card" key={key}>
              <span className={`showcase-icon issue-${key}`}>
                <Icon name={ISSUE_ICONS[key]} size={22} />
              </span>
              <span>{ISSUE_LABELS[key]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="legend-section">
        <h2 className="section-title">Severity guide</h2>
        <div className="legend">
          {Object.entries(SEVERITY_LABELS).map(([key, label]) => (
            <div className="legend-item" key={key}>
              <span className={`legend-dot severity-${key}`} aria-hidden="true" />
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}