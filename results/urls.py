from django.urls import path
from results.views import result_list_view, result_detail_view

urlpatterns = [
    path('', result_list_view, name='result-list'),
    path('<int:pk>/', result_detail_view, name='result-detail'),
]
