import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple
from sqlmodel import Session, select
from .models import Product, Customer, Bill, BillItem

TWOPLACES = Decimal("0.01")

def _round(x: Decimal) -> Decimal:
    return x.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

def compute_change_with_limited_denominations(change: Decimal, drawer_counts: Dict[int,int]) -> Tuple[Dict[int,int], Decimal]:
    """
    change: Decimal rupees (e.g. 237.00)
    drawer_counts: {2000:2, 500:3, ...} where counts are ints
    returns (distribution dict, remainder Decimal)
    """
    remaining_paise = int((change * 100).to_integral_value())
    denom_list = sorted(drawer_counts.keys(), reverse=True)
    dist: Dict[int,int] = {}
    for d in denom_list:
        if remaining_paise <= 0:
            dist[d] = 0
            continue
        unit = d * 100
        need = remaining_paise // unit
        take = min(need, drawer_counts.get(d, 0))
        dist[d] = int(take)
        remaining_paise -= take * unit
    remainder = Decimal(remaining_paise) / Decimal(100)
    return dist, _round(remainder)

def compute_bill(session: Session, req) -> dict:
    total_without_tax = Decimal("0")
    total_tax = Decimal("0")
    items_out = []

    cust = session.query(Customer).filter(Customer.email == req.customer_email).first()
    if not cust:
        cust = Customer(email=req.customer_email)
        session.add(cust)
        session.commit()
        session.refresh(cust)

    for it in req.items:
        prod = session.query(Product).filter(Product.product_id == it.product_code).first()
        if not prod:
            raise ValueError(f"Product {it.product_code} not found")
        if it.quantity > prod.available_stocks:
            raise ValueError(f"Insufficient stock for {prod.product_id}")
        unit_price = Decimal(prod.price)
        qty = int(it.quantity)
        line_total = _round(unit_price * qty)
        tax = _round(line_total * Decimal(prod.tax_percentage) / Decimal(100))
        total_without_tax += line_total
        total_tax += tax
        items_out.append({
            "product": prod,
            "quantity": qty,
            "unit_price": _round(unit_price),
            "line_total": line_total,
            "tax": tax
        })

    total_with_tax = _round(total_without_tax + total_tax)
    paid_amount = _round(req.paid_amount)
    change_to_give = _round(max(Decimal("0"), paid_amount - total_with_tax))

    drawer = {d.value: d.count for d in req.denominations} if hasattr(req, "denominations") else {}
    change_dist, remainder = compute_change_with_limited_denominations(change_to_give, drawer)

    bill = Bill(
        customer_id=cust.id,
        total_without_tax=_round(total_without_tax),
        total_tax=_round(total_tax),
        total_with_tax=_round(total_with_tax),
        paid_amount=paid_amount,
        change_given=_round(change_to_give - remainder),
        change_json=json.dumps({str(k): int(v) for k,v in change_dist.items()})
    )
    session.add(bill)
    session.commit()
    session.refresh(bill)

    for itm in items_out:
        bi = BillItem(
            bill_id=bill.id,
            product_id=itm["product"].id,
            quantity=itm["quantity"],
            unit_price=itm["unit_price"],
            tax_percentage=itm["product"].tax_percentage,
            line_total=itm["line_total"]
        )
        session.add(bi)
        itm["product"].available_stocks = int(itm["product"].available_stocks) - itm["quantity"]
        session.add(itm["product"])
    session.commit()

    items_serializable = []
    for itm in items_out:
        tax_pct = itm["product"].tax_percentage if hasattr(itm["product"], "tax_percentage") else getattr(itm["product"], "tax_percentage", 0)
        items_serializable.append({
            "product_id": itm["product"].product_id,
            "product_name": itm["product"].name,
            "quantity": itm["quantity"],
            "unit_price": format(itm["unit_price"], ".2f"),
            "tax_percentage": format(tax_pct, ".2f"),
            "tax": format(itm["tax"], ".2f"),
            "line_total": format(itm["line_total"], ".2f")
        })

    return {
        "bill": bill,
        "items": items_serializable,
        "change_distribution": {str(k): int(v) for k,v in change_dist.items()},
        "remainder_unreturned": remainder
    }

def get_bill_details(session: Session, bill_id: int):
    bill = session.get(Bill, bill_id)
    if not bill:
        return None

    stmt = select(BillItem).where(BillItem.bill_id == bill_id)
    items = session.exec(stmt).all()

    items_prepared = []
    for it in items:
        prod = session.get(Product, it.product_id)
        items_prepared.append({
            "product": prod,
            "product_name": prod.name if prod else None,
            "product_id": getattr(prod, "product_id", None),
            "quantity": it.quantity,
            "unit_price": format(it.unit_price, ".2f") if it.unit_price is not None else "0.00",
            "tax_percentage": format(it.tax_percentage, ".2f") if it.tax_percentage is not None else "0.00",
            "line_total": format(it.line_total, ".2f") if it.line_total is not None else "0.00",
            "tax": format((Decimal(it.line_total) * Decimal(it.tax_percentage) / Decimal(100)) if (it.line_total and it.tax_percentage) else Decimal("0.00"), ".2f")
        })

    change_distribution = {}
    if bill.change_json:
        try:
            change_distribution = json.loads(bill.change_json)
        except Exception:
            change_distribution = {}
    else:
        for d in [2000,500,200,100,50,20,10,5,2,1]:
            change_distribution[str(d)] = 0

    bill_prepared = {
        "id": bill.id,
        "customer_id": bill.customer_id,
        "created_at": bill.created_at,
        "total_without_tax": format(bill.total_without_tax, ".2f"),
        "total_tax": format(bill.total_tax, ".2f"),
        "total_with_tax": format(bill.total_with_tax, ".2f"),
        "paid_amount": format(bill.paid_amount, ".2f"),
        "change_given": format(bill.change_given, ".2f")
    }

    return bill_prepared, items_prepared, change_distribution