from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import csv
import os
import uuid
from django.conf import settings
from django.db import connection
from django.utils import timezone
from .models import Employee, Department, Position


class EmployeeCsvUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_id = str(uuid.uuid4())
        temp_file_path = os.path.join(settings.MEDIA_ROOT, f'temp_csv_{file_id}.csv')
        
        with open(temp_file_path, 'wb+') as destination:
            for chunk in csv_file.chunks():
                destination.write(chunk)
        
        try:
            with open(temp_file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                
                expected_headers = [
                    'date_of_birth', 'department', 'position', 'salary', 
                    'date_of_joining', 'first_name', 'last_name', 'email', 'phone_number'
                ]
                
                missing_headers = [h for h in expected_headers if h not in headers]
                if missing_headers:
                    os.remove(temp_file_path)
                    return Response({
                        'error': f'Missing required columns: {", ".join(missing_headers)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not any(1 for _ in reader):
                    os.remove(temp_file_path)
                    return Response({'error': 'CSV file has no data rows'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return Response({'error': f'Error validating CSV: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with open(temp_file_path, 'r') as f:
                reader = csv.DictReader(f)
                departments = set()
                positions = set()
                
                for row in reader:
                    if row.get('department'):
                        departments.add(row['department'])
                    if row.get('position'):
                        positions.add(row['position'])
            
            for dept_name in departments:
                Department.objects.get_or_create(
                    name=dept_name, 
                    defaults={'location': 'Unknown'}
                )
            
            for position_title in positions:
                Position.objects.get_or_create(
                    title=position_title
                )
            
            staging_table = f"employee_staging_{file_id.replace('-', '_').lower()}"
            
            with connection.cursor() as cursor:
                cursor.execute(f"""
                CREATE TEMPORARY TABLE {staging_table} (
                    date_of_birth DATE,
                    department VARCHAR(100),
                    position VARCHAR(100),
                    salary NUMERIC(10,2),
                    date_of_joining DATE,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    email VARCHAR(254),
                    phone_number VARCHAR(15)
                )
                """)
                
                with open(temp_file_path, 'r') as f:
                    cursor.copy_expert(f"COPY {staging_table} FROM STDIN WITH CSV HEADER", f)
                
                cursor.execute(f"SELECT COUNT(*) FROM {Employee._meta.db_table}")
                before_count = cursor.fetchone()[0]
                
                now = timezone.now().isoformat()
                
                cursor.execute(f"""
                INSERT INTO {Employee._meta.db_table} (
                    first_name, last_name, email, phone_number, 
                    date_of_birth, date_of_joining, salary,
                    department_id, position_id, created_at, updated_at
                )
                SELECT 
                    s.first_name, 
                    s.last_name, 
                    s.email, 
                    s.phone_number, 
                    s.date_of_birth, 
                    s.date_of_joining, 
                    s.salary,
                    d.id, 
                    p.id, 
                    %s, 
                    %s
                FROM {staging_table} s
                LEFT JOIN {Department._meta.db_table} d ON d.name = s.department
                LEFT JOIN {Position._meta.db_table} p ON p.title = s.position
                """, [now, now])
                
                cursor.execute(f"SELECT COUNT(*) FROM {Employee._meta.db_table}")
                after_count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(*) FROM {staging_table}")
                total_rows = cursor.fetchone()[0]
                
                cursor.execute(f"DROP TABLE {staging_table}")
            
            os.remove(temp_file_path)
            
            return Response({
                'message': 'CSV import completed successfully',
                'rows_processed': total_rows,
                'employees_created': after_count - before_count,
                'total_employees': after_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return Response({
                'error': f'Error during import: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)