import { Link, useOutletContext } from 'react-router-dom';

const STEPS = [
  [
    'Filter',
    'Only pairs that can really trade: category, units, stock, budget, timing and delivery range.',
  ],
  [
    'Understand',
    'A local language model reads both descriptions, so “MS pipes” finds “mild steel tubes”.',
  ],
  ['Learn', 'Every accept or reject retrains the ranking, so matches improve with use.'],
];

export default function HomePage() {
  const { account } = useOutletContext();
  return (
    <div className="space-y-14">
      <section className="max-w-3xl">
        <p className="eyebrow">Supplier–client matching</p>
        <h1 className="mt-3 text-4xl font-semibold leading-tight sm:text-5xl">
          The right supplier for every requirement.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-muted">
          Clients post what they need, suppliers post what they offer, and the matching engine ranks
          the pairs that fit.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          {account ? (
            <Link to="/me" className="btn-primary px-5 py-3">
              Go to my dashboard
            </Link>
          ) : (
            <>
              <Link to="/register?role=client" className="btn-primary px-5 py-3">
                Register as a client
              </Link>
              <Link to="/register?role=supplier" className="btn-primary px-5 py-3">
                Register as a supplier
              </Link>
            </>
          )}
          <Link to="/dashboard" className="btn-secondary px-5 py-3">
            Browse the public dashboard
          </Link>
        </div>
      </section>

      <ol className="grid gap-6 md:grid-cols-3" aria-label="How matching works">
        {STEPS.map(([title, text], i) => (
          <li key={title} className="border-t border-line pt-4">
            <p className="font-display text-3xl text-accent">{i + 1}</p>
            <p className="mt-2 font-medium">{title}</p>
            <p className="mt-1 text-sm text-muted">{text}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
