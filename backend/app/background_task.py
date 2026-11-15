import asyncio
from .db import SessionLocal  
from .db_tables import orders_table

async def check_stale_order_status(order_id: int):
    """
    Waits 15 minutes (900 seconds) in the background. 
    If the order is still 'PLACED', logs a reminder alert for the owner.
    """
    # Wait for 15 minutes (900 seconds). 
    # TIP: Change to 10 or 15 seconds temporarily when testing in Postman!
    await asyncio.sleep(900)
    
    # Open a fresh database session since the original request session is closed
    db = SessionLocal()
    try:
        query = orders_table.select().where(orders_table.c.id == order_id)
        result = db.execute(query).fetchone()
        
        if result:
            order = dict(result._mapping)
            # Check if the owner still hasn't accepted it
            if order["status"] == "PLACED":
                print(f"\n[REMINDER ALERT] 🚨 Order ID #{order_id} (Customer: {order['customer_email']}) has been stuck in 'PLACED' status for 15 minutes! Please alert the restaurant owner.\n")
    finally:
        db.close()