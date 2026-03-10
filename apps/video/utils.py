from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class VideoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        """
        This method defines the standard 'envelope' for all your paginated lists.
        """
        return Response({
            "success": True,
            "pagination": {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            "data": data
        })