import {
  Link,
  Navigate,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useSearchParams,
} from 'react-router-dom';
import { useMeta } from '../hooks/queries.js';
import { accountOf, useSession } from '../hooks/useSession.js';
import { supabase } from '../lib/supabase.js';
import NotificationBell from './NotificationBell.jsx';
import { Mark } from './ui.jsx';

const navClass = ({ isActive }) =>
  `px-3 py-1.5 ${isActive ? 'font-medium text-ink' : 'text-muted hover:text-ink'}`;

export default function Layout() {
  const session = useSession();
  const account = accountOf(session);
  const meta = useMeta();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const q = useSearchParams()[0].get('q') ?? '';
  const search = (event) => {
    event.preventDefault();
    const text = new FormData(event.currentTarget).get('q').trim();
    navigate(text ? `/dashboard?q=${encodeURIComponent(text)}` : '/dashboard');
  };

  const logout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-20 bg-paper/90 backdrop-blur">
        <div className="mx-auto grid max-w-page grid-cols-[1fr_auto] items-center gap-x-6 gap-y-2 px-4 py-4 sm:grid-cols-[1fr_auto_1fr] sm:px-6">
          <Link to="/" className="flex items-center gap-2 text-lg font-medium tracking-[-0.02em]">
            <Mark />
            Wisdom
          </Link>
          <nav
            aria-label="Main"
            className="order-3 col-span-2 flex justify-center gap-1 text-sm sm:order-none sm:col-span-1"
          >
            <NavLink to="/" end className={navClass}>
              Home
            </NavLink>
            {account?.role !== 'supplier' && (
              <Link to="/register?role=supplier" className={navClass({ isActive: false })}>
                Become a Supplier
              </Link>
            )}
            {account && (
              <NavLink to="/me" className={navClass}>
                My dashboard
              </NavLink>
            )}
            <form role="search" onSubmit={search} className="ml-2">
              <input
                key={q}
                type="search"
                name="q"
                defaultValue={q}
                aria-label="Search listings"
                placeholder="Search items, suppliers, cities…"
                className="input w-44 py-1.5 sm:w-56"
              />
            </form>
          </nav>
          <div className="flex items-center justify-end gap-2 text-sm">
            {account ? (
              <>
                <span className="hidden text-muted md:inline">{account.email}</span>
                <NotificationBell email={account.email} />
                <button type="button" className="btn-secondary py-1.5" onClick={logout}>
                  Log out
                </button>
              </>
            ) : (
              session !== undefined && (
                <>
                  <Link to="/login" className="px-3 py-1.5 text-muted hover:text-ink">
                    Log in
                  </Link>
                  <Link to="/register" className="btn-primary">
                    Get started
                  </Link>
                </>
              )
            )}
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-page flex-1 px-4 py-8 sm:px-6 sm:py-12">
        {/* Invited / dashboard-created users have no role yet: finish the account first. */}
        {account && !account.role && pathname !== '/me' ? (
          <Navigate to="/me" replace />
        ) : (
          <Outlet context={{ session, account, meta }} />
        )}
      </main>

      <footer className="mt-16 border-t border-line">
        <div className="mx-auto flex max-w-page flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-muted sm:px-6">
          <p className="flex items-center gap-2">
            <Mark className="h-4 w-4 text-ink" />
            Wisdom. Contact details are shared only after both sides accept.
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
