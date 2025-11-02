from pydantic import BaseModel
from typing import List
from decimal import Decimal

class BillItemIn(BaseModel):
    product_code: str
    quantity: int

class DenominationInput(BaseModel):
    value: int
    count: int

class CreateBillRequest(BaseModel):
    customer_email: str
    items: List[BillItemIn]
    denominations: List[DenominationInput]
    paid_amount: Decimal