import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api/client.js';
import { routes } from '../router.jsx';

let session = null;
vi.mock('../hooks/useSession.js', async (original) => ({
  ...(await original()),
  useSession: () => session,
}));

const META = {
  categories: ['Raw Materials & Metals', 'Packaging'],
  units: ['kg', 'tonne', 'piece'],
  delivery_scopes: { local: 100, regional: 500, national: 5000, international: null },
  score_thresholds: { match_min: 60, notify_min: 70 },
  dev_mode: true,
};

const CASES = {
  client: {
    table: 'requirements',
    submit: 'Post requirement',
    product: 'Product requirement',
    text: {
      'Product requirement': 'MS pipes, 2 inch',
      Quantity: '100',
      'Budget (total)': '2500',
      'Delivery timeline (days)': '14',
      'Delivery location': 'Manchester',
    },
    select: { Unit: 'kg' },
    expected: { client_name: 'Acme Ltd', quantity: 100, budget: 2500, needed_within_days: 14 },
  },
  supplier: {
    table: 'offerings',
    submit: 'Post offering',
    product: 'Product offered',
    text: {
      'Product offered': 'Mild steel tubes, 50 mm',
      'Available quantity': '5',
      'Unit price': '1300',
      'Lead time (days)': '0',
      Location: 'Leeds',
    },
    select: { Unit: 'tonne', 'Delivery scope': 'regional' },
    expected: { supplier_name: 'Acme Ltd', available_quantity: 5, unit_price: 1300 },
  },
};

function renderAt(path) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe.each(Object.entries(CASES))('%s dashboard form', (role, c) => {
  beforeEach(() => {
    session = {
      user: { email: 'me@acme.example.com', user_metadata: { role, company: 'Acme Ltd' } },
    };
    Object.assign(api, {
      meta: vi.fn().mockResolvedValue(META),
      matches: vi.fn().mockResolvedValue([]),
      notifications: vi.fn().mockResolvedValue([]),
      suggestCategory: vi.fn().mockResolvedValue({ category: 'Raw Materials & Metals' }),
    });
    Object.assign(api[c.table], {
      mine: vi.fn().mockResolvedValue([]),
      create: vi.fn(async (values) => ({ id: '1', status: 'open', ...values })),
    });
  });

  it('shows inline errors and does not submit when empty', async () => {
    renderAt('/me');
    fireEvent.change(await screen.findByLabelText(c.product), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: c.submit }));
    expect(await screen.findAllByText(/At least 2 characters|Choose a/)).not.toHaveLength(0);
    expect(api[c.table].create).not.toHaveBeenCalled();
  });

  it('suggests the category, submits, and confirms that matching is running', async () => {
    renderAt('/me');
    await screen.findByRole('button', { name: c.submit });
    for (const [label, value] of Object.entries({ ...c.text, ...c.select })) {
      fireEvent.change(screen.getByLabelText(label), { target: { value } });
    }
    fireEvent.blur(screen.getByLabelText(c.product));
    await waitFor(() =>
      expect(screen.getByLabelText('Category').value).toBe('Raw Materials & Metals'),
    );

    fireEvent.click(screen.getByRole('button', { name: c.submit }));
    await waitFor(() => expect(api[c.table].create).toHaveBeenCalledOnce());
    expect(api[c.table].create.mock.calls[0][0]).toMatchObject(c.expected);
    expect(await screen.findByText(/Matching is running now/)).toBeTruthy();
  });
});
