from datetime import datetime
from datetime import timedelta
from datetime import timezone

SHA_TZ = timezone(
    timedelta(hours=8),
    name='Asia/Shanghai',
)

utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)wo
beijing_now = utc_now.astimezone(SHA_TZ)
print(beijing_now)
