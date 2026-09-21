import { useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { useMeta } from '../hooks/queries.js';
import { useActingEmail } from '../hooks/useActingEmail.js';
import NotificationBell from './NotificationBell.jsx';

const NAV = [
  ['/client', 'Client'],
  ['/supplier', 'Supplier'],
  ['/dashboard', 'Dashboard'],
];

function ActingAs({ email, setEmail }) {
  const [draft, setDraft] = useState(email);
  return (
    <form
      className="flex items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        setEmail(draft);
      }}
    >
      <label htmlFor="acting-as" className="hidden text-xs text-muted md:block">
        Acting as
      </label>
      <input
        id="acting-as"
        type="email"
        className="input w-44 py-1.5 sm:w-56"
        placeholder="you@company.com"
        aria-label="Acting as (your email)"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={() => draft.trim().toLowerCase() !== email && setEmail(draft)}
      />
    </form>
  );
}

export default function Layout() {
  const [email, setEmail] = useActingEmail();
  const meta = useMeta();

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-20 border-b border-line bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-page flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <Link to="/" className="font-display text-lg font-semibold">
            Supplier<span className="text-accent"> Matchmaker</span>
          </Link>
          <nav
            aria-label="Main"
            className="order-3 flex w-full gap-1 text-sm sm:order-none sm:w-auto"
          >
            {NAV.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 ${isActive ? 'bg-accent-soft font-medium text-accent-strong' : 'text-muted hover:text-ink'}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ActingAs key={email} email={email} setEmail={setEmail} />
            <NotificationBell email={email} />
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-page flex-1 px-4 py-8 sm:px-6 sm:py-12">
        <Outlet context={{ email, setEmail, meta }} />
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-page flex-wrap items-center justify-between gap-2 px-4 py-5 text-xs text-muted sm:px-6">
          <p>
            <strong className="font-semibold text-ink">Demo mode – no password.</strong> Anyone can
            act as any email address.
          </p>
          {meta.data?.dev_mode && (
            <Link to="/dev/outbox" className="underline underline-offset-2 hover:text-ink">
              Dev: email outbox
            </Link>
          )}
        </div>
      </footer>
    </div>
  );
}
