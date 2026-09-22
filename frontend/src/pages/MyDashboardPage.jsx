import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate, useOutletContext } from 'react-router-dom';
import { api } from '../api/client.js';
import EntityForm from '../components/EntityForm.jsx';
import MatchActions from '../components/MatchActions.jsx';
import { EmptyState, QueryState, ScoreBar, Skeleton, StatusBadge } from '../components/ui.jsx';
import { useMatches, useMyListings } from '../hooks/queries.js';
import { formatNumber } from '../lib/format.js';
import { offeringSchema, requirementSchema } from '../lib/schemas.js';

const suggestCategory = (text) => api.suggestCategory(text);

const ROLES = {
  client: {
    table: 'requirements',
    title: 'Your requirements',
    intro:
      'Describe what you need. We match on meaning, then check quantity, budget, timing and distance.',
    noun: 'requirement',
    submitLabel: 'Post requirement',
    schema: requirementSchema,
    matchKey: 'requirement_id',
    statuses: ['open', 'closed'],
    fields: (meta) => [
      { name: 'client_name', label: 'Company / client name' },
      {
        name: 'product_requirement',
        label: 'Product requirement',
        type: 'textarea',
        wide: true,
        hint: 'For example: “MS pipes, 2 inch diameter”. We suggest a category from similar listings.',
        suggest: suggestCategory,
      },
      { name: 'category', label: 'Category', type: 'select', options: meta.categories },
      { name: 'location', label: 'Delivery location', hint: 'City, e.g. Manchester' },
      { name: 'quantity', label: 'Quantity', type: 'number' },
      { name: 'unit', label: 'Unit', type: 'select', options: meta.units },
      {
        name: 'budget',
        label: 'Budget (total)',
        type: 'number',
        hint: 'For the whole quantity. Private to you.',
      },
      { name: 'needed_within_days', label: 'Delivery timeline (days)', type: 'number' },
      { name: 'notes', label: 'Additional notes', type: 'textarea', wide: true, optional: true },
    ],
    title_of: (r) => r.product_requirement,
    details: (r) =>
      `${formatNumber(r.quantity)} ${r.unit} · budget ${formatNumber(r.budget)} · ${r.location} · within ${r.needed_within_days} days`,
    counterpart: (m) => [m.supplier_name, m.offering_product],
  },
  supplier: {
    table: 'offerings',
    title: 'Your offerings',
    intro:
      'List your product, stock, price and delivery reach. Matching clients are notified automatically.',
    noun: 'offering',
    submitLabel: 'Post offering',
    schema: offeringSchema,
    matchKey: 'offering_id',
    statuses: ['active', 'inactive'],
    fields: (meta) => [
      { name: 'supplier_name', label: 'Supplier name' },
      {
        name: 'product_offered',
        label: 'Product offered',
        type: 'textarea',
        wide: true,
        hint: 'For example: “Mild steel tubes, 50 mm OD”. We suggest a category from similar listings.',
        suggest: suggestCategory,
      },
      { name: 'category', label: 'Category', type: 'select', options: meta.categories },
      { name: 'location', label: 'Location', hint: 'City, e.g. Leeds' },
      { name: 'available_quantity', label: 'Available quantity', type: 'number' },
      { name: 'unit', label: 'Unit', type: 'select', options: meta.units },
      {
        name: 'unit_price',
        label: 'Unit price',
        type: 'number',
        hint: 'Per unit. Private to you.',
      },
      { name: 'lead_time_days', label: 'Lead time (days)', type: 'number' },
      {
        name: 'delivery_scope',
        label: 'Delivery scope',
        type: 'select',
        options: Object.keys(meta.delivery_scopes),
        hint: 'Local ≤ 100 km, regional ≤ 500 km, national ≤ 5000 km.',
        wide: true,
      },
      {
        name: 'pricing_notes',
        label: 'Pricing notes',
        type: 'textarea',
        wide: true,
        optional: true,
      },
      { name: 'notes', label: 'Additional notes', type: 'textarea', wide: true, optional: true },
    ],
    title_of: (o) => o.product_offered,
    details: (o) =>
      `${formatNumber(o.available_quantity)} ${o.unit} · ${formatNumber(o.unit_price)} per ${o.unit} · ${o.location} · ${o.lead_time_days} days lead · ${o.delivery_scope}`,
    counterpart: (m) => [m.client_name, m.requirement_product],
  },
};

/** Form values for editing: only the fields the form knows, blanks for nulls. */
const editable = (fields, item) =>
  Object.fromEntries(fields.map((f) => [f.name, item[f.name] ?? '']));

