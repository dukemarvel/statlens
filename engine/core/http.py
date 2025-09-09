import hashlib
from django.utils.http import http_date

class ConditionalHeadersMixin:
    """
    Mixin to set Last-Modified (from latest updated_at in queryset)
    and a coarse ETag based on URL + latest timestamp.
    """
    def set_conditional_headers(self, request, response, queryset):
        latest = queryset.order_by("-updated_at").values_list("updated_at", flat=True).first()
        if latest:
            response["Last-Modified"] = http_date(latest.timestamp())
            etag_seed = f"{request.get_full_path()}::{latest.timestamp()}"
        else:
            etag_seed = f"{request.get_full_path()}::no-updates"

        response["ETag"] = hashlib.md5(etag_seed.encode()).hexdigest()
        return response
