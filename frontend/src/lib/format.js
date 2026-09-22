const number = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });
const rupees = (digits) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
const wholeRupees = rupees(0);
const rupeesAndPaise = rupees(2);
const date = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

export const formatNumber = (value) => number.format(value);
/** ₹ with Indian digit grouping: ₹1,50,000 and ₹68.50 */
export const formatINR = (value) =>
  (Number.isInteger(value) ? wholeRupees : rupeesAndPaise).format(value);
export const formatDate = (iso) => date.format(new Date(iso));

/** Score bands from the spec: >= 85 strong, 70-84 good, 60-69 fair. */
export function scoreBand(score) {
  if (score >= 85) return 'strong';
  if (score >= 70) return 'good';
  return 'fair';
}
