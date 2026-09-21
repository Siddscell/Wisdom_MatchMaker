const number = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
const date = new Intl.DateTimeFormat(undefined, {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

export const formatNumber = (value) => number.format(value);
export const formatDate = (iso) => date.format(new Date(iso));

/** Score bands from the spec: >= 85 strong, 70-84 good, 60-69 fair. */
export function scoreBand(score) {
  if (score >= 85) return 'strong';
  if (score >= 70) return 'good';
  return 'fair';
}
