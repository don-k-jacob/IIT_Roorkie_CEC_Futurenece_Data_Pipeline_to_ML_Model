"""Part 0 - profile the NammaMart CSV exports before writing any pipeline code.

Standard library only, so it runs anywhere:
    python3 include/profiling/profile_nammamart.py > include/profiling/data_profile.md

Prints a Markdown report: generic profile per file (row counts, nulls, duplicates,
min/max, distinct values) followed by referential-integrity and business-rule checks.
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "nammamart"
AS_OF = datetime(2026, 10, 1)  # the dataset covers Sept 2026; the next-day file is 1 Oct

NULL_TOKENS = {"", "null", "none", "nan", "n/a", "na", "-"}
VALID_STATUS = {"DELIVERED", "CANCELLED", "RETURNED"}
VALID_PAYMENT_MODE = {"UPI", "Card", "Cash on Delivery", "Wallet"}
TS_FMT = "%Y-%m-%d %H:%M:%S"
DATE_FMT = "%Y-%m-%d"

FILES = {
    "orders": ("orders.csv", "order_id"),
    "payments": ("payments.csv", "payment_id"),
    "customers": ("customers.csv", "customer_id"),
    "products": ("products.csv", "product_id"),
    "stores": ("stores.csv", "store_id"),
    "increment": ("orders_2026-10-01_increment.csv", "order_id"),
}
NUMERIC = {
    "orders": ["quantity", "unit_price", "discount_pct", "order_amount", "delivery_minutes"],
    "increment": ["quantity", "unit_price", "discount_pct", "order_amount", "delivery_minutes"],
    "payments": ["amount_paid"],
    "products": ["mrp", "cost_price"],
    "stores": ["capacity_orders_per_day"],
}
DATES = {
    "orders": {"order_ts": TS_FMT},
    "increment": {"order_ts": TS_FMT},
    "payments": {"payment_ts": TS_FMT},
    "customers": {"signup_date": DATE_FMT},
    "products": {"launch_date": DATE_FMT},
    "stores": {"open_date": DATE_FMT},
}
CATEGORICAL = {
    "orders": ["payment_mode", "order_status", "channel", "store_id"],
    "increment": ["payment_mode", "order_status", "channel"],
    "payments": ["payment_mode", "payment_status"],
    "customers": ["city", "area", "loyalty_tier", "is_active"],
    "products": ["category", "sub_category", "brand", "unit", "is_perishable"],
    "stores": ["zone", "area"],
}


def load(name):
    filename, _ = FILES[name]
    with open(DATA_DIR / filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_null(v):
    return v is None or v.strip().lower() in NULL_TOKENS


def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def to_dt(v, fmt):
    try:
        return datetime.strptime(v.strip(), fmt)
    except (AttributeError, ValueError):
        return None


def show(keys, limit=12):
    keys = list(keys)
    more = f" … (+{len(keys) - limit} more)" if len(keys) > limit else ""
    return ", ".join(str(k) for k in keys[:limit]) + more


def finding(title, keys, note=""):
    keys = list(keys)
    status = "✅ 0" if not keys else f"❌ {len(keys)}"
    line = f"- **{title}**: {status}"
    if keys:
        line += f" — {show(keys)}"
    if note:
        line += f"  \n  _{note}_"
    print(line)


def profile_file(name, rows):
    filename, key = FILES[name]
    cols = list(rows[0].keys())
    print(f"\n## {filename}\n")
    print(f"Rows: **{len(rows)}** · Columns: **{len(cols)}** · Key: `{key}`\n")

    print("| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |")
    print("|---|---|---|---|---|---|---|")
    for c in cols:
        vals = [r[c] for r in rows]
        nulls = sum(is_null(v) for v in vals)
        untrimmed = sum(1 for v in vals if v and v != v.strip())
        distinct = len(set(vals))
        mn = mx = bad = ""
        if c in NUMERIC.get(name, []):
            nums = [to_float(v) for v in vals if not is_null(v)]
            bad = sum(n is None for n in nums)
            nums = [n for n in nums if n is not None]
            mn, mx = (min(nums), max(nums)) if nums else ("", "")
        elif c in DATES.get(name, {}):
            fmt = DATES[name][c]
            dts = [to_dt(v, fmt) for v in vals if not is_null(v)]
            bad = sum(d is None for d in dts)
            dts = [d for d in dts if d is not None]
            mn, mx = (min(dts), max(dts)) if dts else ("", "")
        print(f"| {c} | {nulls} | {untrimmed} | {distinct} | {mn} | {mx} | {bad} |")

    ids = Counter(r[key] for r in rows)
    dup_ids = [k for k, n in ids.items() if n > 1]
    full = Counter(tuple(r.values()) for r in rows)
    exact_dupes = sum(n - 1 for n in full.values() if n > 1)
    print(f"\nDuplicate `{key}` values: **{len(dup_ids)}** "
          f"({sum(ids[k] for k in dup_ids)} rows){': ' + show(dup_ids) if dup_ids else ''}  ")
    print(f"Exact duplicate rows (every column identical): **{exact_dupes}**\n")

    for c in CATEGORICAL.get(name, []):
        counts = Counter(repr(r[c]) if r[c] != r[c].strip() or r[c] == "" else r[c] for r in rows)
        print(f"- `{c}` distinct values: " + ", ".join(f"{v} ({n})" for v, n in counts.most_common()))


def bad_dates(rows, key, col, fmt, lo=None, hi=None):
    out = []
    for r in rows:
        if is_null(r[col]):
            continue
        d = to_dt(r[col], fmt)
        if d is None:
            out.append(f"{r[key]}={r[col]!r}")
        elif (lo and d < lo) or (hi and d > hi):
            out.append(f"{r[key]}={r[col]}")
    return out


def check_orders(name, orders, customers, products, stores):
    print(f"\n### Rule checks — {FILES[name][0]}\n")
    cust_ids = {r["customer_id"].strip() for r in customers}
    prod_ids = {r["product_id"].strip() for r in products}
    store_ids = {r["store_id"].strip() for r in stores}
    test_pat = re.compile(r"test|dummy|demo", re.I)

    finding("customer_id null", [r["order_id"] for r in orders if is_null(r["customer_id"])])
    finding("customer_id not in customers.csv",
            [f"{r['order_id']}→{r['customer_id']}" for r in orders
             if not is_null(r["customer_id"]) and r["customer_id"].strip() not in cust_ids])
    finding("product_id not in products.csv",
            [f"{r['order_id']}→{r['product_id']}" for r in orders if r["product_id"].strip() not in prod_ids])
    finding("store_id not in stores.csv",
            [f"{r['order_id']}→{r['store_id']}" for r in orders if r["store_id"].strip() not in store_ids])
    finding("order_ts null/blank/N/A", [f"{r['order_id']}={r['order_ts']!r}" for r in orders if is_null(r["order_ts"])])
    finding("order_ts not in YYYY-MM-DD HH:MM:SS or not a real date",
            [f"{r['order_id']}={r['order_ts']!r}" for r in orders
             if not is_null(r["order_ts"]) and to_dt(r["order_ts"], TS_FMT) is None])
    finding("order_ts in the future (after 1 Oct 2026)",
            [f"{r['order_id']}={r['order_ts']}" for r in orders
             if to_dt(r["order_ts"], TS_FMT) and to_dt(r["order_ts"], TS_FMT) >= datetime(2026, 10, 2)])

    qty = [(r["order_id"], to_float(r["quantity"])) for r in orders]
    finding("quantity ≤ 0 or not a number", [f"{k}={q}" for k, q in qty if q is None or q <= 0])
    finding("quantity not a whole number", [f"{k}={q}" for k, q in qty if q is not None and q != int(q)])
    finding("quantity > 20 (suspiciously large for q-commerce)", [f"{k}={q}" for k, q in qty if q and q > 20])
    finding("unit_price ≤ 0 or not a number",
            [f"{r['order_id']}={r['unit_price']}" for r in orders
             if to_float(r["unit_price"]) is None or to_float(r["unit_price"]) <= 0])
    finding("discount_pct outside 0–100",
            [f"{r['order_id']}={r['discount_pct']}" for r in orders
             if to_float(r["discount_pct"]) is None or not 0 <= to_float(r["discount_pct"]) <= 100])

    # current MRP = the product row not tagged "(old)"
    mrp = {r["product_id"].strip(): to_float(r["mrp"]) for r in products if "(old)" not in r["product_name"]}
    finding("unit_price ≠ current product MRP",
            [f"{r['order_id']} {r['product_id']} price={r['unit_price']} mrp={mrp.get(r['product_id'])}"
             for r in orders if to_float(r["unit_price"]) and (mrp.get(r["product_id"]) or 0) > 0
             and abs(to_float(r["unit_price"]) - mrp[r["product_id"]]) > 0.01],
            "Distribution check: in clean data every order is sold at MRP")
    finding("Ordered product has a negative MRP in products.csv",
            [f"{r['order_id']} {r['product_id']}" for r in orders
             if mrp.get(r["product_id"]) is not None and mrp[r["product_id"]] <= 0])

    patterns = defaultdict(list)
    for r in orders:
        q, p, d, a = (to_float(r[c]) for c in ("quantity", "unit_price", "discount_pct", "order_amount"))
        if None in (q, p, d, a):
            continue
        expected = round(q * p * (1 - d / 100), 2)
        if abs(expected - a) <= 0.01:
            continue
        if not 0 <= d <= 100:
            kind = "discount_pct > 100, amount ignores discount"
        elif expected and abs(a / expected - 10) < 0.01:
            kind = "10× too high (decimal shift)"
        else:
            kind = f"{a / expected:.1f}× expected" if expected else "expected 0"
        patterns[kind].append(f"{r['order_id']} exp={expected} got={a}")
    finding("order_amount ≠ quantity × unit_price × (1 − discount/100)",
            [k for v in patterns.values() for k in v],
            "; ".join(f"{k}: {len(v)}" for k, v in patterns.items()))

    finding("payment_mode not exactly in allowed list",
            [f"{r['order_id']}={r['payment_mode']!r}" for r in orders if r["payment_mode"] not in VALID_PAYMENT_MODE])
    finding("order_status not exactly in allowed list",
            [f"{r['order_id']}={r['order_status']!r}" for r in orders if r["order_status"] not in VALID_STATUS])

    delivered = [r for r in orders if r["order_status"].strip().upper() == "DELIVERED"]
    finding("DELIVERED with no delivery_minutes", [r["order_id"] for r in delivered if is_null(r["delivery_minutes"])])
    dm = [(r["order_id"], r["order_status"], to_float(r["delivery_minutes"])) for r in orders
          if not is_null(r["delivery_minutes"])]
    finding("delivery_minutes ≥ 120 (hours, not minutes)", [f"{k}={m}" for k, s, m in dm if m is not None and m >= 120])
    finding("delivery_minutes ≤ 0", [f"{k}={m}" for k, s, m in dm if m is not None and m <= 0])
    finding("delivery_minutes outside normal 8–35 (but < 120)",
            [f"{k}={m}" for k, s, m in dm if m is not None and (0 < m < 8 or 35 < m < 120)],
            "Warning-level: possible but unusual")
    finding("CANCELLED order with a delivery_minutes value",
            [f"{k}={m}" for k, s, m in dm if s.strip().upper() == "CANCELLED"])

    finding("Looks like a test entry (test/dummy/demo in any field)",
            [r["order_id"] for r in orders if any(test_pat.search(v or "") for v in r.values())])

    # duplicate orders that differ only by order_id (same customer, product, timestamp)
    sig = defaultdict(list)
    for r in orders:
        sig[(r["order_ts"], r["customer_id"], r["product_id"], r["quantity"])].append(r["order_id"])
    finding("Same customer+product+timestamp+qty under different order_ids",
            ["/".join(v) for v in sig.values() if len(set(v)) > 1])


def check_payments(payments, orders):
    print("\n### Rule checks — payments.csv\n")
    order_by_id = {}
    for r in orders:
        order_by_id.setdefault(r["order_id"], r)
    pays_per_order = Counter(r["order_id"] for r in payments)

    orphans = [r for r in payments if r["order_id"] not in order_by_id]
    finding("order_id not in orders.csv", [f"{r['payment_id']}→{r['order_id']}" for r in orphans],
            f"payment_ts values: {sorted({r['payment_ts'] for r in orphans})}; "
            f"total ₹{sum(to_float(r['amount_paid']) or 0 for r in orphans):,.2f}" if orphans else "")
    finding("More than one payment row for an order",
            [f"{k}×{n}" for k, n in pays_per_order.items() if n > 1])
    finding("payment_ts in the future (after 1 Oct 2026)",
            [f"{r['payment_id']}={r['payment_ts']}" for r in payments
             if to_dt(r["payment_ts"], TS_FMT) and to_dt(r["payment_ts"], TS_FMT) >= datetime(2026, 10, 2)])
    finding("payment_mode not exactly in allowed list",
            [f"{r['payment_id']}={r['payment_mode']!r}" for r in payments if r["payment_mode"] not in VALID_PAYMENT_MODE])
    finding("amount_paid ≤ 0 or not a number",
            [f"{r['payment_id']}={r['amount_paid']}" for r in payments
             if to_float(r["amount_paid"]) is None or to_float(r["amount_paid"]) <= 0])

    amt_mismatch, mode_mismatch, before_order, on_cancelled = [], [], [], []
    for r in payments:
        o = order_by_id.get(r["order_id"])
        if not o:
            continue
        paid, due = to_float(r["amount_paid"]), to_float(o["order_amount"])
        if r["payment_status"].strip().upper() == "SUCCESS" and paid is not None and due is not None \
                and abs(paid - due) > 0.01:
            amt_mismatch.append(f"{r['payment_id']}/{r['order_id']} paid={paid} due={due} short={due - paid:.2f}")
        if r["payment_mode"].strip().lower() != o["payment_mode"].strip().lower():
            mode_mismatch.append(f"{r['order_id']} order={o['payment_mode']!r} pay={r['payment_mode']!r}")
        pt, ot = to_dt(r["payment_ts"], TS_FMT), to_dt(o["order_ts"], TS_FMT)
        if pt and ot and pt < ot:
            before_order.append(f"{r['payment_id']} pay={pt} order={ot}")
        if o["order_status"].strip().upper() == "CANCELLED":
            on_cancelled.append(f"{r['payment_id']}→{r['order_id']} ({r['payment_status']})")
    finding("SUCCESS payment amount ≠ order_amount", amt_mismatch)
    finding("payment_mode differs from the order's payment_mode", mode_mismatch)
    finding("payment_ts earlier than order_ts", before_order)
    finding("Payment exists for a CANCELLED order", on_cancelled)

    statuses = defaultdict(set)
    for r in payments:
        statuses[r["order_id"]].add(r["payment_status"].strip().upper())
    cross = Counter((o["order_status"], "/".join(sorted(statuses.get(k, {"NO PAYMENT"}))))
                    for k, o in order_by_id.items())
    print("\norder_status × payment_status:\n")
    print("| order_status | payment_status | orders |\n|---|---|---|")
    for (os_, ps), n in sorted(cross.items()):
        print(f"| {os_} | {ps} | {n} |")
    print()
    finding("DELIVERED order whose only payment FAILED",
            [k for k, o in order_by_id.items()
             if o["order_status"].strip().upper() == "DELIVERED" and statuses.get(k) == {"FAILED"}],
            "Revenue counted with no money collected")
    finding("RETURNED order not REFUNDED",
            [k for k, o in order_by_id.items()
             if o["order_status"].strip().upper() == "RETURNED" and statuses.get(k) != {"REFUNDED"}])
    finding("gateway_ref blank on a non-cash payment",
            [f"{r['payment_id']} ({r['payment_mode']})" for r in payments
             if is_null(r["gateway_ref"]) and r["payment_mode"] != "Cash on Delivery"],
            f"{sum(is_null(r['gateway_ref']) for r in payments)} blank refs in total; "
            "Cash on Delivery never goes through the gateway, so blanks there are expected")
    finding("Duplicate gateway_ref", [k for k, n in Counter(r["gateway_ref"] for r in payments
                                                           if not is_null(r["gateway_ref"])).items() if n > 1])
    paid_orders = {r["order_id"] for r in payments}
    finding("DELIVERED/RETURNED order with no payment row",
            [k for k, o in order_by_id.items()
             if o["order_status"].strip().upper() in ("DELIVERED", "RETURNED") and k not in paid_orders])


def check_customers(customers):
    print("\n### Rule checks — customers.csv\n")
    email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
    finding("Same customer_id with different details",
            [k for k, rs in group(customers, "customer_id").items()
             if len(rs) > 1 and len({tuple(r.values()) for r in rs}) > 1])
    finding("full_name blank", [r["customer_id"] for r in customers if is_null(r["full_name"])])
    # PII: report customer IDs only, never the raw email or phone
    finding("email invalid format", [r["customer_id"] for r in customers
                                     if not is_null(r["email"]) and not email_re.match(r["email"].strip())])
    finding("email blank or N/A", [f"{r['customer_id']}={r['email']!r}" for r in customers if is_null(r["email"])])
    finding("Same email on different customer_ids",
            [k for k, rs in group(customers, "email").items()
             if not is_null(k) and len({r["customer_id"] for r in rs}) > 1])
    finding("phone not exactly 10 digits", [f"{r['customer_id']} ({len(r['phone'].strip())} digits)" for r in customers
                                            if not re.fullmatch(r"\d{10}", r["phone"].strip())])
    finding("phone not starting 6–9 (Indian mobile)", [r["customer_id"] for r in customers
                                                       if re.fullmatch(r"\d{10}", r["phone"]) and r["phone"][0] not in "6789"])
    finding("pincode not exactly 6 digits", [f"{r['customer_id']}={r['pincode']!r}" for r in customers
                                             if not re.fullmatch(r"\d{6}", r["pincode"].strip())])
    finding("pincode not a Bengaluru 560xxx code", [f"{r['customer_id']}={r['pincode']}" for r in customers
                                                    if re.fullmatch(r"\d{6}", r["pincode"]) and not r["pincode"].startswith("560")])
    finding("city blank", [r["customer_id"] for r in customers if is_null(r["city"])])
    finding("signup_date unparseable or in the future",
            bad_dates(customers, "customer_id", "signup_date", DATE_FMT, hi=AS_OF))
    finding("loyalty_tier not one of Bronze/Silver/Gold/Platinum (casing)",
            [f"{r['customer_id']}={r['loyalty_tier']!r}" for r in customers
             if r["loyalty_tier"] not in {"Bronze", "Silver", "Gold", "Platinum"}])


def check_products(products):
    print("\n### Rule checks — products.csv\n")
    finding("Same product_id with different details",
            [k for k, rs in group(products, "product_id").items()
             if len(rs) > 1 and len({tuple(r.values()) for r in rs}) > 1])
    finding("category blank", [r["product_id"] for r in products if is_null(r["category"])])
    finding("mrp ≤ 0 or not a number", [f"{r['product_id']}={r['mrp']}" for r in products
                                        if to_float(r["mrp"]) is None or to_float(r["mrp"]) <= 0])
    finding("cost_price ≤ 0 or not a number", [f"{r['product_id']}={r['cost_price']}" for r in products
                                               if to_float(r["cost_price"]) is None or to_float(r["cost_price"]) <= 0])
    finding("cost_price > mrp (sold at a loss)",
            [f"{r['product_id']} cost={r['cost_price']} mrp={r['mrp']}" for r in products
             if to_float(r["cost_price"]) and to_float(r["mrp"]) and to_float(r["cost_price"]) > to_float(r["mrp"])])
    finding("launch_date unparseable or in the future",
            bad_dates(products, "product_id", "launch_date", DATE_FMT, hi=AS_OF))
    finding("Same product_name on different product_ids",
            [k for k, rs in group(products, "product_name").items() if len({r["product_id"] for r in rs}) > 1])


def check_stores(stores):
    print("\n### Rule checks — stores.csv\n")
    finding("zone blank", [r["store_id"] for r in stores if is_null(r["zone"])])
    finding("capacity_orders_per_day ≤ 0", [f"{r['store_id']}={r['capacity_orders_per_day']}" for r in stores
                                            if (to_float(r["capacity_orders_per_day"]) or 0) <= 0])
    finding("pincode not exactly 6 digits", [f"{r['store_id']}={r['pincode']!r}" for r in stores
                                             if not re.fullmatch(r"\d{6}", r["pincode"].strip())])
    finding("open_date unparseable or in the future",
            bad_dates(stores, "store_id", "open_date", DATE_FMT, hi=AS_OF))
    finding("manager_name blank", [r["store_id"] for r in stores if is_null(r["manager_name"])])


def check_cross_file(orders, customers, stores):
    print("\n### Cross-file checks\n")
    signup = {r["customer_id"]: to_dt(r["signup_date"], DATE_FMT) for r in customers}
    finding("Order placed before the customer signed up",
            [f"{r['order_id']} {r['customer_id']} order={r['order_ts'][:10]} signup={signup[r['customer_id']].date()}"
             for r in orders if signup.get(r["customer_id"]) and to_dt(r["order_ts"], TS_FMT)
             and to_dt(r["order_ts"], TS_FMT) < signup[r["customer_id"]]])
    inactive = {r["customer_id"] for r in customers if r["is_active"] == "N"}
    finding("Orders from customers marked is_active = N",
            [r["order_id"] for r in orders if r["customer_id"] in inactive],
            "Probably fine (customer churned after ordering); confirm what is_active means")
    store_pin = {r["area"]: r["pincode"] for r in stores}
    finding("Customer pincode doesn't match the area's pincode",
            [f"{r['customer_id']} {r['area']} {r['pincode']}" for r in customers
             if store_pin.get(r["area"]) and r["pincode"] != store_pin[r["area"]]])
    open_date = {r["store_id"]: to_dt(r["open_date"], DATE_FMT) for r in stores}
    finding("Order placed before its store opened",
            [f"{r['order_id']} {r['store_id']} order={r['order_ts'][:10]} opened={open_date[r['store_id']].date()}"
             for r in orders if open_date.get(r["store_id"]) and to_dt(r["order_ts"], TS_FMT)
             and to_dt(r["order_ts"], TS_FMT) < open_date[r["store_id"]]])
    cap = {r["store_id"]: to_float(r["capacity_orders_per_day"]) for r in stores}
    daily = Counter((r["store_id"], r["order_ts"][:10]) for r in orders)
    finding("Store-days over capacity_orders_per_day",
            [f"{s} {d}: {n}>{cap[s]}" for (s, d), n in daily.items() if cap.get(s) is not None and n > cap[s]])


def check_increment(increment, orders):
    print("\n### Incremental file vs orders.csv\n")
    old = {r["order_id"]: r for r in orders}
    corrections = [r for r in increment if r["order_id"] in old]
    new = [r for r in increment if r["order_id"] not in old]
    print(f"- Existing order_ids (corrections): **{len(corrections)}** · new order_ids: **{len(new)}**")
    changes = []
    for r in corrections:
        diff = [f"{c}: {old[r['order_id']][c]!r}→{r[c]!r}" for c in r if r[c] != old[r["order_id"]][c]]
        changes.append(f"{r['order_id']} ({'; '.join(diff) or 'no change'})")
    print("- Corrections:\n" + "\n".join(f"  - {c}" for c in changes))
    ts = [to_dt(r["order_ts"], TS_FMT) for r in new]
    ts = [t for t in ts if t]
    if ts:
        print(f"- New orders span {min(ts)} → {max(ts)}")


def group(rows, col):
    g = defaultdict(list)
    for r in rows:
        g[r[col].strip()].append(r)
    return g


def main():
    data = {name: load(name) for name in FILES}
    print("# NammaMart data profile\n")
    print(f"Source: `{DATA_DIR.relative_to(Path.cwd()) if DATA_DIR.is_relative_to(Path.cwd()) else DATA_DIR}` · "
          f"reference date for timeliness checks: {AS_OF.date()}\n")
    print("| File | Rows |\n|---|---|")
    for name, (filename, _) in FILES.items():
        print(f"| {filename} | {len(data[name])} |")
    print(f"| **Total** | **{sum(len(v) for v in data.values())}** |")

    for name in FILES:
        profile_file(name, data[name])

    print("\n---\n\n# Rule and integrity checks")
    check_orders("orders", data["orders"], data["customers"], data["products"], data["stores"])
    check_payments(data["payments"], data["orders"])
    check_customers(data["customers"])
    check_products(data["products"])
    check_stores(data["stores"])
    check_cross_file(data["orders"], data["customers"], data["stores"])
    check_orders("increment", data["increment"], data["customers"], data["products"], data["stores"])
    check_increment(data["increment"], data["orders"])


if __name__ == "__main__":
    sys.exit(main())
