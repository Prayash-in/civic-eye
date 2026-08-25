export default function Skeleton({ width, height, radius, className = '', style }) {
  return (
    <div
      className={`skeleton${className ? ` ${className}` : ''}`}
      style={{ width, height, ...(radius != null ? { borderRadius: radius } : {}), ...style }}
      aria-hidden="true"
    />
  )
}