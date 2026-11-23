package com.example.orders;

/** One line of an order. Money is long cents (see services/orders/AGENTS.md). */
public record LineItem(String sku, long priceCents, int quantity) {

    public LineItem {
        if (sku == null || sku.isBlank()) {
            throw new IllegalArgumentException("sku must not be blank");
        }
        if (priceCents < 0) {
            throw new IllegalArgumentException("priceCents must not be negative");
        }
        if (quantity < 1) {
            throw new IllegalArgumentException("quantity must be at least 1");
        }
    }

    /** Price times quantity; throws ArithmeticException instead of overflowing. */
    public long lineTotalCents() {
        return Math.multiplyExact(priceCents, (long) quantity);
    }
}
