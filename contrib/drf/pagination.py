from rest_framework import pagination


class LimitedCursorPagination(pagination.CursorPagination):
    page_size_query_param = "page_size"
    max_page_size = 500
    ordering = "-created_at"

    def get_ordering(self, request, queryset, view):
        if hasattr(view, "ordering"):
            ordering = view.ordering
            if isinstance(ordering, str):
                ordering = (ordering,)
            return ordering

        return super().get_ordering(request, queryset, view)
