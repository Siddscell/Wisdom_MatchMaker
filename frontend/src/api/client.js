/**
 * The frontend's only path to the backend. Shapes mirror backend/app/schemas.py.
 *
 * @typedef {{ categories: string[], units: string[],
 *   delivery_scopes: Record<string, number|null>,
 *   score_thresholds: { match_min: number, notify_min: number }, dev_mode: boolean }} Meta
 * @typedef {{ id: string, client_name: string, contact_email?: string,
 *   product_requirement: string, category: string, quantity: number, unit: string,
 *   budget?: number, location: string, needed_within_days: number, notes: string|null,
 *   status: 'open'|'closed', created_at: string }} Requirement
 * @typedef {{ id: string, supplier_name: string, contact_email?: string,
 *   product_offered: string, category: string, available_quantity: number, unit: string,
 *   unit_price?: number, pricing_notes?: string|null, location: string, lead_time_days: number,
 *   delivery_scope: string, notes: string|null, status: 'active'|'inactive',
 *   created_at: string }} Offering
 * @typedef {{ id: string, requirement_id: string, offering_id: string, score: number,
 *   status: 'new'|'notified'|'accepted'|'rejected', created_at: string, updated_at: string,
 *   requirement_product: string, client_name: string, offering_product: string,
 *   supplier_name: string, client_email: string|null, supplier_email: string|null }} Match
 *   (Requirement/Offering fields marked ? are only in the owner's view; match emails only
 *   reach the two parties of an accepted match)
 * @typedef {{ id: string, match_id: string, recipient_role: 'client'|'supplier',
 *   recipient_email: string, message: string, is_read: boolean, created_at: string }} Notification
 * @typedef {{ total_requirements: number, total_offerings: number, total_matches: number,
 *   average_score: number|null, accepted_count: number,
 *   matches_by_status: Record<string, number> }} Summary
 * @typedef {{ id: string, to_email: string, subject: string, body: string,
 *   created_at: string, sent_at: string|null }} OutboxEmail
 */

import { env } from '../lib/env.js';
import { supabase } from '../lib/supabase.js';

/** Thrown for any non-2xx response; `fields` maps field name -> message (validation errors). */
export class ApiError extends Error {
  constructor(status, { code = 'error', message = 'Request failed', fields = {} } = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

async function request(path, { params, body, method = body ? 'POST' : 'GET' } = {}) {
  const query = params
    ? '?' +
      new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
      )
    : '';
  const token = (await supabase?.auth.getSession())?.data.session?.access_token;
  const headers = {
    ...(body && { 'Content-Type': 'application/json' }),
    ...(token && { Authorization: `Bearer ${token}` }),
  };
  let response;
  try {
    response = await fetch(`${env.apiUrl}${path}${query}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, { code: 'network', message: 'Cannot reach the server. Is it running?' });
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, payload.error);
  return payload;
}

/**
 * One client for both listing types. Public list/detail omit contacts, budgets and prices;
 * `mine`, `create`, `update`, `setStatus` need a logged-in owner.
 * @param {'requirements'|'offerings'} table
 */
const listings = (table) => ({
  /** @param {{ category?: string, status?: string }} [params] */
  list: (params) => request(`/api/${table}`, { params }),
  mine: () => request(`/api/${table}/mine`),
  create: (data) => request(`/api/${table}`, { body: data }),
  update: (id, data) => request(`/api/${table}/${id}`, { method: 'PUT', body: data }),
  /** @param {'open'|'closed'|'active'|'inactive'} status */
  setStatus: (id, status) =>
    request(`/api/${table}/${id}/status`, { method: 'PATCH', body: { status } }),
});

export const api = {
  /** @returns {Promise<Meta>} */
  meta: () => request('/api/meta'),
  /** @returns {Promise<Summary>} */
  summary: () => request('/api/dashboard/summary'),
  /** @returns {Promise<{ category: string|null }>} category of the most similar listing */
  suggestCategory: (text) => request('/api/categories/suggest', { params: { text } }),

  requirements: listings('requirements'),
  offerings: listings('offerings'),

  /** @param {{ requirement_id?: string, offering_id?: string, status?: string, min_score?: number }} [params] @returns {Promise<Match[]>} */
  matches: (params) => request('/api/matches', { params }),
  /** @param {'accepted'|'rejected'} status @returns {Promise<Match>} */
  setMatchStatus: (id, status) =>
    request(`/api/matches/${id}/status`, { method: 'PATCH', body: { status } }),

  /** The logged-in user's notifications. @param {{ unread?: boolean }} [params] @returns {Promise<Notification[]>} */
  notifications: (params) => request('/api/notifications', { params }),
  /** @returns {Promise<Notification>} */
  markRead: (id) => request(`/api/notifications/${id}/read`, { method: 'POST' }),

  seed: () => request('/api/dev/seed', { method: 'POST' }),
  rematch: () => request('/api/dev/rematch', { method: 'POST' }),
  /** @returns {Promise<OutboxEmail[]>} */
  outbox: () => request('/api/dev/outbox'),
};
