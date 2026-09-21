import { useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { api } from '../api/client.js';
import DataTable from '../components/DataTable.jsx';
import MatchActions from '../components/MatchActions.jsx';
import { EmptyState, QueryState, ScoreBar, StatusBadge } from '../components/ui.jsx';
import {
  useAllNotifications,
  useMatches,
  useOfferings,
  useRequirements,
  useSummary,
} from '../hooks/queries.js';
import { formatDate, formatNumber } from '../lib/format.js';

const TABS = ['Requirements', 'Offerings', 'Matches', 'Notifications'];
const byDate = (row) => new Date(row.created_at).getTime();

function Select({ label, value, onChange, options }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted">
      {label}
      <select
        className="input min-w-[10rem] py-1.5"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function Filters({ children }) {
  return <div className="mb-4 flex flex-wrap items-end gap-3">{children}</div>;
}

function NoData() {
  return (
    <EmptyState title="Nothing here yet">
      Submit a requirement or offering from the portals{' '}
      <span className="whitespace-nowrap">(or load the sample data above).</span>
    </EmptyState>
  );
}

function RequirementsTab({ categories }) {
  const [filters, setFilters] = useState({ category: '', status: '' });
  const query = useRequirements(filters);
  const set = (key) => (value) => setFilters((f) => ({ ...f, [key]: value }));
  return (
    <>
      <Filters>
        <Select
          label="Category"
          value={filters.category}
          onChange={set('category')}
          options={categories}
        />
        <Select
          label="Status"
          value={filters.status}
          onChange={set('status')}
          options={['open', 'closed']}
        />
      </Filters>
      <QueryState query={query} empty={<NoData />}>
        {(rows) => (
          <DataTable
            caption="Requirements"
            rows={rows}
            initialSort={{ key: 'created_at', dir: 'desc' }}
            columns={[
              {
                key: 'client_name',
                header: 'Client',
                render: (r) => <span className="font-medium">{r.client_name}</span>,
              },
              { key: 'product_requirement', header: 'Product' },
              { key: 'category', header: 'Category' },
              {
                key: 'quantity',
                header: 'Quantity',
                render: (r) => `${formatNumber(r.quantity)} ${r.unit}`,
              },
              { key: 'budget', header: 'Budget', render: (r) => formatNumber(r.budget) },
              { key: 'location', header: 'Location' },
              {
                key: 'needed_within_days',
                header: 'Needed in',
                render: (r) => `${r.needed_within_days} d`,
              },
              { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
              {
                key: 'created_at',
                header: 'Created',
                value: byDate,
                render: (r) => formatDate(r.created_at),
              },
            ]}
          />
        )}
      </QueryState>
    </>
  );
}

function OfferingsTab({ categories }) {
  const [filters, setFilters] = useState({ category: '', status: '' });
  const query = useOfferings(filters);
  const set = (key) => (value) => setFilters((f) => ({ ...f, [key]: value }));
  return (
    <>
      <Filters>
        <Select
          label="Category"
          value={filters.category}
          onChange={set('category')}
          options={categories}
        />
        <Select
          label="Status"
          value={filters.status}
          onChange={set('status')}
          options={['active', 'inactive']}
        />
      </Filters>
      <QueryState query={query} empty={<NoData />}>
        {(rows) => (
          <DataTable
            caption="Offerings"
            rows={rows}
            initialSort={{ key: 'created_at', dir: 'desc' }}
            columns={[
              {
                key: 'supplier_name',
                header: 'Supplier',
                render: (o) => <span className="font-medium">{o.supplier_name}</span>,
              },
              { key: 'product_offered', header: 'Product' },
              { key: 'category', header: 'Category' },
              {
                key: 'available_quantity',
                header: 'Available',
                render: (o) => `${formatNumber(o.available_quantity)} ${o.unit}`,
              },
              {
                key: 'unit_price',
                header: 'Unit price',
                render: (o) => formatNumber(o.unit_price),
              },
              { key: 'location', header: 'Location' },
              {
                key: 'lead_time_days',
                header: 'Lead time',
                render: (o) => `${o.lead_time_days} d`,
              },
              { key: 'delivery_scope', header: 'Scope' },
              { key: 'status', header: 'Status', render: (o) => <StatusBadge status={o.status} /> },
              {
                key: 'created_at',
                header: 'Created',
                value: byDate,
                render: (o) => formatDate(o.created_at),
              },
            ]}
          />
        )}
      </QueryState>
    </>
  );
}

function MatchesTab() {
  const [filters, setFilters] = useState({ status: '', min_score: '' });
  const query = useMatches(filters);
  const set = (key) => (value) => setFilters((f) => ({ ...f, [key]: value }));
  return (
    <>
      <Filters>
        <Select
          label="Status"
          value={filters.status}
          onChange={set('status')}
          options={['new', 'notified', 'accepted', 'rejected']}
        />
        <Select
          label="Minimum score"
          value={filters.min_score}
          onChange={set('min_score')}
          options={['60', '70', '85']}
        />
      </Filters>
      <QueryState query={query} empty={<NoData />}>
        {(rows) => (
          <DataTable
            caption="Matches"
            rows={rows}
            initialSort={{ key: 'score', dir: 'desc' }}
            columns={[
              {
                key: 'requirement_product',
                header: 'Requirement',
                render: (m) => (
                  <>
                    <span className="font-medium">{m.requirement_product}</span>
                    <span className="block text-xs text-muted">{m.client_name}</span>
                  </>
                ),
              },
              {
                key: 'supplier_name',
                header: 'Supplier',
                render: (m) => (
                  <>
                    <span className="font-medium">{m.supplier_name}</span>
                    <span className="block text-xs text-muted">{m.offering_product}</span>
                  </>
                ),
              },
              { key: 'score', header: 'Score', render: (m) => <ScoreBar score={m.score} /> },
              { key: 'status', header: 'Status', render: (m) => <StatusBadge status={m.status} /> },
              {
                key: 'created_at',
                header: 'Created',
                value: byDate,
                render: (m) => formatDate(m.created_at),
              },
              {
                key: 'actions',
                header: 'Actions',
                sortable: false,
                render: (m) => <MatchActions match={m} />,
              },
            ]}
          />
        )}
      </QueryState>
    </>
  );
}

function NotificationsTab() {
  const [role, setRole] = useState('');
  const query = useAllNotifications();
  return (
    <>
      <Filters>
        <Select
          label="Recipient"
          value={role}
          onChange={setRole}
          options={['client', 'supplier']}
        />
      </Filters>
      <QueryState
        query={query}
        empty={
          <EmptyState title="No notifications yet">
            They are created when a match scores 70 or more.
          </EmptyState>
        }
      >
        {(rows) => (
          <DataTable
            caption="Notifications"
            rows={role ? rows.filter((n) => n.recipient_role === role) : rows}
            initialSort={{ key: 'created_at', dir: 'desc' }}
            columns={[
              {
                key: 'recipient_email',
                header: 'Recipient',
                render: (n) => <span className="font-medium">{n.recipient_email}</span>,
              },
              {
                key: 'recipient_role',
                header: 'Role',
                render: (n) => <span className="capitalize">{n.recipient_role}</span>,
              },
              { key: 'message', header: 'Message' },
              {
                key: 'is_read',
                header: 'Read',
                value: (n) => Number(n.is_read),
                render: (n) => (n.is_read ? 'Read' : 'Unread'),
              },
              {
                key: 'created_at',
                header: 'Created',
                value: byDate,
                render: (n) => formatDate(n.created_at),
              },
            ]}
          />
        )}
      </QueryState>
    </>
  );
}

function SummaryCards() {
  const summary = useSummary();
  const s = summary.data;
  const cards = [
    ['Requirements', s?.total_requirements],
    ['Offerings', s?.total_offerings],
    ['Matches', s?.total_matches],
    ['Average score', s?.average_score == null ? '–' : s.average_score.toFixed(1)],
    ['Accepted', s?.accepted_count],
  ];
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map(([label, value]) => (
        <div key={label} className="card">
          <dt className="eyebrow">{label}</dt>
          <dd className="mt-2 font-display text-3xl font-semibold tabular-nums">
            {summary.isPending ? (
              <span className="inline-block h-8 w-12 animate-pulse rounded bg-line/60" />
            ) : summary.isError ? (
              '!'
            ) : (
              value
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function DevTools() {
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries();
  const seed = useMutation({ mutationFn: api.seed, onSuccess: refresh });
  const rematch = useMutation({ mutationFn: api.rematch, onSuccess: refresh });
  const done = seed.data ?? rematch.data;
  const failed = seed.error ?? rematch.error;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        className="btn-primary"
        disabled={seed.isPending}
        onClick={() => seed.mutate()}
      >
        {seed.isPending ? 'Loading…' : 'Load sample data'}
      </button>
      <button
        type="button"
        className="btn-secondary"
        disabled={rematch.isPending}
        onClick={() => rematch.mutate()}
      >
        Recompute matches
      </button>
      <p role="status" className="w-full text-xs text-muted">
        {failed ? <span className="text-danger">{failed.message}</span> : done?.message}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const { meta } = useOutletContext();
  const [tab, setTab] = useState(TABS[0]);
  const tabRefs = useRef([]);
  const categories = meta.data?.categories ?? [];

  const onKeyDown = (event) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    const next = (TABS.indexOf(tab) + step + TABS.length) % TABS.length;
    setTab(TABS[next]);
    tabRefs.current[next]?.focus();
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Overview</p>
          <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">Dashboard</h1>
        </div>
        {meta.data?.dev_mode && <DevTools />}
      </div>

      <SummaryCards />

      <section className="card">
        <div
          role="tablist"
          aria-label="Dashboard sections"
          className="-mx-1 mb-5 flex gap-1 overflow-x-auto overflow-y-hidden border-b border-line"
          onKeyDown={onKeyDown}
        >
          {TABS.map((name, i) => (
            <button
              key={name}
              ref={(el) => (tabRefs.current[i] = el)}
              type="button"
              role="tab"
              id={`tab-${name}`}
              aria-selected={tab === name}
              aria-controls={`panel-${name}`}
              tabIndex={tab === name ? 0 : -1}
              className={`-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm ${tab === name ? 'border-accent font-medium text-ink' : 'border-transparent text-muted hover:text-ink'}`}
              onClick={() => setTab(name)}
            >
              {name}
            </button>
          ))}
        </div>
        <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
          {tab === 'Requirements' && <RequirementsTab categories={categories} />}
          {tab === 'Offerings' && <OfferingsTab categories={categories} />}
          {tab === 'Matches' && <MatchesTab />}
          {tab === 'Notifications' && <NotificationsTab />}
        </div>
      </section>
    </div>
  );
}
