"""
golden.py — the hand-written golden set: business questions + the record ids each one needs.

    one row = (qid, question, type, must_find, helpful, example_ok, limits, behaviour, assumption, why)

    must_find   ids the LLM cannot do without — grade 2. Missing one = wrong or unsafe SQL.
    helpful     ids that make the answer better — grade 1.
    example_ok  nlq_examples ids; ANY ONE of them counts as "a proven query was found".
    limits      capability_card ids the answer depends on (1 = what it answers, 2 = what it can't, 3 = rules).
    behaviour   answer · answer + state assumption · refuse

Does NOT contain questions copied from nlq_examples, paraphrases or answers_questions — those are embedded or
used elsewhere. Business words such as GMV are allowed: users really type them (type = jargon).
"""

C = "column::ecom."
G = "glossary::"
J = "join::ecom."
X = "nlq_examples::"
CAP = "capability_card::"

GOLDEN = [
    # ── A · jargon: the word appears only in glossary synonyms ────────────────────────────────────
    ("G01", "What was our GMV last month?", "jargon",
     [G + "Revenue", C + "orders.total_amount"], [C + "orders.order_date"], [X + "1"], [CAP + "2", CAP + "3"],
     "answer + state assumption", "latest full month in the data = November 2024; merchandise only",
     "GMV appears only in the Revenue synonyms; 'last month' has no data today"),
    ("G02", "What's our AOV on mobile versus desktop?", "jargon",
     [G + "Average Order Value", C + "orders.total_amount", C + "orders.device_type"], [C + "orders.order_id"], [X + "4"], [],
     "answer", "", "abbreviation AOV; the device column is never named"),
    ("G03", "What is our OTD by carrier?", "jargon",
     [G + "On-Time Delivery Rate", C + "shipments.on_time", C + "shipments.carrier"], [C + "shipments.status"], [X + "37"], [CAP + "3"],
     "answer", "Delivered shipments only", "abbreviation OTD; rule changes the WHERE clause"),
    ("G04", "Who are our highest-CLV customers?", "jargon",
     [G + "Lifetime Value", C + "customers.lifetime_revenue"], [], [X + "20"], [],
     "answer", "", "CLV is a synonym of Lifetime Value"),
    ("G05", "Which products have an MOQ of 50 units or more?", "jargon",
     [G + "Minimum Order Quantity", C + "product_suppliers.minimum_order_quantity"], [J + "product_suppliers->ecom.products::product_id"], [], [],
     "answer", "", "abbreviation MOQ; no example covers it"),
    ("G06", "Is our decline rate higher with some payment providers?", "jargon",
     [G + "Payment Failure Rate", C + "payment_transactions.status", C + "payment_transactions.payment_provider"], [], [X + "30"], [],
     "answer", "", "'decline rate' is a synonym; provider column is never named"),
    ("G07", "How many orders used BOPIS last year?", "jargon",
     [G + "Store Pickup", C + "orders.shipping_method"], [C + "orders.order_date"], [X + "42"], [],
     "answer + state assumption", "'last year' = 2024, the last full year in the data", "abbreviation BOPIS"),
    ("G08", "Do payments without 3DS get disputed more often?", "jargon",
     [G + "3-D Secure", G + "Chargeback", C + "payment_transactions.is_3d_secure", C + "payment_transactions.chargeback_raised"], [], [X + "33"], [],
     "answer", "", "two jargon words in one question"),
    ("G09", "Find the product with SKU ADI-CAS-1206", "jargon",
     [G + "SKU", C + "products.sku"], [], [], [CAP + "3"],
     "answer", "", "identifier lookup; rule: identify products by sku, never by name"),
    ("G10", "How many lost customers do we have?", "jargon",
     [G + "Churned", C + "customers.customer_segment"], [], [X + "19"], [],
     "answer", "", "'lost customers' is a synonym of the Churned segment"),

    # ── B · plain wording: no column names, no synonyms ───────────────────────────────────────────
    ("G11", "How much money did customers spend with us in each month of 2024?", "plain",
     [G + "Revenue", C + "orders.total_amount"], [C + "orders.order_date"], [X + "1"], [CAP + "3"],
     "answer", "merchandise only", "revenue described in everyday words"),
    ("G12", "After the money we gave back, how much did we really earn?", "plain",
     [G + "Net Revenue", C + "payment_transactions.amount", C + "payment_transactions.status"], [], [X + "3"], [CAP + "3"],
     "answer", "", "net revenue without the word 'net' or 'revenue'"),
    ("G13", "Which items are our most popular by number of pieces sold?", "plain",
     [G + "Units Sold", C + "order_items.quantity", J + "order_items->ecom.products::product_id"], [C + "products.product_name"], [X + "10"], [CAP + "3"],
     "answer", "", "'pieces sold' = units; needs a join to name the products"),
    ("G14", "Which items earn us the biggest cut on each sale?", "plain",
     [G + "Gross Margin", C + "products.margin_pct"], [C + "products.cost_price"], [X + "13"], [],
     "answer", "", "margin in slang"),
    ("G15", "How long does a parcel take to reach the buyer?", "plain",
     [G + "Delivery Time", C + "shipments.delivery_days_actual"], [C + "shipments.status"], [X + "38"], [CAP + "3"],
     "answer", "Delivered shipments only", "rule: delivery_days_actual is 0 when not delivered"),
    ("G16", "Which products are running low and need restocking?", "plain",
     [G + "Below Reorder Point", C + "inventory.quantity_available", C + "inventory.reorder_point"], [J + "inventory->ecom.products::product_id"], [X + "46"], [],
     "answer", "", "'running low' = below reorder point"),
    ("G17", "How many people bought from us more than once?", "plain",
     [G + "Repeat Customer", C + "customers.lifetime_orders"], [], [X + "22"], [],
     "answer", "", "repeat customer described, not named"),
    ("G18", "Where do our shoppers live?", "plain",
     [G + "Home State", C + "customers.state"], [], [X + "24"], [CAP + "3"],
     "answer", "", "trap: orders.shipping_state is where orders went, not where customers live"),
    ("G19", "How old were the people who bought from us in 2024?", "plain",
     [G + "Age", C + "customers.birth_year", J + "orders->ecom.customers::customer_id"], [C + "orders.order_date"], [X + "25"], [CAP + "2"],
     "answer", "age from birth year only", "only the birth year is stored"),
    ("G20", "Which customers have gone quiet since the middle of 2024?", "plain",
     [C + "customers.last_order_date"], [], [X + "27"], [],
     "answer", "", "trap: NOT the Churned label, which is assigned by the CRM"),
    ("G21", "How happy are buyers with each category?", "plain",
     [G + "Sentiment", C + "reviews.rating", J + "reviews->ecom.products::product_id"], [C + "products.category"], [X + "59"], [],
     "answer", "", "'how happy' = review rating / sentiment"),
    ("G22", "Which vendors take longest to deliver stock to us?", "plain",
     [G + "Lead Time", C + "product_suppliers.lead_time_days", J + "product_suppliers->ecom.suppliers::supplier_id"], [C + "suppliers.supplier_name"], [X + "51"], [],
     "answer", "", "'vendors' + 'take longest' = supplier lead time"),

    # ── C · two business terms in one question ────────────────────────────────────────────────────
    ("G23", "Is the AOV higher when a coupon is used?", "two terms",
     [G + "Average Order Value", C + "orders.total_amount", C + "orders.coupon_code"], [G + "Coupon Redemptions"], [X + "55"], [],
     "answer", "", "AOV + coupon"),
    ("G24", "Which is higher for us, the return rate or the refund rate?", "two terms",
     [G + "Return Rate", G + "Refund Rate", C + "orders.order_status", C + "payment_transactions.status"], [], [X + "30", X + "44"], [],
     "answer", "", "two similar-sounding metrics with different definitions"),
    ("G25", "What share of VIP customers are repeat buyers?", "two terms",
     [G + "VIP", G + "Repeat Customer", C + "customers.customer_segment", C + "customers.lifetime_orders"], [], [X + "19", X + "22"], [],
     "answer", "", "segment label + repeat definition"),

    # ── D · needs several tables (joins) ──────────────────────────────────────────────────────────
    ("G26", "What is revenue by supplier?", "joins",
     [G + "Revenue", C + "order_items.total_price", C + "suppliers.supplier_name",
      J + "order_items->ecom.products::product_id", J + "product_suppliers->ecom.products::product_id",
      J + "product_suppliers->ecom.suppliers::supplier_id"],
     [G + "Primary Supplier", C + "product_suppliers.is_primary_supplier"], [], [CAP + "3"],
     "answer + state assumption", "credit each product's sales to its primary supplier", "a 4-table path; no example exists"),
    ("G27", "Which warehouse has the most late deliveries?", "joins",
     [G + "On-Time Delivery Rate", C + "shipments.on_time", C + "warehouses.warehouse_name", J + "shipments->ecom.warehouses::warehouse_id"], [C + "shipments.status"], [X + "37", X + "38"], [CAP + "3"],
     "answer", "Delivered shipments only", "'late' = not on time; needs the warehouse join"),
    ("G28", "What is revenue by top-level department?", "joins",
     [G + "Revenue", G + "Category Hierarchy", C + "order_items.total_price", C + "categories.parent_category_id",
      J + "order_items->ecom.products::product_id", J + "products->ecom.categories::category_id",
      J + "categories->ecom.categories::parent_category_id = category_id"],
     [C + "categories.category_level"], [X + "11", X + "17"], [CAP + "3"],
     "answer", "", "'department' is a Category Hierarchy synonym; 3 joins incl. the self-join"),
    ("G29", "Which customers write the most negative reviews?", "joins",
     [G + "Sentiment", C + "reviews.sentiment", J + "reviews->ecom.customers::customer_id"], [C + "reviews.rating"], [X + "59"], [],
     "answer", "", "reviews joined to customers"),
    ("G30", "How much did carriers charge us compared with what customers paid for delivery?", "joins",
     [C + "orders.shipping_cost", C + "shipments.shipping_cost", J + "shipments->ecom.orders::order_id"], [], [X + "41"], [CAP + "3"],
     "answer", "", "two columns with the same name in two tables; rule says which is which"),

    # ── E · a rule in the capability card changes the SQL ─────────────────────────────────────────
    ("G31", "What was our total revenue in 2024 including shipping and tax?", "rules",
     [G + "Revenue", C + "orders.total_amount", C + "orders.shipping_cost", C + "orders.tax_amount"], [C + "orders.order_date"], [X + "7"], [CAP + "3"],
     "answer", "", "total_amount alone excludes shipping and tax"),
    ("G32", "Which states do we send the most orders to?", "rules",
     [G + "Shipping Address", C + "orders.shipping_state"], [], [X + "6"], [CAP + "3"],
     "answer", "", "trap: the opposite of G18 — destination, not home state"),
    ("G33", "Who are our most valuable customers — are they all VIP?", "rules",
     [G + "VIP", C + "customers.lifetime_revenue", C + "customers.customer_segment"], [], [X + "20", X + "19"], [],
     "answer", "", "VIP is a CRM label (81% of customers), not a value tier"),
    ("G34", "How many orders are on their way right now?", "rules",
     [G + "Shipped", C + "orders.order_status"], [G + "In Transit", C + "shipments.status"], [X + "39"], [CAP + "2"],
     "answer + state assumption", "'right now' = at the end of the data, 2024-12-28", "status words + 'now' has no data"),
    ("G35", "Which promotions are running at the moment?", "rules",
     [G + "Active Promotion", C + "promotions.status"], [], [X + "56"], [],
     "answer + state assumption", "status is as of 2024-12-31", "'at the moment' = the data's reference date"),
    ("G36", "How did this year's sales compare with last year's?", "rules",
     [G + "Revenue", C + "orders.total_amount"], [C + "orders.order_date"], [X + "2"], [CAP + "1", CAP + "3"],
     "answer + state assumption", "'this year' = 2024, 'last year' = 2023 (the data ends 2024-12-28)", "relative dates"),

    # ── F · the knowledge base cannot answer: the agent must say so ──────────────────────────────
    ("G37", "How many people visited our website yesterday?", "can't answer",
     [CAP + "2"], [], [], [CAP + "2"], "refuse", "", "no visit data"),
    ("G38", "What was our revenue in March 2025?", "can't answer",
     [CAP + "2"], [G + "Revenue"], [], [CAP + "2"], "refuse", "", "after 2024-12-28"),
    ("G39", "How much did we spend on Facebook ads last quarter?", "can't answer",
     [CAP + "2"], [], [], [CAP + "2"], "refuse", "", "trap: Facebook is a referral source, but there is no ad spend"),
    ("G40", "What is our conversion rate from visit to purchase?", "can't answer",
     [CAP + "2"], [], [], [CAP + "2"], "refuse", "", "no sessions or conversion"),
    ("G41", "Which customers have a birthday this week?", "can't answer",
     [CAP + "2"], [G + "Age"], [], [CAP + "2"], "refuse", "", "only the birth year is kept"),
    ("G42", "Which of the catalogue promotions did shoppers use most?", "can't answer",
     [CAP + "2"], [G + "Coupon Redemptions"], [], [CAP + "2"], "refuse", "", "no orders reference the 100 catalogue promotions"),
    ("G43", "What's the weather in Chicago tomorrow?", "out of scope",
     [], [], [], [CAP + "1"], "refuse", "", "nothing in the knowledge base is relevant — used to set a score threshold"),

    ("G46", "Who won the cricket match yesterday?", "out of scope",
     [], [], [], [CAP + "1"], "refuse", "", "nothing in the knowledge base is relevant"),
    ("G47", "Give me a recipe for chicken biryani", "out of scope",
     [], [], [], [CAP + "1"], "refuse", "", "nothing in the knowledge base is relevant"),
    ("G48", "What is Nike's share price today?", "out of scope",
     [], [], [], [CAP + "1"], "refuse", "", "trap: Nike is a brand in the catalogue, but share prices are not data we hold"),
    ("G49", "Translate 'thank you for your order' into French", "out of scope",
     [], [], [], [CAP + "1"], "refuse", "", "a language task, not a data question"),

    # ── G · identifiers and codes ─────────────────────────────────────────────────────────────────
    ("G44", "Find the shipment for waybill 1Z000AA004245796", "jargon",
     [G + "Tracking Number", C + "shipments.tracking_number"], [], [], [],
     "answer", "", "'waybill' is a synonym"),
    ("G45", "Which suppliers give us a discount for paying early?", "plain",
     [G + "2/10 Net 30", C + "suppliers.payment_terms"], [], [], [],
     "answer", "", "payment-terms code described in words"),
]

