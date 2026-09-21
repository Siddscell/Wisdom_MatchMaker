import { useSetMatchStatus } from '../hooks/queries.js';

/** Accept / Reject for matches still in new|notified; contact details once accepted. */
export default function MatchActions({ match, side }) {
  const setStatus = useSetMatchStatus();

  if (match.status === 'accepted') {
    const contact =
      side === 'client' ? match.supplier_email : side === 'supplier' ? match.client_email : null;
    return contact ? (
      <a className="text-sm text-accent underline underline-offset-2" href={`mailto:${contact}`}>
        {contact}
      </a>
    ) : (
      <span className="text-xs text-muted">Contacts shared</span>
    );
  }
  if (match.status === 'rejected') return <span className="text-xs text-muted">—</span>;

  const busy = setStatus.isPending;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex gap-2">
        <button
          type="button"
          className="btn-primary px-3 py-1 text-xs"
          disabled={busy}
          onClick={() => setStatus.mutate({ id: match.id, status: 'accepted' })}
        >
          Accept
        </button>
        <button
          type="button"
          className="btn-secondary px-3 py-1 text-xs"
          disabled={busy}
          onClick={() => setStatus.mutate({ id: match.id, status: 'rejected' })}
        >
          Reject
        </button>
      </div>
      {setStatus.isError && (
        <p role="alert" className="text-xs text-danger">
          {setStatus.error.message}
        </p>
      )}
    </div>
  );
}
