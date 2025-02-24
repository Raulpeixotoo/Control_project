from django import forms
from .models import Employee, Warning, Attachment, Attendance
from django.forms.widgets import DateInput

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['matricula','name', 'position', 'department', 'admission_date','shift']
        labels = {
            'matricula': 'Matricula',
            'name': 'Nome',
            'position': 'Cargo',
            'department': 'Departamento',
            'admission_date': 'Data de Admissão',
            'shift':'Turno'
        }
        widgets = {
            'admission_date': DateInput(attrs={'type': 'date'}),
        }

class WarningForm(forms.ModelForm):
    class Meta:
        model = Warning
        fields = ['date', 'description', 'warning_type', 'responsible']
        labels = {
            'date': 'Data da Advertencia',
            'description': 'Observação',
            'warning_type': 'Grau da Advertencia',
            'responsible': 'Gestor responsável',
        }
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']




class SearchForm(forms.Form):
    query = forms.CharField(
        label='Pesquisar Funcionários',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Digite o nome, cargo ou departamento...'})
    )


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(choices=Attendance.ATTENDANCE_STATUS),
        }