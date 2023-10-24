from rest_framework.pagination import PageNumberPagination
import json
from datetime import datetime


#Paginattion
class CustomPagination(PageNumberPagination):
    page_size = 4  # Set your preferred page size here
    page_size_query_param = 'pagination'
    max_page_size = 100  # Set the maximum page size if needed



class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)