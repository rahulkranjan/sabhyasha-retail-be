import csv
from django.http import StreamingHttpResponse
from django.db.models import F, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from master_config.models import Employee


class Echo:
    def write(self, value):
        return value


class EmployeeExportAPIView(APIView):
    
    def get_queryset(self, request):
        search_query = request.query_params.get('search', '')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        department_id = request.query_params.get('department', None)
        position_id = request.query_params.get('position', None)
        
        queryset = Employee.objects.select_related('department', 'position').values(
            'id', 'first_name', 'last_name', 'email', 'phone_number', 'salary', 'date_of_joining',
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
        
        return queryset.order_by('-date_of_joining')
    
    def generate_rows(self, queryset):
        yield ['ID', 'First Name', 'Last Name', 'Email', 'Phone Number', 'Salary', 'Date of Joining', 'Department', 'Position']
        
        for employee in queryset.iterator():
            yield [
                str(employee['id']),
                employee['first_name'],
                employee['last_name'],
                employee['email'],
                employee['phone_number'],
                str(employee['salary']),
                employee['date_of_joining'].strftime('%Y-%m-%d'),
                employee['department_name'],
                employee['position_title']
            ]
    
    @method_decorator(cache_page(60 * 5))
    def get(self, request, format=None):
        queryset = self.get_queryset(request)
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in self.generate_rows(queryset)),
            content_type="text/csv"
        )
        
        filename = f"employees_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
