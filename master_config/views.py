from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Department, Employee, Position
from .serializers import EmployeeSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class CustomEmployeePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class EmployeeListAPIView(APIView):
    pagination_class = CustomEmployeePagination
    
    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        search_query = request.query_params.get('search', '')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        department_id = request.query_params.get('department', None)
        position_id = request.query_params.get('position', None)
        
        # Start with a values query to get exactly the fields we need
        queryset = Employee.objects.select_related('department', 'position').values(
            'id', 'first_name', 'last_name', 'email', 'date_of_joining','phone_number','salary',
            department_name=F('department__name'),
            position_title=F('position__title')
        )
        
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) | 
                Q(last_name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(department__name__icontains=search_query)
            )
        
        if start_date and end_date:
            queryset = queryset.filter(date_of_joining__range=[start_date, end_date])
            
        if department_id:
            queryset = queryset.filter(department_id=department_id)
            
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        
        queryset = queryset.order_by('-date_of_joining')
        
        paginator = self.pagination_class()
        return paginator.get_paginated_response(paginator.paginate_queryset(queryset, request))