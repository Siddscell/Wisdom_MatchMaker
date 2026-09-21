import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Link, useOutletContext } from 'react-router-dom';
import { api } from '../api/client.js';
import EntityForm from '../components/EntityForm.jsx';
import MatchActions from '../components/MatchActions.jsx';
import { EmptyState, QueryState, ScoreBar, StatusBadge } from '../components/ui.jsx';
import { useMatches, useOfferings, useRequirements } from '../hooks/queries.js';
import { formatNumber } from '../lib/format.js';
import { offeringSchema, requirementSchema } from '../lib/schemas.js';

const ROLES = {
  client: {
    eyebrow: 'Client portal',
    title: 'Tell us what you need',
    intro:
      'Describe the product in your own words. We match on meaning, then check quantity, budget, timing and distance.',
    listTitle: 'My requirements',
    noun: 'requirement',
    submitLabel: 'Submit requirement',
    schema: requirementSchema,
    create: (values) => api.createRequirement(values),
    useItems: useRequirements,
    matchKey: 'requirement_id',
    fields: (meta) => [
      { name: 'client_name', label: 'Company / client name' },
      { name: 'contact_email', label: 'Contact email', type: 'email' },
      {
        name: 'product_requirement',
        label: 'Product requirement',
        type: 'textarea',
        wide: true,
        hint: 'For example: “MS pipes, 2 inch diameter”',
      },
      { name: 'category', label: 'Category', type: 'select', options: meta.categories, wide: true },
      { name: 'quantity', label: 'Quantity', type: 'number' },
      { name: 'unit', label: 'Unit', type: 'select', options: meta.units },
      {
        name: 'budget',
        label: 'Budget (total)',
        type: 'number',
        hint: 'For the whole quantity, not per unit.',
      },
      { name: 'needed_within_days', label: 'Delivery timeline (days)', type: 'number' },
      { name: 'location', label: 'Delivery location', hint: 'City, e.g. Manchester', wide: true },
      { name: 'notes', label: 'Additional notes', type: 'textarea', wide: true, optional: true },
    ],
    title_of: (r) => r.product_requirement,
    details: (r) =>
      `${formatNumber(r.quantity)} ${r.unit} · budget ${formatNumber(r.budget)} · ${r.location} · within ${r.needed_within_days} days`,
    counterpart: (m) => [m.supplier_name, m.offering_product],
  },
  supplier: {
    eyebrow: 'Supplier portal',
    title: 'List what you supply',
    intro:
      'Add your product, stock, price and delivery reach. Matching clients are notified automatically.',
    listTitle: 'My offerings',
    noun: 'offering',
    submitLabel: 'Submit offering',
    schema: offeringSchema,
    create: (values) => api.createOffering(values),
    useItems: useOfferings,
    matchKey: 'offering_id',
    fields: (meta) => [
      { name: 'supplier_name', label: 'Supplier name' },
      { name: 'contact_email', label: 'Contact email', type: 'email' },
      {
        name: 'product_offered',
        label: 'Product offered',
        type: 'textarea',
        wide: true,
        hint: 'For example: “Mild steel tubes, 50 mm OD”',
      },
      { name: 'category', label: 'Category', type: 'select', options: meta.categories, wide: true },
      { name: 'available_quantity', label: 'Available quantity', type: 'number' },
      { name: 'unit', label: 'Unit', type: 'select', options: meta.units },
      { name: 'unit_price', label: 'Unit price', type: 'number', hint: 'Price for one unit.' },
      { name: 'lead_time_days', label: 'Lead time (days)', type: 'number' },
      { name: 'location', label: 'Location', hint: 'City, e.g. Leeds' },
      {
        name: 'delivery_scope',
        label: 'Delivery scope',
        type: 'select',
        options: Object.keys(meta.delivery_scopes),
        hint: 'Local ≤ 100 km, regional ≤ 500 km, national ≤ 5000 km.',
      },
      {
        name: 'pricing_notes',
        label: 'Pricing notes',
        type: 'textarea',
        wide: true,
        optional: true,
        hint: 'Bulk discounts, minimum order, etc.',
      },
      { name: 'notes', label: 'Additional notes', type: 'textarea', wide: true, optional: true },
    ],
    title_of: (o) => o.product_offered,
    details: (o) =>
      `${formatNumber(o.available_quantity)} ${o.unit} · ${formatNumber(o.unit_price)} per ${o.unit} · ${o.location} · ${o.lead_time_days} days lead · ${o.delivery_scope}`,
    counterpart: (m) => [m.client_name, m.requirement_product],
  },
};

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

function MyItems({ role, email }) {
  const config = ROLES[role];
  const items = config.useItems({ email }, { enabled: Boolean(email) });

  if (!email) {
    return (
      <EmptyState title={`Your ${config.noun}s will appear here`}>
        Enter your email under “Acting as” at the top, or submit the form.
      </EmptyState>
    );
  }
  return (
    <QueryState
      query={items}
      empty={
        <EmptyState title={`No ${config.noun}s for ${email} yet`}>
          Submit the form to add your first {config.noun}.
        </EmptyState>
      }
    >
      {(rows) => (
        <ul className="space-y-4">
          {rows.map((item) => (
            <li key={item.id} className="card">
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-lg font-medium">{config.title_of(item)}</h3>
                <StatusBadge status={item.status} />
              </div>
              <p className="mt-1 text-sm text-muted">{config.details(item)}</p>
              <p className="eyebrow mb-1 mt-4">Top matches</p>
              <ItemMatches role={role} item={item} />
            </li>
          ))}
        </ul>
      )}
    </QueryState>
  );
}

export default function PortalPage({ role }) {
  const config = ROLES[role];
  const { email, setEmail, meta } = useOutletContext();
  const queryClient = useQueryClient();
  const [created, setCreated] = useState(null);

  const submit = async (values) => {
    const item = await config.create(values);
    setCreated(item);
    if (item.contact_email !== email) setEmail(item.contact_email);
    queryClient.invalidateQueries({ queryKey: [role === 'client' ? 'requirements' : 'offerings'] });
    queryClient.invalidateQueries({ queryKey: ['summary'] });
  };

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
      <section aria-labelledby="form-title">
        <p className="eyebrow">{config.eyebrow}</p>
        <h1 id="form-title" className="mt-2 text-3xl font-semibold sm:text-4xl">
          {config.title}
        </h1>
        <p className="mt-3 max-w-prose text-muted">{config.intro}</p>

        {created && (
          <div
            role="status"
            className="mt-6 rounded-lg border border-accent/30 bg-accent-soft p-4 text-sm"
          >
            <p className="font-medium text-accent-strong">
              Received: “{config.title_of(created)}”.
            </p>
            <p className="mt-1">
              Matching is running now. Results appear under <strong>{config.listTitle}</strong>{' '}
              within a few seconds, and on the{' '}
              <Link to="/dashboard" className="underline underline-offset-2">
                dashboard
              </Link>
              . You will get a notification for strong matches.
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
              defaultValues={{ contact_email: email }}
              submitLabel={config.submitLabel}
              onSubmit={submit}
            />
          )}
        </div>
      </section>

      <section aria-labelledby="list-title">
        <h2 id="list-title" className="mb-4 text-2xl font-semibold lg:mt-[4.5rem]">
          {config.listTitle}
        </h2>
        <MyItems role={role} email={email} />
      </section>
    </div>
  );
}