function ItemMatches({ role, item }) {
  const config = ROLES[role];
  const matches = useMatches({ [config.matchKey]: item.id });
  return (
    <QueryState
      query={matches}
      rows={1}
      empty={
        <p className="text-sm text-muted">
          No matches yet. Matching runs in the background and this list refreshes on its own.
        </p>
      }
    >
      {(rows) => (
        <ul className="divide-y divide-line">
          {rows.slice(0, 5).map((match) => {
            const [name, product] = config.counterpart(match);
            return (
              <li key={match.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="font-medium">{name}</p>
                  <p className="truncate text-sm text-muted">{product}</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <ScoreBar score={match.score} />
                  <StatusBadge status={match.status} />
                  <MatchActions match={match} side={role} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </QueryState>
  );
}

function ItemCard({ role, item, meta }) {
  const config = ROLES[role];
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: [config.table] });
    queryClient.invalidateQueries({ queryKey: ['matches'] });
  };
  const [active, inactive] = config.statuses;
  const toggle = useMutation({
    mutationFn: () =>
      api[config.table].setStatus(item.id, item.status === active ? inactive : active),
    onSuccess: refresh,
  });
  const fields = config.fields(meta);

  return (
    <li className="card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-lg font-medium">{config.title_of(item)}</h3>
        <div className="flex items-center gap-2">
          <StatusBadge status={item.status} />
          <button
            type="button"
            className="btn-secondary px-3 py-1 text-xs"
            onClick={() => setEditing((v) => !v)}
          >
            {editing ? 'Cancel' : 'Edit'}
          </button>
          <button
            type="button"
            className="btn-secondary px-3 py-1 text-xs"
            disabled={toggle.isPending}
            onClick={() => toggle.mutate()}
          >
            {item.status === active ? 'Close' : 'Reopen'}
          </button>
        </div>
      </div>
      <p className="mt-1 text-sm text-muted">{config.details(item)}</p>
      {toggle.isError && (
        <p role="alert" className="mt-2 text-sm text-danger">
          {toggle.error.message}
        </p>
      )}
      {editing ? (
        <div className="mt-4 border-t border-line pt-4">
          <EntityForm
            fields={fields}
            schema={config.schema(meta)}
            defaultValues={editable(fields, item)}
            submitLabel="Save changes"
            onSubmit={async (values) => {
              await api[config.table].update(item.id, values);
              setEditing(false);
              refresh();
            }}
          />
        </div>
      ) : (
        <>
          <p className="eyebrow mb-1 mt-4">Top matches</p>
          <ItemMatches role={role} item={item} />
        </>
      )}
    </li>
  );
}

function MyListings({ role, meta }) {
  const config = ROLES[role];
  const items = useMyListings(config.table);
  return (
    <QueryState
      query={items}
      empty={
        <EmptyState title={`No ${config.noun}s yet`}>
          Use the form to post your first {config.noun}.
        </EmptyState>
      }
    >
      {(rows) => (
        <ul className="space-y-4">
          {rows.map((item) => (
            <ItemCard key={item.id} role={role} item={item} meta={meta} />
          ))}
        </ul>
      )}
    </QueryState>
  );
}

export default function MyDashboardPage() {
  const { session, account, meta } = useOutletContext();
  const queryClient = useQueryClient();
  const [created, setCreated] = useState(null);

  if (session === undefined) return <Skeleton rows={4} />;
  if (!account) return <Navigate to="/login" replace />;
  const role = account.role;
  const config = ROLES[role];
  if (!config) {
    return (
      <EmptyState title="Your account has no role">
        Register again as a client or a supplier.
      </EmptyState>
    );
  }

  const submit = async (values) => {
    setCreated(await api[config.table].create(values));
    queryClient.invalidateQueries({ queryKey: [config.table] });
    queryClient.invalidateQueries({ queryKey: ['summary'] });
  };
  const nameField = role === 'client' ? 'client_name' : 'supplier_name';

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,6fr)_minmax(0,6fr)]">
      <section aria-labelledby="form-title">
        <p className="eyebrow">{account.company || account.email}</p>
        <h1 id="form-title" className="mt-2 text-3xl font-semibold sm:text-4xl">
          Post a new {config.noun}
        </h1>
        <p className="mt-3 max-w-prose text-muted">{config.intro}</p>

        {created && (
          <div
            role="status"
            className="mt-6 rounded-lg border border-accent/30 bg-accent-soft p-4 text-sm"
          >
            <p className="font-medium text-accent-strong">Posted: “{config.title_of(created)}”.</p>
            <p className="mt-1">
              Matching is running now. Results appear in your list within a few seconds, and on the{' '}
              <Link to="/dashboard" className="underline underline-offset-2">
                public dashboard
              </Link>
              .
            </p>
          </div>
        )}

        <div className="card mt-6">
          {meta.isPending && <p className="text-sm text-muted">Loading form…</p>}
          {meta.isError && (
            <p role="alert" className="text-sm text-danger">
              Could not load categories and units: {meta.error.message}
            </p>
          )}
          {meta.data && (
            <EntityForm
              key={created?.id ?? 'new'}
              fields={config.fields(meta.data)}
              schema={config.schema(meta.data)}
              defaultValues={{ [nameField]: account.company }}
              submitLabel={config.submitLabel}
              onSubmit={submit}
            />
          )}
        </div>
      </section>

      <section aria-labelledby="list-title">
        <h2 id="list-title" className="mb-4 text-2xl font-semibold lg:mt-[4.5rem]">
          {config.title}
        </h2>
        {meta.data && <MyListings role={role} meta={meta.data} />}
      </section>
    </div>
  );
}