# Telugu and Hinglish versions of six golden questions. Same ids as the parent question.
LANGUAGES = [
    ("G01", "Telugu", "గత నెల మా GMV ఎంత?"),
    ("G01", "Hinglish", "pichle mahine ka GMV kitna tha?"),
    ("G03", "Telugu", "క్యారియర్ వారీగా సమయానికి డెలివరీ అయిన శాతం ఎంత?"),
    ("G03", "Hinglish", "carrier ke hisaab se on-time delivery kitni hai?"),
    ("G11", "Telugu", "2024లో ప్రతి నెల కస్టమర్లు మా దగ్గర ఎంత డబ్బు ఖర్చు చేశారు?"),
    ("G11", "Hinglish", "2024 mein har mahine customers ne humare yahan kitna paisa kharch kiya?"),
    ("G15", "Telugu", "పార్సిల్ కొనుగోలుదారుడికి చేరడానికి ఎన్ని రోజులు పడుతుంది?"),
    ("G15", "Hinglish", "parcel customer tak pahunchne mein kitne din lagte hain?"),
    ("G18", "Telugu", "మా కస్టమర్లు ఏ రాష్ట్రాల్లో నివసిస్తున్నారు?"),
    ("G18", "Hinglish", "humare customers kis state mein rehte hain?"),
    ("G37", "Telugu", "నిన్న మా వెబ్‌సైట్‌ను ఎంత మంది సందర్శించారు?"),
    ("G37", "Hinglish", "kal humari website pe kitne log aaye the?"),
]
