"""Cursor pagination in the shape the frontend already uses: {items, next_cursor}."""

from urllib.parse import parse_qs, urlparse

from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class NewestFirstCursorPagination(CursorPagination):
    ordering = ("-created_at", "-id")
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100  # out-of-range limits are clamped by DRF, not rejected

    def get_paginated_response(self, data):  # noqa: ANN001, ANN201
        link = self.get_next_link()
        cursor = None if link is None else parse_qs(urlparse(link).query)[self.cursor_query_param][0]
        return Response({"items": data, "next_cursor": cursor})
