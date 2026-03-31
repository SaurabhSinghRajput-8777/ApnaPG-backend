"""
Integration test: End-to-end PDF generation test.
Creates owner + tenant + property + connection, then generates the lease PDF.

Run with: python test_pdf_e2e.py
"""

import sys
import os

# Add the backend root to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.crud import user as user_crud
from app.crud import property as property_crud
from app.crud import connection as connection_crud
from app.schemas.user import UserCreate
from app.schemas.property import PropertyCreate
from app.schemas.connection import ConnectionStatusUpdate
from app.services.pdf_generator import generate_lease_pdf


def main():
    db = SessionLocal()
    try:
        # 1. Sync/get users
        owner = user_crud.get_user_by_clerk_id(db, "test_owner_001")
        tenant = user_crud.get_user_by_clerk_id(db, "test_clerk_001")

        if not owner:
            owner = user_crud.create_user(db, UserCreate(
                clerk_id="test_owner_001", role="owner",
                full_name="Rajesh Kumar", email="rajesh@owner.com",
                phone_number="+91-9876543210",
            ))
        if not tenant:
            tenant = user_crud.create_user(db, UserCreate(
                clerk_id="test_clerk_001", role="tenant",
                full_name="Amit Sharma", email="amit@tenant.com",
                phone_number="+91-9988776655",
            ))

        print(f"Owner: {owner.full_name} ({owner.id})")
        print(f"Tenant: {tenant.full_name} ({tenant.id})")

        # 2. Create a property
        prop = property_crud.create_property(db, owner_id=owner.id, data=PropertyCreate(
            title="Sunshine PG - Karol Bagh",
            description="Well-maintained PG with AC rooms near metro station.",
            locality="Karol Bagh, New Delhi",
            latitude=28.6519,
            longitude=77.1902,
            monthly_rent=8500,
            occupancy_type="double",
            house_rules={
                "curfew": "10:30 PM",
                "guests_allowed": False,
                "smoking": "Strictly prohibited",
                "laundry": "Twice a week (Mon, Thu)",
                "food": "Breakfast and dinner included",
                "deposit": "2 months advance",
            },
        ))
        print(f"Property: {prop.title} ({prop.id})")

        # 3. Create connection (tenant requests)
        conn = connection_crud.create_connection(db, tenant_id=tenant.id, property_id=prop.id)
        print(f"Connection: {conn.id} [status={conn.status}]")

        # 4. Owner accepts
        conn = connection_crud.update_connection_status(
            db, conn, ConnectionStatusUpdate(status="accepted")
        )
        print(f"Connection accepted. Tenancy starts: {conn.tenancy_start_date}")

        # 5. Generate the PDF
        pdf_buffer = generate_lease_pdf(
            tenant_data={
                "full_name": tenant.full_name,
                "email": tenant.email,
                "phone_number": tenant.phone_number,
            },
            owner_data={
                "full_name": owner.full_name,
                "email": owner.email,
                "phone_number": owner.phone_number,
            },
            property_data={
                "title": prop.title,
                "locality": prop.locality,
                "monthly_rent": prop.monthly_rent,
                "occupancy_type": prop.occupancy_type,
                "house_rules": prop.house_rules,
                "tenancy_start_date": conn.tenancy_start_date,
            },
        )

        # 6. Save the PDF locally for inspection
        output_path = os.path.join(os.path.dirname(__file__), "test_lease.pdf")
        with open(output_path, "wb") as f:
            f.write(pdf_buffer.read())

        size_kb = os.path.getsize(output_path) / 1024
        print(f"\n✅ PDF generated successfully!")
        print(f"   File: {output_path}")
        print(f"   Size: {size_kb:.1f} KB")

    finally:
        db.close()


if __name__ == "__main__":
    main()
