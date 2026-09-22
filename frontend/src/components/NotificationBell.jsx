import { useEffect, useRef, useState } from 'react';
import { useMarkRead, useMyNotifications } from '../hooks/queries.js';
import { formatDate } from '../lib/format.js';

const TOAST_MS = 6000;

/** Bell with unread count, a dropdown of recent notifications, and toasts for new ones. */
export default function NotificationBell({ email }) {
  const query = useMyNotifications(email);
  const data = query.data ?? [];
  const markRead = useMarkRead();
  const [open, setOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const seen = useRef(null);
  const panel = useRef(null);
  const unread = data.filter((n) => !n.is_read);

  // Toast only for notifications that arrive after the first successful load for this email.
  useEffect(() => {
    if (!query.isSuccess) return;
    if (seen.current?.email !== email) {
      seen.current = { email, ids: new Set(query.data.map((n) => n.id)) };
      return;
    }
    const fresh = query.data.filter((n) => !seen.current.ids.has(n.id));
    fresh.forEach((n) => seen.current.ids.add(n.id));
    if (fresh.length) setToasts((current) => [...current, ...fresh]);
  }, [query.isSuccess, query.data, email]);

  useEffect(() => {
    if (!toasts.length) return undefined;
    const timer = setTimeout(() => setToasts((current) => current.slice(1)), TOAST_MS);
    return () => clearTimeout(timer);
  }, [toasts]);

  useEffect(() => {
    if (!open) return undefined;
    const close = (event) => {
      if (
        event.key === 'Escape' ||
        (event.type === 'mousedown' && !panel.current?.contains(event.target))
      ) {
        setOpen(false);
      }
    };
    document.addEventListener('keydown', close);
    document.addEventListener('mousedown', close);
    return () => {
      document.removeEventListener('keydown', close);
      document.removeEventListener('mousedown', close);
    };
  }, [open]);

  return (
    <div className="relative" ref={panel}>
      <button
        type="button"
        className="relative rounded-md p-2 text-ink hover:bg-line/50"
        aria-label={email ? `Notifications, ${unread.length} unread` : 'Notifications'}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          aria-hidden="true"
        >
          <path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {unread.length > 0 && (
          <span className="absolute -right-0.5 -top-0.5 min-w-[1.1rem] rounded-full bg-accent px-1 text-center text-[0.65rem] font-semibold leading-[1.1rem] text-white">
            {unread.length}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-[min(22rem,calc(100vw-2rem))] rounded-lg border border-line bg-surface p-2 shadow-lg">
          {!email && (
            <p className="p-3 text-sm text-muted">
              Enter your email under “Acting as” to see your notifications.
            </p>
          )}
          {email && data.length === 0 && (
            <p className="p-3 text-sm text-muted">No notifications yet.</p>
          )}
          <ul className="max-h-96 overflow-y-auto">
            {data.slice(0, 15).map((n) => (
              <li key={n.id} className="rounded-md p-3 hover:bg-paper">
                <p className={`text-sm ${n.is_read ? 'text-muted' : 'font-medium'}`}>{n.message}</p>
                <div className="mt-1 flex items-center justify-between text-xs text-muted">
                  <span>{formatDate(n.created_at)}</span>
                  {!n.is_read && (
                    <button
                      type="button"
                      className="text-accent underline-offset-2 hover:underline"
                      onClick={() => markRead.mutate(n.id)}
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-40 flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      >
        {toasts.map((n) => (
          <div
            key={n.id}
            className="rounded-lg border border-accent/30 bg-surface p-4 text-sm shadow-lg"
          >
            <p className="eyebrow text-accent">New match</p>
            <p className="mt-1">{n.message}</p>
            <button
              type="button"
              className="mt-2 text-xs text-muted hover:text-ink"
              onClick={() => setToasts((c) => c.filter((t) => t.id !== n.id))}
            >
              Dismiss
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
