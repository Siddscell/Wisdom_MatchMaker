import { z } from 'zod';

// Built from /api/meta so the allowed lists live only in the backend.
const text = (min, max) =>
  z
    .string()
    .trim()
    .min(min, min === 1 ? 'Required' : `At least ${min} characters`)
    .max(max, `At most ${max} characters`);
const optionalText = z.string().trim().max(2000, 'At most 2000 characters').optional();
const positive = z.coerce
  .number({ invalid_type_error: 'Enter a number' })
  .positive('Must be greater than 0');
const days = (min) =>
  z.coerce
    .number({ invalid_type_error: 'Enter a number' })
    .int('Whole days only')
    .min(min, min === 0 ? 'Cannot be negative' : 'At least 1 day')
    .max(3650, 'At most 3650 days');
const oneOf = (values, message) => z.string().refine((v) => values.includes(v), message);
const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const photo = z
  .any()
  .optional()
  .refine(
    (files) => !files?.[0] || files[0].size <= MAX_PHOTO_BYTES,
    'Photo must be 5 MB or smaller',
  )
  .refine(
    (files) => !files?.[0] || ['image/jpeg', 'image/png', 'image/webp'].includes(files[0].type),
    'Use a JPG, PNG or WebP photo',
  );

/** @param {import('../api/client.js').Meta} meta */
export function requirementSchema(meta) {
  return z.object({
    client_name: text(2, 200),
    product_requirement: text(2, 2000),
    category: oneOf(meta.categories, 'Choose a category'),
    quantity: positive,
    unit: oneOf(meta.units, 'Choose a unit'),
    budget: positive,
    location: text(2, 200),
    needed_within_days: days(1),
    notes: optionalText,
    photo,
  });
}

/** @param {import('../api/client.js').Meta} meta */
export function offeringSchema(meta) {
  return z.object({
    supplier_name: text(2, 200),
    product_offered: text(2, 2000),
    category: oneOf(meta.categories, 'Choose a category'),
    available_quantity: positive,
    unit: oneOf(meta.units, 'Choose a unit'),
    unit_price: positive,
    pricing_notes: optionalText,
    location: text(2, 200),
    lead_time_days: days(0),
    delivery_scope: oneOf(Object.keys(meta.delivery_scopes), 'Choose a delivery scope'),
    notes: optionalText,
    photo,
  });
}

/** react-hook-form resolver for a zod schema (what @hookform/resolvers does, in 8 lines). */
export const zodResolver = (schema) => async (values) => {
  const result = schema.safeParse(values);
  if (result.success) return { values: result.data, errors: {} };
  const errors = {};
  for (const issue of result.error.issues) {
    errors[issue.path[0]] ??= { type: issue.code, message: issue.message };
  }
  return { values: {}, errors };
};
