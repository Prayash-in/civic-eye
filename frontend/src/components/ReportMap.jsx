import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { useTheme } from '../theme'
import { simplePinHtml } from './mapPins'

// Initial viewport centered on Mangaldai, Assam for presentation.
// User GPS coordinates, when granted, always take precedence and re-center the map at zoom 16.
const DEFAULT_CENTER = [26.43, 92.04]

const TILES = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}

const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'

function tileLayer(theme) {
  return L.tileLayer(TILES[theme] || TILES.light, {
    maxZoom: 19,
    attribution: TILE_ATTRIBUTION,
  })
}

function pinIcon(severity) {
  return L.divIcon({
    className: 'map-pin-wrap',
    html: simplePinHtml(severity),
    iconSize: [26, 32],
    iconAnchor: [13, 30],
    popupAnchor: [0, -28],
  })
}

export default function ReportMap({
  latitude,
  longitude,
  onPick,
  height = '300px',
  severity,
  interactive = true,
}) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const tileRef = useRef(null)
  const markerRef = useRef(null)
  const onPickRef = useRef(onPick)
  onPickRef.current = onPick
  const { theme } = useTheme()

  useEffect(() => {
    const map = L.map(containerRef.current, { zoomControl: true }).setView(DEFAULT_CENTER, 12)
    tileRef.current = tileLayer(theme).addTo(map)
    map.on('click', (event) => {
      if (interactive && onPickRef.current) {
        onPickRef.current(event.latlng.lat, event.latlng.lng)
      }
    })
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      tileRef.current = null
      markerRef.current = null
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
    const map = mapRef.current
    if (!map) return

    if (markerRef.current) {
      markerRef.current.remove()
      markerRef.current = null
    }

    if (latitude != null && longitude != null) {
      // GPS or map-selected location: center at street-level zoom 16 (requirement: 15–17)
      // This ensures the map does NOT remain centered on Guwahati after GPS is obtained.
      map.setView([latitude, longitude], 16, { animate: true })
      markerRef.current = L.marker([latitude, longitude], { icon: pinIcon(severity) }).addTo(map)
    }
  }, [latitude, longitude, severity])

  return <div ref={containerRef} className="map-container" style={{ height }} />
}