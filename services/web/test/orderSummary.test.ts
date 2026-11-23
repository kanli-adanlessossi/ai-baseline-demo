import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatCents, parseOrderSummary, orderSummaryLine } from '../src/orderSummary.ts';
import type { Fetch } from '../src/http.ts';

const fakeFetch = (body: unknown, status = 200): Fetch =>
  (async () => new Response(JSON.stringify(body), { status })) as Fetch;

test('formatCents formats integer cents as currency', () => {
  assert.equal(formatCents(123456), '$1,234.56');
  assert.equal(formatCents(0), '$0.00');
});

test('formatCents rejects fractional cents', () => {
  assert.throws(() => formatCents(10.5), RangeError);
});

test('parseOrderSummary accepts a valid response', () => {
  assert.deepEqual(parseOrderSummary({ orderId: 'A1', totalCents: 500, itemCount: 2 }), {
    orderId: 'A1', totalCents: 500, itemCount: 2,
  });
});

test('parseOrderSummary rejects float amounts', () => {
  assert.throws(() => parseOrderSummary({ orderId: 'A1', totalCents: 5.0001, itemCount: 2 }), TypeError);
});

test('orderSummaryLine builds the display line', async () => {
  const line = await orderSummaryLine('https://orders.test', 'A1', fakeFetch({ orderId: 'A1', totalCents: 2599, itemCount: 1 }));
  assert.equal(line, 'Order A1: 1 item, $25.99');
});

test('orderSummaryLine surfaces HTTP errors', async () => {
  await assert.rejects(orderSummaryLine('https://orders.test', 'A1', fakeFetch({}, 503)), /status 503/);
});
