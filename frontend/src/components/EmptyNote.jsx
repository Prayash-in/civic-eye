import Icon from './icons'

export default function EmptyNote({ message, icon = 'report', hint }) {
  return (
    <div className="empty-note">
      <span className="empty-note-icon">
        <Icon name={icon} size={28} />
      </span>
      <span className="empty-note-text">{message}</span>
      {hint && <span className="empty-note-hint">{hint}</span>}
    </div>
  )
}