from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        db_table = 'departments'


class Position(models.Model):
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]
        db_table = 'positions'


class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    date_of_joining = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees_department')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees_position')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['date_of_joining']),
            models.Index(fields=['department']),
            models.Index(fields=['position']),
        ]
        ordering = ['-date_of_joining']
        db_table = 'employees'