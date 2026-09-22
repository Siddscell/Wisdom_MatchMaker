import { Link, useOutletContext } from 'react-router-dom';
import { Mark } from '../components/ui.jsx';
import { useSummary } from '../hooks/queries.js';
import { formatNumber } from '../lib/format.js';

/** Rolling hills with two glossy discs, supply and demand, drifting toward each other. */
function HeroArt() {
  return (
    <svg
      viewBox="0 0 1200 420"
      preserveAspectRatio="xMidYMax slice"
      className="absolute inset-x-0 bottom-0 h-[46%] w-full"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="disc" cx="35%" cy="30%" r="80%">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="0.45" stopColor="#d7f1e2" />
          <stop offset="1" stopColor="#5aa77f" />
        </radialGradient>
        <linearGradient id="rim" x1="0" x2="1">
          <stop offset="0" stopColor="#e9f7ef" />
          <stop offset="1" stopColor="#2f7d58" />
        </linearGradient>
        <linearGradient id="far" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#a9dcbf" />
          <stop offset="1" stopColor="#5fae86" />
        </linearGradient>
        <linearGradient id="mid" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3d9a6d" />
          <stop offset="1" stopColor="#15563b" />
        </linearGradient>
        <linearGradient id="near" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#12442f" />
          <stop offset="1" stopColor="#03140d" />
        </linearGradient>
      </defs>
      <path
        d="M0 250 C 180 170 330 210 480 190 S 820 120 1000 170 S 1160 190 1200 180 V420 H0 Z"
        fill="url(#far)"
      />
      <g className="hero-disc hero-disc-left">
        <ellipse
          cx="300"
          cy="275"
          rx="18"
          ry="96"
          fill="url(#rim)"
          transform="rotate(-18 300 275)"
        />
        <ellipse
          cx="283"
          cy="272"
          rx="76"
          ry="96"
          fill="url(#disc)"
          transform="rotate(-18 283 272)"
        />
      </g>
      <g className="hero-disc hero-disc-right">
        <ellipse
          cx="900"
          cy="258"
          rx="18"
          ry="100"
          fill="url(#rim)"
          transform="rotate(16 900 258)"
        />
        <ellipse
          cx="917"
          cy="255"
          rx="80"
          ry="100"
          fill="url(#disc)"
          transform="rotate(16 917 255)"
        />
      </g>
      <path
        d="M0 300 C 150 250 300 290 450 270 S 760 220 930 262 S 1120 280 1200 250 V420 H0 Z"
        fill="url(#mid)"
      />
      <path d="M0 350 C 200 310 380 360 600 330 S 980 300 1200 330 V420 H0 Z" fill="url(#near)" />
    </svg>
  );
}

function LiveNumbers() {
  const { data } = useSummary();
  if (!data || data.total_requirements + data.total_offerings === 0) return null;
  const figures = [
    [data.total_requirements, 'requirements posted'],
    [data.total_offerings, 'offerings listed'],
    [data.total_matches, 'matches found'],
  ];
  return (
    <section aria-label="Wisdom right now" className="flex flex-wrap items-end gap-x-14 gap-y-6">
      <p className="max-w-[12rem] text-sm text-muted">Live on Wisdom right now</p>
      {figures.map(([value, label]) => (
        <p key={label}>
          <span className="block text-3xl font-medium tracking-[-0.03em] tabular-nums">
            {formatNumber(value)}
          </span>
          <span className="text-sm text-muted">{label}</span>
        </p>
      ))}
    </section>
  );
}

