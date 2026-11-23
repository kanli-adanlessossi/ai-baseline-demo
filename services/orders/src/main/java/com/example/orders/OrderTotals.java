package com.example.orders;

import java.util.List;

/** Order total calculations. */
public final class OrderTotals {

    private OrderTotals() {
    }

    /** Sum of all line totals in cents. An empty order totals zero. */
    public static long totalCents(List<LineItem> items) {
        if (items == null) {
            throw new IllegalArgumentException("items must not be null");
        }
        long total = 0;
        for (LineItem item : items) {
            if (item == null) {
                throw new IllegalArgumentException("items must not contain null");
            }
            total = Math.addExact(total, item.lineTotalCents());
        }
        return total;
    }

    /** Total item count across all lines. */
    public static int itemCount(List<LineItem> items) {
        if (items == null) {
            throw new IllegalArgumentException("items must not be null");
        }
        return items.stream().mapToInt(LineItem::quantity).reduce(0, Math::addExact);
    }
}
