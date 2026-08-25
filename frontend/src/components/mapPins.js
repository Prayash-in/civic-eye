import { iconSvgString, ISSUE_ICONS } from './icons'

export function mapPinHtml(issueType, severity) {
  const iconName = ISSUE_ICONS[issueType] || 'report'
  const svg = iconSvgString(iconName, 13)
  return `<div class="map-pin pin-${severity || 'unknown'}">${svg}</div>`
}

export function simplePinHtml(severity) {
  return `<div class="map-pin pin-simple pin-${severity || 'unknown'}"></div>`
}