import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { listReports } from '../api'
import Icon, { ISSUE_ICONS } from '../components/icons'
import { IssueBadge, SeverityBadge, StatusBadge, SEVERITY_LABELS, STATUS_LABELS } from '../components/Badge'
import Skeleton from '../components/Skeleton'
import ErrorNote from '../components/ErrorNote'
import EmptyNote from '../components/EmptyNote'

const GROUPS = {
  all: [],
  potholes: ['pothole'],
  drainage: ['blocked_drain', 'open_drain'],
  waste: ['garbage_overflow', 'illegal_dumping'],
  water: ['water_leakage'],
  streetlights: ['broken_streetlight'],
  'road-damage': ['damaged_road'],
}

const GROUP_LABELS = {
  all: 'All',
  potholes: 'Potholes',
  drainage: 'Drainage',
  waste: 'Waste',
  water: 'Water',
  streetlights: 'Streetlights',
  'road-damage': 'Road Damage',
}

const SEVERITY_ORDER = { low: 0, medium: 1, high: 2, critical: 3 }

function CardSkeleton() {
  return (
    <div className="report-card skeleton-card">
      <Skeleton height={160} radius={0} />
      <div className="card-body">
        <Skeleton width="70%" height={22} />
        <Skeleton width="100%" height={14} />
        <Skeleton width="90%" height={14} />
        <Skeleton width="50%" height={12} />
      </div>
    </div>
  )
}

export default function ReportsList() {
  const [reports, setReports] = useState(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [group, setGroup] = useState('all')
  const [severity, setSeverity] = useState('all')
  const [status, setStatus] = useState('all')
  const [sort, setSort] = useState('newest')

  useEffect(() => {
    let cancelled = false
    listReports({ limit: 500 })
      .then((data) => {
        if (!cancelled) setReports(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    if (!reports) return []
    const groups = GROUPS[group] || []
    const query = search.trim().toLowerCase()

    const list = reports.filter((report) => {
      if (groups.length && !groups.includes(report.issue_type)) return false
      if (severity !== 'all' && report.severity !== severity) return false
      if (status !== 'all' && report.status !== status) return false
      if (query) {
        const haystack = [report.description, report.issue_type, report.category]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        if (!haystack.includes(query)) return false
      }
      return true
    })

    list.sort((a, b) => {
      if (sort === 'newest') return new Date(b.created_at) - new Date(a.created_at)
      if (sort === 'oldest') return new Date(a.created_at) - new Date(b.created_at)
      return (SEVERITY_ORDER[b.severity] ?? -1) - (SEVERITY_ORDER[a.severity] ?? -1)
    })

    return list
  }, [reports, search, group, severity, status, sort])

  const hasActiveFilters =
    search.trim() !== '' || group !== 'all' || severity !== 'all' || status !== 'all'

  function clearFilters() {
    setSearch('')
    setGroup('all')
    setSeverity('all')
    setStatus('all')
    setSort('newest')
  }

  return (
    <div className="reports-page">
      <div className="page-head">
        <h1>Reports</h1>
        <p className="page-sub">Browse civic issues detected by Civic Eye.</p>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <Icon name="search" size={18} />
          <input
            type="search"
            placeholder="Search reports…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search reports"
          />
          {search && (
            <button
              type="button"
              className="icon-button"
              onClick={() => setSearch('')}
              aria-label="Clear search"
            >
              <Icon name="close" size={16} />
            </button>
          )}
        </div>

        <div className="sort-box">
          <label htmlFor="sort-select" className="visually-hidden">
            Sort reports
          </label>
          <select
            id="sort-select"
            value={sort}
            onChange={(event) => setSort(event.target.value)}
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="severity">Highest severity</option>
          </select>
        </div>
      </div>

      <div className="filter-chips" role="group" aria-label="Filter by issue">
        {Object.entries(GROUP_LABELS).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={`chip${group === key ? ' active' : ''}`}
            onClick={() => setGroup(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="filter-chips" role="group" aria-label="Filter by severity">
        <button
          type="button"
          className={`chip${severity === 'all' ? ' active' : ''}`}
          onClick={() => setSeverity('all')}
        >
          All severities
        </button>
        {Object.entries(SEVERITY_LABELS).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={`chip severity-${key}${severity === key ? ' active' : ''}`}
            onClick={() => setSeverity(key)}
          >
            <span className="chip-dot" aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>

      <div className="filter-chips" role="group" aria-label="Filter by status">
        <button
          type="button"
          className={`chip${status === 'all' ? ' active' : ''}`}
          onClick={() => setStatus('all')}
        >
          All statuses
        </button>
        {Object.entries(STATUS_LABELS).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={`chip${status === key ? ' active' : ''}`}
            onClick={() => setStatus(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {hasActiveFilters && (
        <div className="toolbar-row">
          <span className="result-count">
            {filtered.length} result{filtered.length === 1 ? '' : 's'}
          </span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={clearFilters}>
            <Icon name="close" size={14} /> Clear Filters
          </button>
        </div>
      )}

      {error && <ErrorNote message={error} />}

      {!error && !reports && (
        <div className="report-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}

      {!error && reports && filtered.length === 0 && (
        <EmptyNote
          icon="search"
          message={
            hasActiveFilters ? 'No reports match your filters.' : 'No reports yet.'
          }
          hint={hasActiveFilters ? 'Try clearing filters or adjusting your search.' : 'Be the first to report an issue.'}
        />
      )}

      {!error && filtered.length > 0 && (
        <div className="report-grid">
          {filtered.map((report) => {
            const confidence =
              report.confidence != null ? Math.round(report.confidence * 100) : null
            return (
              <article className="report-card" key={report.id}>
                <div className="card-media">
                  {report.image_url ? (
                    <img
                      src={report.image_url}
                      alt=""
                      loading="lazy"
                      className="card-thumb"
                    />
                  ) : (
                    <div className="card-thumb card-thumb-placeholder">
                      <Icon name="image" size={28} />
                    </div>
                  )}
                  <span className={`card-glyph severity-${report.severity || 'unknown'}`}>
                    <Icon name={ISSUE_ICONS[report.issue_type] || 'report'} size={16} />
                  </span>
                </div>
                <div className="card-body">
                  <div className="card-badges">
                    <IssueBadge issueType={report.issue_type} />
                    <SeverityBadge severity={report.severity} />
                    <StatusBadge status={report.status} />
                  </div>
                  <p className="card-desc">{report.description}</p>
                  <div className="card-meta">
                    <span className="card-meta-item">
                      <Icon name="sparkle" size={13} />
                      {confidence != null ? `${confidence}% confidence` : 'Analysis pending'}
                    </span>
                    <span className="card-meta-item">
                      <Icon name="pin" size={13} />
                      {report.latitude != null
                        ? `${report.latitude.toFixed(4)}, ${report.longitude.toFixed(4)}`
                        : 'No location'}
                    </span>
                    <span className="card-meta-item">
                      <Icon name="clock" size={13} />
                      {new Date(report.created_at).toLocaleString()}
                    </span>
                  </div>
                  <Link to={`/reports/${report.id}`} className="card-link">
                    View Report <Icon name="chevron-right" size={14} />
                  </Link>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}