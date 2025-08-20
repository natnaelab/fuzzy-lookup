from django.urls import path
from .views import ColumnNamesApiView,FuzzyLookupMultiApiView

urlpatterns = [
    path('api/column_names/', ColumnNamesApiView.as_view(), name='api_column_names'),
    path('api/lookup_multi_file_apiView/', FuzzyLookupMultiApiView.as_view(), name='lookup_multi_file_apiView'),
]
