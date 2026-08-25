import Icon from './icons'
import { ISSUE_ICONS } from './icons'

export const ISSUE_LABELS = {
  pothole: 'Pothole',
  damaged_road: 'Damaged Road',
  garbage_overflow: 'Garbage Overflow',
  illegal_dumping: 'Illegal Dumping',
  broken_streetlight: 'Broken Streetlight',
  water_leakage: 'Water Leakage',
  blocked_drain: 'Blocked Drain',
  open_drain: 'Open Drain',
}

export const SEVERITY_LABELS = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
}

export const STATUS_LABELS = {
  submitted: 'Submitted',
  reviewed: 'Reviewed',
  resolved: 'Resolved',
}

export function IssueBadge({ issueType, glyph = true }) {
  return (
    <span className={`badge badge-issue issue-${issueType || 'unknown'}`}>
      {glyph && (
        <Icon name={ISSUE_ICONS[issueType] || 'report'} size={13} className="badge-glyph" />
      )}
      {ISSUE_LABELS[issueType] || 'Unclassified'}
    </span>
  )
}

export function SeverityBadge({ severity }) {
  return (
    <span className={`badge badge-severity severity-${severity || 'unknown'}`}>
      <span className="badge-dot" aria-hidden="true" />
      {SEVERITY_LABELS[severity] || 'Unknown'}
    </span>
  )
}

export function StatusBadge({ status }) {
  return (
    <span className={`badge badge-status status-${status || 'unknown'}`}>
      {STATUS_LABELS[status] || status || 'Unknown'}
    </span>
  )
}