import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import { listReports } from '../api'
import { useTheme } from '../theme'
import { mapPinHtml } from '../components/mapPins'
import { ISSUE_LABELS, SEVERITY_LABELS } from '../components/Badge'
import Loading from '../components/Loading'
import ErrorNote from '../components/ErrorNote'

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

const TILES = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}

const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[char])
}

function tileLayer(theme) {
  return L.tileLayer(TILES[theme] || TILES.light, {
    maxZoom: 19,
    attribution: TILE_ATTRIBUTION,
  })
}

export default function MapPage() {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const tileRef = useRef(null)
  const layerRef = useRef(null)
  const { theme } = useTheme()

  const [reports, setReports] = useState(null)
  const [error, setError] = useState('')
  const [group, setGroup] = useState('all')
  const [severity, setSeverity] = useState('all')

  useEffect(() => {
    // Mangaldai-focused viewport for presentation; actual report markers determine final focus.
    const map = L.map(containerRef.current, { zoomControl: true }).setView([26.43, 92.04], 11)
    tileRef.current = tileLayer(theme).addTo(map)
    layerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      tileRef.current = null
      layerRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (tileRef.current) map.removeLayer(tileRef.current)
    tileRef.current = tileLayer(theme).addTo(map)
  }, [theme])

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

  const visible = useMemo(() => {
    if (!reports) return []
    const groups = GROUPS[group] || []
    return reports.filter((report) => {
      if (report.latitude == null || report.longitude == null) return false
      if (groups.length && !groups.includes(report.issue_type)) return false
      if (severity !== 'all' && report.severity !== severity) return false
      return true
    })
  }, [reports, group, severity])

  useEffect(() => {
    const layer = layerRef.current
    if (!layer || !reports) return
    layer.clearLayers()

    visible.forEach((report) => {
      const icon = L.divIcon({
        className: 'map-pin-wrap',
        html: mapPinHtml(report.issue_type, report.severity),
        iconSize: [26, 32],
        iconAnchor: [13, 30],
        popupAnchor: [0, -30],
      })

      const marker = L.marker([report.latitude, report.longitude], { icon }).addTo(layer)

      const issue = ISSUE_LABELS[report.issue_type] || 'Unclassified'
      const severityLabel = SEVERITY_LABELS[report.severity] || 'Unknown'
      const confidence =
        report.confidence != null ? `${Math.round(report.confidence * 100)}%` : 'pending'
      const location = `${Number(report.latitude).toFixed(4)}, ${Number(report.longitude).toFixed(4)}`
      const thumb = report.image_url
        ? `<img class="map-popup-thumb" src="${escapeHtml(report.image_url)}" alt="" loading="lazy" />`
        : `<span class="map-popup-thumb map-popup-thumb-empty"></span>`
      const dept =
        report.authority && report.authority.department
          ? escapeHtml(report.authority.department)
          : null
      const acName =
        report.jurisdiction &&
        report.jurisdiction.assembly_constituency &&
        report.jurisdiction.assembly_constituency.name
          ? escapeHtml(report.jurisdiction.assembly_constituency.name)
          : null

      marker.bindPopup(
        `<div class="map-popup">
          ${thumb}
          <div class="map-popup-badges">
            <span class="map-popup-issue">${escapeHtml(issue)}</span>
            <span class="map-popup-sev severity-${escapeHtml(report.severity || 'unknown')}">${escapeHtml(severityLabel)}</span>
          </div>
          <p class="map-popup-desc">${escapeHtml(report.description || '')}</p>
          <div class="map-popup-meta">${escapeHtml(confidence)} · ${escapeHtml(location)}</div>
          ${dept ? `<div class="map-popup-authority">${dept}${acName ? ` · <span title="Assembly constituency">${acName}</span>` : ''}</div>` : ''}
          <a class="map-popup-link" href="/reports/${report.id}">View Report &rarr;</a>
        </div>`,
        { className: 'civic-popup' },
      )
    })
  }, [visible, reports])

  const hasActiveFilters = group !== 'all' || severity !== 'all'

  const severityCounts = useMemo(() => {
    const counts = { low: 0, medium: 0, high: 0, critical: 0 }
    visible.forEach((r) => {
      if (counts[r.severity] != null) counts[r.severity] += 1
    })
    return counts
  }, [visible])

  return (
    <div className="map-page">
      <div className="map-toolbar">
        <div className="filter-chips" role="group" aria-label="Filter map by issue">
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
        <div className="filter-chips" role="group" aria-label="Filter map by severity">
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
        {hasActiveFilters && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setGroup('all')
              setSeverity('all')
            }}
          >
            <IconClose />
            Clear Filters
          </button>
        )}
      </div>

      {error && <ErrorNote message={error} />}

      <div ref={containerRef} className="map-full" />

      {!error && !reports && (
        <div className="map-loading">
          <Loading text="Loading reports…" />
        </div>
      )}

      <div className="map-legend" aria-hidden="true">
        <span className="map-legend-title">Severity</span>
        {Object.entries(SEVERITY_LABELS).map(([key, label]) => (
          <span key={key} className="map-legend-item">
            <span className={`legend-dot severity-${key}`} />
            {label}
            <em>{severityCounts[key] || 0}</em>
          </span>
        ))}
      </div>
    </div>
  )
}

function IconClose() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </svg>
  )
}