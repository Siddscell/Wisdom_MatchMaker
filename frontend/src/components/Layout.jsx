import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useMeta } from '../hooks/queries.js';
import { accountOf, useSession } from '../hooks/useSession.js';
import { supabase } from '../lib/supabase.js';
import NotificationBell from './NotificationBell.jsx';

const navClass = ({ isActive }) =>
  `rounded-md px-3 py-1.5 ${isActive ? 'bg-accent-soft font-medium text-accent-strong' : 'text-muted hover:text-ink'}`;

export default function Layout() {
  const session = useSession();
  const account = accountOf(session);
  const meta = useMeta();
  const navigate = useNavigate();

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
      <header className="sticky top-0 z-20 border-b border-line bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-page flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <Link to="/" className="font-display text-lg font-semibold">
            Supplier<span className="text-accent"> Matchmaker</span>
          </Link>
          <nav aria-label="Main" className="flex gap-1 text-sm">
            <NavLink to="/dashboard" className={navClass}>
              Public dashboard
            </NavLink>
            {account && (
              <NavLink to="/me" className={navClass}>
                My dashboard
              </NavLink>
            )}
          </nav>
          <div className="ml-auto flex items-center gap-2 text-sm">
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
                  <Link to="/login" className="btn-secondary py-1.5">
                    Log in
                  </Link>
                  <Link to="/register" className="btn-primary py-1.5">
                    Register
                  </Link>
                </>
              )
            )}
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-page flex-1 px-4 py-8 sm:px-6 sm:py-12">
        <Outlet context={{ session, account, meta }} />
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-page flex-wrap items-center justify-between gap-2 px-4 py-5 text-xs text-muted sm:px-6">
          <p>Contact details are shared only between the two sides of an accepted match.</p>
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
