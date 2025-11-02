from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from .db import create_db_and_tables, get_session
from .schemas import CreateBillRequest
from .crud import compute_bill, get_bill_details
from .email_utils import send_invoice_background
from .models import Customer, Bill, BillItem, Product

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def billing_page(request: Request):
    return templates.TemplateResponse("billing_page.html", {"request": request})

@app.post("/api/generate-bill")
def api_generate_bill(req: CreateBillRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    try:
        result = compute_bill(session, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    bill_obj = result["bill"]

    cust_email = None
    if getattr(bill_obj, "customer_id", None) is not None:
        cust = session.get(Customer, bill_obj.customer_id)
        if cust:
            cust_email = cust.email

    invoice_html = templates.get_template("bill_preview.html").render(
        bill=result["bill"],
        items=result["items"],
        change=result["change_distribution"],
        customer_email=cust_email or req.customer_email
    )

    send_invoice_background(background_tasks, req.customer_email, "Your Invoice", invoice_html)

    print(f"DEBUG generate-bill -> bill_id={getattr(bill_obj, 'id', None)} customer_id={getattr(bill_obj, 'customer_id', None)} cust_email={cust_email}")

    return {
        "bill_id": getattr(bill_obj, "id", None),
        "customer_email": cust_email or req.customer_email,
        "change_distribution": result["change_distribution"],
        "remainder_unreturned": str(result["remainder_unreturned"])
    }

@app.get("/api/bill/{bill_id}")
def api_get_bill(bill_id: int, session: Session = Depends(get_session)):
    details = get_bill_details(session, bill_id)
    if not details:
        raise HTTPException(status_code=404, detail="Bill not found")
    bill, items, change = details

    customer_email = None
    if getattr(bill, "customer_id", None) is not None:
        customer = session.get(Customer, bill.customer_id)
        if customer:
            customer_email = customer.email
            
    if not customer_email:
        customer_email = request.query_params.get("email", "")

    bill_dict = {
        "id": bill.id,
        "customer_id": bill.customer_id,
        "customer_email": customer_email,
        "created_at": str(bill.created_at),
        "total_without_tax": str(bill.total_without_tax),
        "total_tax": str(bill.total_tax),
        "total_with_tax": str(bill.total_with_tax),
        "paid_amount": str(bill.paid_amount),
        "change_given": str(bill.change_given)
    }
    items_out = []
    for it in items:
        items_out.append({
            "product_id": it.product_id,
            "product_name": getattr(it, "product_name", None),
            "quantity": it.quantity,
            "unit_price": str(it.unit_price),
            "tax_percentage": str(it.tax_percentage),
            "line_total": str(it.line_total)
        })
    return {"bill": bill_dict, "items": items_out, "change_distribution": change}

@app.get("/preview/{bill_id}")
def preview_bill(request: Request, bill_id: int, session: Session = Depends(get_session)):
    details = get_bill_details(session, bill_id)
    if not details:
        raise HTTPException(status_code=404, detail="Bill not found")

    bill_prepared, items_prepared, change_dist = details

    customer_id = bill_prepared.get("customer_id") if isinstance(bill_prepared, dict) else getattr(bill_prepared, "customer_id", None)
    customer_email = None

    if customer_id:
        cust = session.get(Customer, customer_id)
        if cust:
            customer_email = cust.email

    if not customer_email:
        customer_email = request.query_params.get("email", "")

    print(f"DEBUG preview -> bill_id={bill_id}, customer_email={customer_email}")

    return templates.TemplateResponse(
        "bill_preview.html",
        {
            "request": request,
            "bill": bill_prepared,
            "items": items_prepared,
            "change": change_dist,
            "customer_email": customer_email,
        },
    )


@app.get("/purchases")
def purchases_page(request: Request, email: str = None, session: Session = Depends(get_session)):
    bills = []
    if email:
        customer = session.query(Customer).filter(Customer.email == email).first()
        if customer:
            bills = session.query(Bill).filter(Bill.customer_id == customer.id).all()
    return templates.TemplateResponse("purchases.html", {"request": request, "bills": bills, "email": email})