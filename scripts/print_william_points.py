import os
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sundowns_app.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from points.models import PointsTransaction

User = get_user_model()
user = User.objects.filter(username='william').first()
if not user:
    print('USER_NOT_FOUND')
    raise SystemExit(0)

account = getattr(user, 'points_account', None)
if not account:
    print('ACCOUNT_NOT_FOUND')
    raise SystemExit(0)

print('BALANCE:', account.balance)
qs = PointsTransaction.objects.filter(account=account).order_by('-created_at')
rows = []
for tx in qs:
    rows.append({
        'transaction_type': tx.transaction_type,
        'points': tx.points,
        'description': tx.description,
        'reference_id': tx.reference_id,
        'created_at': tx.created_at.isoformat(),
    })
print(json.dumps(rows, indent=2))
