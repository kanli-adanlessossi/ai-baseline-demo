import { getJson, type Fetch } from './http.ts';

export interface OrderSummary {
  orderId: string;
  totalCents: number;
  itemCount: number;
}

/** Format integer cents for display, e.g. 123456 -> "$1,234.56". */
export function formatCents(cents: number, currency = 'USD', locale = 'en-US'): string {
  if (!Number.isSafeInteger(cents)) throw new RangeError('cents must be an integer');
  return new Intl.NumberFormat(locale, { style: 'currency', currency }).format(cents / 100);
}

/** Narrow an unknown API response to an OrderSummary, or throw. */
export function parseOrderSummary(data: unknown): OrderSummary {
  if (typeof data !== 'object' || data === null) throw new TypeError('order summary must be an object');
  const { orderId, totalCents, itemCount } = data as Record<string, unknown>;
  if (typeof orderId !== 'string' || orderId === '') throw new TypeError('orderId must be a non-empty string');
  if (typeof totalCents !== 'number' || !Number.isSafeInteger(totalCents) || totalCents < 0)
    throw new TypeError('totalCents must be a non-negative integer');
  if (typeof itemCount !== 'number' || !Number.isSafeInteger(itemCount) || itemCount < 0)
    throw new TypeError('itemCount must be a non-negative integer');
  return { orderId, totalCents, itemCount };
}

/** Fetch an order from the orders service and return the line shown on the page. */
export async function orderSummaryLine(baseUrl: string, orderId: string, fetchImpl?: Fetch): Promise<string> {
  const summary = parseOrderSummary(await getJson(`${baseUrl}/orders/${encodeURIComponent(orderId)}`, fetchImpl));
  const items = summary.itemCount === 1 ? '1 item' : `${summary.itemCount} items`;
  return `Order ${summary.orderId}: ${items}, ${formatCents(summary.totalCents)}`;
}
