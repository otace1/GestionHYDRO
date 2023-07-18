from rest_framework.pagination import PageNumberPagination
import json
from datetime import datetime


#Paginattion
class CustomPagination(PageNumberPagination):
    page_size = 4  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 40  # Maximum number of items per page


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)