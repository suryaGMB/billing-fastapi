from .db import create_db_and_tables, engine
from .models import Product, Denomination
from sqlmodel import Session
from decimal import Decimal

def seed():
    create_db_and_tables()
    with Session(engine) as s:
        if s.query(Product).count() == 0:
            p1 = Product(product_id="P001", name="Pencil", available_stocks=100, price=Decimal("12.00"), tax_percentage=Decimal("5.0"))
            p2 = Product(product_id="P002", name="Notebook", available_stocks=50, price=Decimal("45.00"), tax_percentage=Decimal("12.0"))
            s.add_all([p1, p2])
        if s.query(Denomination).count() == 0:
            denominations = [2000,500,200,100,50,20,10,5,2,1]
            for v in denominations:
                s.add(Denomination(value=v, available_count=10))
        s.commit()

if __name__ == "__main__":
    seed()
    print("Seeded DB")