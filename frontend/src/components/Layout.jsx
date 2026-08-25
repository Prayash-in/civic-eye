import { Link, NavLink, useLocation } from 'react-router-dom'
import Icon from './icons'
import { useTheme } from '../theme'

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: 'home', end: true },
  { to: '/report', label: 'Report', icon: 'report' },
  { to: '/reports', label: 'Reports', icon: 'list' },
  { to: '/map', label: 'Map', icon: 'map' },
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
]

const linkClass = ({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')

export default function Layout({ children }) {
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand" aria-label="Civic Eye home">
          <span className="brand-mark" aria-hidden="true">
            <Icon name="pin" size={22} />
          </span>
          <span className="brand-text">
            CIVIC <strong>EYE</strong>
          </span>
        </Link>

        <nav className="nav nav-desktop" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="topbar-actions">
          <button
            type="button"
            className="icon-button theme-toggle"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
          >
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={18} />
          </button>
          {!location.pathname.startsWith('/report') && (
            <Link to="/report" className="btn btn-primary btn-report">
              <Icon name="plus" size={16} />
              Report an Issue
            </Link>
          )}
        </div>
      </header>

      <main className="content">{children}</main>

      <footer className="footer">
        <span className="footer-brand">
          <Icon name="pin" size={14} /> CIVIC EYE
        </span>
        <span>Report a civic problem, let AI analyze it, help improve the city.</span>
      </footer>

      <nav className="nav-mobile" aria-label="Primary">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
            <Icon name={item.icon} size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}