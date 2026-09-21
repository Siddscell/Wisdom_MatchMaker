import { useOutletContext } from 'react-router-dom';
import { EmptyState, QueryState } from '../components/ui.jsx';
import { useOutbox } from '../hooks/queries.js';
import { formatDate } from '../lib/format.js';

function OutboxList() {
  const outbox = useOutbox();
  return (
    <QueryState
      query={outbox}
      empty={
        <EmptyState title="No emails yet">
          Emails are queued when a match scores 70 or more.
        </EmptyState>
      }
    >
      {(emails) => (
        <ul className="space-y-3">
          {emails.map((mail) => (
            <li key={mail.id} className="card">
              <div className="flex flex-wrap justify-between gap-2 text-sm">
                <p>
                  <span className="text-muted">To </span>
                  <span className="font-medium">{mail.to_email}</span>
                </p>
                <p className="text-muted">
                  {formatDate(mail.created_at)} · {mail.sent_at ? 'sent' : 'not sent (outbox only)'}
                </p>
              </div>
              <p className="mt-2 font-medium">{mail.subject}</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-muted">{mail.body}</p>
            </li>
          ))}
        </ul>
      )}
    </QueryState>
  );
}

export default function OutboxPage() {
  const { meta } = useOutletContext();
  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow">Development</p>
        <h1 className="mt-2 text-3xl font-semibold">Email outbox</h1>
        <p className="mt-2 text-muted">
          Emails the platform would send. With EMAIL_BACKEND=outbox nothing leaves the server.
        </p>
      </div>
      {meta.data && !meta.data.dev_mode ? (
        <EmptyState title="Not available">The outbox is only shown in development mode.</EmptyState>
      ) : (
        <OutboxList />
      )}
    </div>
  );
}
