package com.example.orders;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;

class OrderTotalsTest {

    @Test
    void sumsLineTotals() {
        var items = List.of(new LineItem("A", 1250, 2), new LineItem("B", 99, 1));
        assertEquals(2599, OrderTotals.totalCents(items));
        assertEquals(3, OrderTotals.itemCount(items));
    }

    @Test
    void emptyOrderTotalsZero() {
        assertEquals(0, OrderTotals.totalCents(List.of()));
    }

    @Test
    void rejectsNullItems() {
        assertThrows(IllegalArgumentException.class, () -> OrderTotals.totalCents(null));
        assertThrows(IllegalArgumentException.class,
                () -> OrderTotals.totalCents(Arrays.asList(new LineItem("A", 1, 1), null)));
    }

    @Test
    void rejectsInvalidLineItems() {
        assertThrows(IllegalArgumentException.class, () -> new LineItem("A", -1, 1));
        assertThrows(IllegalArgumentException.class, () -> new LineItem("A", 100, 0));
        assertThrows(IllegalArgumentException.class, () -> new LineItem(" ", 100, 1));
    }

    @Test
    void overflowThrowsInsteadOfWrapping() {
        var items = List.of(new LineItem("A", Long.MAX_VALUE, 2));
        assertThrows(ArithmeticException.class, () -> OrderTotals.totalCents(items));
    }
}