export default function HomePage() {
  const { account } = useOutletContext();
  const start = account ? '/me' : '/register';

  return (
    <div className="space-y-24">
      <section className="relative flex min-h-[34rem] flex-col items-center overflow-hidden rounded-panel bg-gradient-to-b from-[#eef8f1] via-mint to-[#7cc49e] px-6 pt-16 text-center sm:min-h-[40rem] sm:pt-20">
        <Mark className="relative z-10 h-8 w-8 text-ink" />
        <h1 className="relative z-10 mt-5 max-w-3xl text-5xl leading-[1.02] sm:text-7xl">
          The right supplier, found for you
        </h1>
        <p className="relative z-10 mt-5 max-w-xl text-lg text-ink/70">
          Post what you need or what you make. Wisdom reads both, checks price, stock, timing and
          distance, and introduces the pair that fits.
        </p>
        <div className="relative z-10 mt-8 flex flex-wrap justify-center gap-3">
          <Link to={start} className="btn-primary px-6 py-2.5">
            {account ? 'Open my dashboard' : 'Get started'}
          </Link>
          <Link
            to="/dashboard"
            className="btn border border-ink/15 bg-white/60 px-6 py-2.5 hover:bg-white"
          >
            Browse listings
          </Link>
        </div>
        <HeroArt />
      </section>

      <section className="grid gap-8 md:grid-cols-2 md:items-start">
        <div>
          <h2 className="text-4xl sm:text-5xl">What is Wisdom?</h2>
          <Link to="/dashboard" className="btn-primary mt-6">
            See it working
          </Link>
        </div>
        <p className="text-2xl leading-snug tracking-[-0.01em] text-ink/80">
          A marketplace for Indian businesses that does the searching for you. Describe a product in
          your own words, add a photo if you have one, and Wisdom finds who can supply it, or who
          needs it.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-[1.4fr_1fr_1fr]">
        <article className="relative min-h-[17rem] overflow-hidden rounded-panel bg-gradient-to-br from-[#f3fbf6] to-mint p-7">
          <h3 className="text-2xl">Understands what you mean</h3>
          <p className="absolute bottom-7 left-7 max-w-xs text-sm text-ink/70">
            “MS pipes” finds “mild steel tubes”. A photo of the part finds the listing that shows
            it.
          </p>
          <svg
            viewBox="0 0 200 200"
            className="absolute -bottom-10 -right-6 h-52 w-52"
            aria-hidden="true"
          >
            <circle cx="80" cy="110" r="62" fill="#5aa77f" opacity="0.35" />
            <circle cx="125" cy="95" r="62" fill="#16734f" opacity="0.55" />
          </svg>
        </article>
        <article className="flex min-h-[17rem] flex-col justify-between rounded-panel bg-ink p-7 text-white">
          <h3 className="text-2xl">Private until you say yes</h3>
          <p className="text-sm text-white/70">
            Prices, budgets and contact details stay hidden. Both sides see each other only after a
            match is accepted.
          </p>
        </article>
        <article className="flex min-h-[17rem] flex-col justify-between rounded-panel bg-forest p-7 text-white">
          <h3 className="text-2xl">Gets better with every decision</h3>
          <p className="text-sm text-white/70">
            Each accept or reject teaches Wisdom what a good match looks like for your trade.
          </p>
        </article>
      </section>

      <LiveNumbers />

      <section className="grid gap-10 md:grid-cols-[1fr_1.3fr]">
        <div>
          <h2 className="text-4xl sm:text-5xl">Two ways in</h2>
          <p className="mt-4 max-w-sm text-muted">
            Register once as a buyer or a supplier. Matching runs the moment you post.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            [
              'For buyers',
              'Post a requirement with quantity, budget and deadline. Get ranked suppliers who can deliver to your city.',
              'client',
              'Register as a buyer',
            ],
            [
              'For suppliers',
              'List what you make, your stock and your delivery reach. Hear about buyers who need it.',
              'supplier',
              'Register as a supplier',
            ],
          ].map(([title, text, role, cta]) => (
            <article
              key={role}
              className="flex flex-col rounded-panel border border-line bg-surface p-7"
            >
              <h3 className="text-2xl">{title}</h3>
              <p className="mt-3 flex-1 text-sm text-muted">{text}</p>
              <Link
                to={account ? '/me' : `/register?role=${role}`}
                className="btn-secondary mt-6 self-start"
              >
                {account ? 'Open my dashboard' : cta}
              </Link>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
