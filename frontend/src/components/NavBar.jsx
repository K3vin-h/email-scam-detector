import { NavLink } from 'react-router-dom';

function NavItem({ to, end, children }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? 'bg-slate-100 text-slate-900'
            : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
        }`
      }
    >
      {children}
    </NavLink>
  );
}

export function NavBar() {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-10">
      <nav className="max-w-5xl mx-auto px-6 h-14 flex items-center gap-8">
        <span className="text-slate-900 font-bold text-base tracking-tight">
          Scam Filter
        </span>
        <div className="flex items-center gap-1 ml-4">
          <NavItem to="/" end>Dashboard</NavItem>
          <NavItem to="/reports">Reports</NavItem>
          <NavItem to="/settings">Settings</NavItem>
        </div>
      </nav>
    </header>
  );
}
