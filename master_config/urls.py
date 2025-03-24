from django.urls import path
from master_config.views import EmployeeListAPIView
from master_config.upload_csv import EmployeeCsvUploadView
from master_config.export_csv import EmployeeExportAPIView

urlpatterns = [
    path('employee-list/', EmployeeListAPIView.as_view()),
    path('upload-csv/', EmployeeCsvUploadView.as_view()),
    path('export-csv/', EmployeeExportAPIView.as_view()),
]