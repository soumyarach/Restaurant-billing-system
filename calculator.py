def compute_bill(items_with_qty, menu_lookup, discount_percent=0.0):
    itemized, subtotal, gst_total = {}, 0.0, 0.0
    for item, qty in items_with_qty.items():
        price = menu_lookup[item]['price']
        gst_rate = menu_lookup[item]['gst']
        amt = price * qty
        gst_amt = amt * gst_rate
        itemized[item] = {"qty": qty, "amount": amt, "gst": gst_amt}
        subtotal += amt
        gst_total += gst_amt
    discount = subtotal * (discount_percent / 100.0)
    taxable = subtotal - discount
    gst_total = gst_total * (taxable / subtotal) if subtotal > 0 else 0
    total = taxable + gst_total
    return {
        "itemized": itemized,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "gst_total": round(gst_total, 2),
        "total": round(total, 2)
    }
