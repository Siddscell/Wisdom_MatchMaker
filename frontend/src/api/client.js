/**
 * The frontend's only path to the backend. Shapes mirror backend/app/schemas.py.
 *
 * @typedef {{ categories: string[], units: string[],
 *   delivery_scopes: Record<string, number|null>,
 *   score_thresholds: { match_min: number, notify_min: number }, dev_mode: boolean }} Meta
 * @typedef {{ id: string, client_name: string, contact_email: string,
 *   product_requirement: string, category: string, quantity: number, unit: string,
 *   budget: number, location: string, needed_within_days: number, notes: string|null,
 *   status: 'open'|'closed', created_at: string }} Requirement
 * @typedef {{ id: string, supplier_name: string, contact_email: string,
 *   product_offered: string, category: string, available_quantity: number, unit: string,
 *   unit_price: number, pricing_notes: string|null, location: string, lead_time_days: number,
 *   delivery_scope: string, notes: string|null, status: 'active'|'inactive',
 *   created_at: string }} Offering
 * @typedef {{ id: string, requirement_id: string, offering_id: string, score: number,
 *   status: 'new'|'notified'|'accepted'|'rejected', created_at: string, updated_at: string,
 *   requirement_product: string, client_name: string, offering_product: string,
 *   supplier_name: string, client_email: string|null, supplier_email: string|null }} Match
 *   (emails are null until the match is accepted)
 * @typedef {{ id: string, match_id: string, recipient_role: 'client'|'supplier',
 *   recipient_email: string, message: string, is_read: boolean, created_at: string }} Notification
 * @typedef {{ total_requirements: number, total_offerings: number, total_matches: number,
 *   average_score: number|null, accepted_count: number,
 *   matches_by_status: Record<string, number> }} Summary
 * @typedef {{ id: string, to_email: string, subject: string, body: string,
 *   created_at: string, sent_at: string|null }} OutboxEmail
 */

import { env } from '../lib/env.js';

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
  let response;
  try {
    response = await fetch(`${env.apiUrl}${path}${query}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, { code: 'network', message: 'Cannot reach the server. Is it running?' });
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, payload.error);
  return payload;
}

export const api = {
  /** @returns {Promise<Meta>} */
  meta: () => request('/api/meta'),
  /** @returns {Promise<Summary>} */
  summary: () => request('/api/dashboard/summary'),

  /** @returns {Promise<Requirement>} */
  createRequirement: (data) => request('/api/requirements', { body: data }),
  /** @param {{ email?: string, category?: string, status?: string }} [params] @returns {Promise<Requirement[]>} */
  requirements: (params) => request('/api/requirements', { params }),

  /** @returns {Promise<Offering>} */
  createOffering: (data) => request('/api/offerings', { body: data }),
  /** @param {{ email?: string, category?: string, status?: string }} [params] @returns {Promise<Offering[]>} */
  offerings: (params) => request('/api/offerings', { params }),

  /** @param {{ requirement_id?: string, offering_id?: string, status?: string, min_score?: number }} [params] @returns {Promise<Match[]>} */
  matches: (params) => request('/api/matches', { params }),
  /** @param {'accepted'|'rejected'} status @returns {Promise<Match>} */
  setMatchStatus: (id, status) =>
    request(`/api/matches/${id}/status`, { method: 'PATCH', body: { status } }),

  /** @param {{ email?: string, unread?: boolean }} [params] @returns {Promise<Notification[]>} */
  notifications: (params) => request('/api/notifications', { params }),
  /** @returns {Promise<Notification>} */
  markRead: (id) => request(`/api/notifications/${id}/read`, { method: 'POST' }),

  seed: () => request('/api/dev/seed', { method: 'POST' }),
  rematch: () => request('/api/dev/rematch', { method: 'POST' }),
  /** @returns {Promise<OutboxEmail[]>} */
  outbox: () => request('/api/dev/outbox'),
};
