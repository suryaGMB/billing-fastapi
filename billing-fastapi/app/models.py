from typing import Optional
from decimal import Decimal
import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Numeric, Integer, Text

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True, unique=True)
    name: str
    available_stocks: int = Field(sa_column=Column(Integer))
    price: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    tax_percentage: Decimal = Field(sa_column=Column(Numeric(5, 2)))

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)

class Bill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[int]
    customer_email: Optional[str] = Field(default=None, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    total_without_tax: Decimal = Field(sa_column=Column(Numeric(14,2)))
    total_tax: Decimal = Field(sa_column=Column(Numeric(14,2)))
    total_with_tax: Decimal = Field(sa_column=Column(Numeric(14,2)))
    paid_amount: Decimal = Field(sa_column=Column(Numeric(14,2)))
    change_given: Decimal = Field(sa_column=Column(Numeric(14,2)))
    change_json: Optional[str] = Field(default=None, sa_column=Column(Text))

class BillItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bill_id: Optional[int]
    product_id: Optional[int]
    quantity: int = Field(sa_column=Column(Integer))
    unit_price: Decimal = Field(sa_column=Column(Numeric(12,2)))
    tax_percentage: Decimal = Field(sa_column=Column(Numeric(5,2)))
    line_total: Decimal = Field(sa_column=Column(Numeric(14,2)))

class Denomination(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    value: int = Field(sa_column=Column(Integer))
    available_count: int = Field(sa_column=Column(Integer))