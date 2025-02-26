from django.db import models

class Employee(models.Model):
    SHIFTS = [
        ('1', 'Turno 1'),
        ('2', 'Turno 2'),
        ('3', 'Turno 3'),
    ]

    matricula = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    admission_date = models.DateField()
    shift = models.CharField(max_length=1, choices=SHIFTS, default='1')  # Turno de trabalho

    def __str__(self):
        return self.name

class Warning(models.Model):
    WARNING_TYPES = [
        ('L', 'Leve'),
        ('M', 'Média'),
        ('G', 'Grave'),
    ]

    employee = models.ForeignKey(Employee, related_name='warnings', on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    warning_type = models.CharField(max_length=1, choices=WARNING_TYPES)
    responsible = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.employee.name} - {self.get_warning_type_display()}"

class Attachment(models.Model):
    warning = models.ForeignKey(Warning, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anexo de {self.warning.employee.name}"
    


from django.db import models

class Attendance(models.Model):
    ATTENDANCE_STATUS = [
        ('P', 'Presença'),
        ('F', 'Falta'),
        ('AT', 'Atestado'),
        ('AF', 'Atestado'),
        ('FE', 'ferias'),
    ]
    employee = models.ForeignKey('Employee', related_name='attendances', on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=2, choices=ATTENDANCE_STATUS)

    class Meta:
        unique_together = ('employee', 'date')  # Garante que não haja duplicatas para o mesmo funcionário e data

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.get_status_display()}"