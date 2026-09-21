import { scoreBand } from '../lib/format.js';

const BAND_STYLE = { strong: 'bg-band-strong', good: 'bg-band-good', fair: 'bg-band-fair' };
const BAND_LABEL = { strong: 'Strong', good: 'Good', fair: 'Fair' };

/** Number + bar + band word, so the score never depends on colour alone. */
export function ScoreBar({ score }) {
  const band = scoreBand(score);
  return (
    <div className="flex min-w-[10rem] items-center gap-2">
      <span className="w-10 text-sm font-semibold tabular-nums">{score.toFixed(1)}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line" aria-hidden="true">
        <div className={`h-full rounded-full ${BAND_STYLE[band]}`} style={{ width: `${score}%` }} />
      </div>
      <span className="w-12 text-xs text-muted">{BAND_LABEL[band]}</span>
    </div>
  );
}

const STATUS_STYLE = {
  new: 'border-line bg-surface text-ink',
  notified: 'border-accent/30 bg-accent-soft text-accent-strong',
  accepted: 'border-accent bg-accent text-white',
  rejected: 'border-line bg-paper text-muted line-through decoration-muted/60',
  open: 'border-accent/30 bg-accent-soft text-accent-strong',
  active: 'border-accent/30 bg-accent-soft text-accent-strong',
  closed: 'border-line bg-paper text-muted',
  inactive: 'border-line bg-paper text-muted',
};

export function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLE[status] ?? STATUS_STYLE.new}`}
    >
      {status}
    </span>
  );
}

export function Skeleton({ rows = 3 }) {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-12 animate-pulse rounded-md bg-line/60" />
      ))}
    </div>
  );
}

export function EmptyState({ title, children }) {
  return (
    <div className="rounded-md border border-dashed border-line px-4 py-8 text-center">
      <p className="font-medium">{title}</p>
      {children && <div className="mt-2 text-sm text-muted">{children}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div role="alert" className="rounded-md border border-danger/30 bg-danger/5 px-4 py-4 text-sm">
      <p className="font-medium text-danger">Could not load this.</p>
      <p className="mt-1 text-muted">{error?.message}</p>
      <button type="button" className="btn-secondary mt-3" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}

/** Renders loading / error / empty states for a TanStack query, else children(data). */
export function QueryState({ query, empty, rows, children }) {
  if (query.isPending) return <Skeleton rows={rows} />;
  if (query.isError) return <ErrorState error={query.error} onRetry={() => query.refetch()} />;
  if (Array.isArray(query.data) && query.data.length === 0) return empty;
  return children(query.data);
}
