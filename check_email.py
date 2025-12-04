"""Check employee email in Odoo"""
import xmlrpc.client

url = "http://51.20.91.45:8069"
db = "karem2"
username = "karem.ceo@ailigent.ai"
password = "5066ea93f7ca68b38e55b153437958668fae7bd8"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
print(f"Authenticated as UID: {uid}")

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Get employee 8
employee = models.execute_kw(db, uid, password, 'hr.employee', 'read', [[8]], {'fields': ['name', 'work_email', 'private_email']})
print(f"\nEmployee 8:")
print(f"  Name: {employee[0]['name']}")
print(f"  Work Email: {employee[0].get('work_email')}")
print(f"  Private Email: {employee[0].get('private_email')}")

# Search by email
email_to_search = "muhannadkhaledd@gmail.com"
result = models.execute_kw(db, uid, password, 'hr.employee', 'search', [[['work_email', '=', email_to_search]]])
print(f"\nSearching for work_email = '{email_to_search}':")
print(f"  Found employee IDs: {result}")

# Also try ilike (case-insensitive)
result2 = models.execute_kw(db, uid, password, 'hr.employee', 'search', [[['work_email', 'ilike', email_to_search]]])
print(f"\nSearching for work_email ilike '{email_to_search}':")
print(f"  Found employee IDs: {result2}")
