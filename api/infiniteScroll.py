from rest_framework.pagination import PageNumberPagination

#Paginattion
class CustomPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100  # Maximum number of items per page