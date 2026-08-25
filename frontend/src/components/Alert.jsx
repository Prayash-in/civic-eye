import Icon from './icons'

const ICON_BY_VARIANT = {
  info: 'alert',
  success: 'check',
  warning: 'alert',
  danger: 'alert',
}

export default function Alert({ variant = 'info', title, children, className = '' }) {
  const icon = ICON_BY_VARIANT[variant] || 'alert'
  return (
    <div
      className={`alert alert-${variant}${className ? ` ${className}` : ''}`}
      role={variant === 'danger' ? 'alert' : variant === 'info' ? 'status' : undefined}
    >
      <span className="alert-icon">
        <Icon name={icon} size={18} />
      </span>
      <div className="alert-body">
        {title && <strong className="alert-title">{title}</strong>}
        <div>{children}</div>
      </div>
    </div>
  )
}