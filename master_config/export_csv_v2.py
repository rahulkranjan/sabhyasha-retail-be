import pandas as pd
from django.http import StreamingHttpResponse
from django.db.models import Q
from django.utils import timezone
from rest_framework.views import APIView
from master_config.models import Employee

class EmployeeExportAPIViewV2(APIView):
    def get_queryset(self, request):
        search_query = request.query_params.get('search', '')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        department_id = request.query_params.get('department', None)
        position_id = request.query_params.get('position', None)

        queryset = Employee.objects.select_related('department', 'position').only(
            'id', 'first_name', 'last_name', 'email', 'phone_number', 'salary', 'date_of_joining',
            'department__name', 'position__title'
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

    def get(self, request, format=None):
        queryset = self.get_queryset(request)
        column_mapping = {
            'id': 'ID',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'phone_number': 'Phone Number',
            'salary': 'Salary',
            'date_of_joining': 'Date of Joining',
            'department__name': 'Department',
            'position__title': 'Position'
        }

        filename = f"employees_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = StreamingHttpResponse(
            self.stream_csv(queryset, column_mapping),
            content_type="text/csv"
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def stream_csv(self, queryset, column_mapping):
        yield ','.join(column_mapping.values()) + '\n'
        
        for employee in queryset.iterator():
            row = [
                str(employee.id),
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.phone_number,
                str(employee.salary),
                employee.date_of_joining.strftime('%Y-%m-%d'),
                employee.department.name,
                employee.position.title
            ]
            yield ','.join(row) + '\n'
