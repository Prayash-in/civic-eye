import Icon from './icons'

export default function ErrorNote({ message }) {
  return (
    <div className="error-note" role="alert">
      <Icon name="alert" size={18} />
      <span>{message}</span>
    </div>
  )
}