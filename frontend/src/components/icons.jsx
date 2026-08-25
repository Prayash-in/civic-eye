const P = {
  pothole:
    '<path d="M3 6h18" /><path d="M3 18h18" /><path d="M9 6v3.5a2.5 2.5 0 0 0 2 2.45 2.5 2.5 0 0 0 3-2.45V6" />',
  'damaged-road':
    '<path d="M3 6h18" /><path d="M3 18h18" /><path d="M7 6l2 4-3 8" /><path d="M14 6l1.5 3L13 18" />',
  garbage:
    '<path d="M6 7h12l-1 13H7L6 7z" /><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" /><path d="M10 11v5" /><path d="M14 11v5" />',
  dumping:
    '<path d="M4 17h16" /><path d="M7 17l3-6h4l3 6" /><path d="M12 11V8" /><circle cx="12" cy="6.5" r="1.5" />',
  streetlight:
    '<path d="M12 3v9" /><path d="M8 12h8l-1 6H9l-1-6z" /><path d="M9 18l-.5 3" /><path d="M15 18l.5 3" /><path d="M5 7l2 1" /><path d="M19 7l-2 1" />',
  water:
    '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" /><path d="M9 14a3 3 0 0 0 3 3" />',
  'blocked-drain':
    '<rect x="4" y="4" width="16" height="16" rx="2" /><path d="M4 10h16" /><path d="M4 16h16" /><path d="M10 4v16" /><path d="M16 4v16" /><circle cx="12" cy="13" r="2" fill="currentColor" stroke="none" />',
  'open-drain':
    '<path d="M4 7h16l-2 10H6L4 7z" /><path d="M9 7l-1 10" /><path d="M15 7l1 10" />',
  camera:
    '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" /><circle cx="12" cy="14" r="3.5" />',
  gps:
    '<circle cx="12" cy="12" r="7" /><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" /><path d="M12 2v3" /><path d="M12 19v3" /><path d="M2 12h3" /><path d="M19 12h3" />',
  pin: '<path d="M12 21s-7-5.5-7-11a7 7 0 0 1 14 0c0 5.5-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" />',
  chevron: '<path d="M6 9l6 6 6-6" />',
  'chevron-right': '<path d="M9 6l6 6-6 6" />',
  'chevron-left': '<path d="M15 6l-6 6 6 6" />',
  check: '<path d="M5 13l4 4L19 7" />',
  alert: '<path d="M12 3L2.5 20h19L12 3z" /><path d="M12 10v4" /><path d="M12 17h.01" />',
  close: '<path d="M6 6l12 12" /><path d="M18 6L6 18" />',
  plus: '<path d="M12 5v14" /><path d="M5 12h14" />',
  menu: '<path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" />',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" />',
  sun: '<circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="M4.9 4.9l1.4 1.4" /><path d="M17.7 17.7l1.4 1.4" /><path d="M4.9 19.1l1.4-1.4" /><path d="M17.7 6.3l1.4-1.4" />',
  'external-link':
    '<path d="M14 4h6v6" /><path d="M20 4L10 14" /><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6" />',
  search: '<circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" />',
  filter: '<path d="M4 5h16l-6 7v6l-4 2v-8L4 5z" />',
  dashboard:
    '<rect x="4" y="4" width="7" height="7" rx="1" /><rect x="13" y="4" width="7" height="7" rx="1" /><rect x="4" y="13" width="7" height="7" rx="1" /><rect x="13" y="13" width="7" height="7" rx="1" />',
  map: '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z" /><path d="M9 4v14" /><path d="M15 6v14" />',
  report:
    '<path d="M9 3h6a1 1 0 0 1 1 1v1h2a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h2V4a1 1 0 0 1 1-1z" /><path d="M9 10h6" /><path d="M9 14h6" /><path d="M9 18h4" />',
  home: '<path d="M4 11l8-7 8 7" /><path d="M6 9.5V20a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V9.5" />',
  list: '<path d="M8 6h13" /><path d="M8 12h13" /><path d="M8 18h13" /><circle cx="3.5" cy="6" r="1" fill="currentColor" stroke="none" /><circle cx="3.5" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="3.5" cy="18" r="1" fill="currentColor" stroke="none" />',
  clock: '<circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />',
  image: '<rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="M3 17l5-4 4 3 4-3 5 4" />',
  sparkle:
    '<path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3z" /><path d="M18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9L18 15z" />',
  building:
    '<path d="M4 21V5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16" /><path d="M15 9h4a1 1 0 0 1 1 1v11" /><path d="M2 21h20" /><path d="M7 8h2" /><path d="M10 8h2" /><path d="M7 12h2" /><path d="M10 12h2" /><path d="M7 16h2" /><path d="M10 16h2" /><path d="M17 13h1" /><path d="M17 17h1" />',
  users:
    '<circle cx="9" cy="8" r="3.5" /><path d="M3 20a6 6 0 0 1 12 0" /><path d="M16 5a3.5 3.5 0 0 1 0 7" /><path d="M17.5 14.5A6 6 0 0 1 21 20" />',
  send:
    '<path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" />',
}

export function iconSvgString(name, size = 20, color) {
  const inner = P[name] || ''
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${
    color || 'currentColor'
  }" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`
}

export const ISSUE_ICONS = {
  pothole: 'pothole',
  damaged_road: 'damaged-road',
  garbage_overflow: 'garbage',
  illegal_dumping: 'dumping',
  broken_streetlight: 'streetlight',
  water_leakage: 'water',
  blocked_drain: 'blocked-drain',
  open_drain: 'open-drain',
}

export default function Icon({ name, size = 20, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`icon icon-${name}${className ? ` ${className}` : ''}`}
      aria-hidden="true"
      focusable="false"
      dangerouslySetInnerHTML={{ __html: P[name] || '' }}
    />
  )
}