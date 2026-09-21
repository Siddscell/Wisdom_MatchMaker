import { Link } from 'react-router-dom';

const STEPS = [
  [
    'Filter',
    'Only pairs that can actually trade survive: same category, compatible units, enough stock, within budget, fast enough, and inside the supplier’s delivery range.',
  ],
  [
    'Understand meaning',
    'A local language model reads both descriptions, so “MS pipes” finds “mild steel tubes” even with no words in common.',
  ],
  [
    'Score',
    'Meaning, price, quantity, delivery time and distance combine into one score from 0 to 100. Strong matches notify both sides.',
  ],
];

function Entry({ to, eyebrow, title, text }) {
  return (
    <Link to={to} className="card group block transition-colors hover:border-accent">
      <p className="eyebrow">{eyebrow}</p>
      <p className="mt-3 font-display text-2xl font-semibold group-hover:text-accent">{title} →</p>
      <p className="mt-2 text-sm text-muted">{text}</p>
    </Link>
  );
}

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="max-w-3xl">
        <p className="eyebrow">Supplier–client matching</p>
        <h1 className="mt-3 text-4xl font-semibold leading-tight sm:text-5xl">
          The right supplier for every requirement, found for you.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-muted">
          Clients describe what they need. Suppliers describe what they offer. The matching engine
          ranks the pairs that fit and tells both sides.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2" aria-label="Get started">
        <Entry
          to="/client"
          eyebrow="For buyers"
          title="I need a product"
          text="Post a requirement and see ranked suppliers."
        />
        <Entry
          to="/supplier"
          eyebrow="For suppliers"
          title="I supply products"
          text="List an offering and hear about matching buyers."
        />
      </section>

      <section aria-labelledby="how">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="how" className="text-2xl font-semibold">
            How matching works
          </h2>
          <Link to="/dashboard" className="text-sm text-accent underline underline-offset-2">
            See every match on the dashboard
          </Link>
        </div>
        <ol className="mt-6 grid gap-6 md:grid-cols-3">
          {STEPS.map(([title, text], i) => (
            <li key={title} className="border-t border-line pt-4">
              <p className="font-display text-3xl text-accent">{i + 1}</p>
              <p className="mt-2 font-medium">{title}</p>
              <p className="mt-1 text-sm text-muted">{text}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
