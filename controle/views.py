from django.shortcuts import render, get_object_or_404, redirect
from .models import Employee, Warning, Attachment,models, Attendance
from .forms import EmployeeForm, WarningForm, AttachmentForm, SearchForm, AttendanceForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db.models import Q
from datetime import datetime, timedelta
from django.http import HttpResponse
from openpyxl import Workbook

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('employee_list')  # Redireciona para a lista de funcionários
        else:
            return render(request, 'login.html', {'error': 'Credenciais inválidas'})
    return render(request, 'login.html')


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})


def home(request):
    if request.user.is_authenticated:
        # Se o usuário estiver logado, redirecione para a lista de funcionários
        return redirect('employee_list')
    else:
        # Se o usuário não estiver logado, redirecione para a página de login
        return redirect('login')


# Lista de Funcionários
@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})

# Detalhes de um Funcionário
@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employee_detail.html', {'employee': employee})

# Adicionar Funcionário
@login_required
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'add_employee.html', {'form': form})

# Adicionar Advertência
@login_required
def add_warning(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    if request.method == 'POST':
        form = WarningForm(request.POST)
        if form.is_valid():
            warning = form.save(commit=False)
            warning.employee = employee
            warning.save()
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = WarningForm()
    return render(request, 'add_warning.html', {'form': form, 'employee': employee})

# Adicionar Anexo
@login_required
def add_attachment(request, warning_pk):
    warning = get_object_or_404(Warning, pk=warning_pk)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.warning = warning
            attachment.save()
            return redirect('employee_detail', pk=warning.employee.pk)
    else:
        form = AttachmentForm()
    return render(request, 'add_attachment.html', {'form': form, 'warning': warning})


@login_required
def delete_attachment(request, attachment_pk):
    attachment = get_object_or_404(Attachment, pk=attachment_pk)
    employee_pk = attachment.warning.employee.pk  # Para redirecionar ao detalhe do funcionário
    attachment.delete()  # Remove o anexo do banco de dados
    return redirect('employee_detail', pk=employee_pk)

@login_required
def delete_employee(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    if request.method == 'POST':  # Confirmação via POST
        employee.delete()
        messages.success(request, f'O funcionário "{employee.name}" foi removido com sucesso.')
        return redirect('employee_list')  # Redireciona para a lista de funcionários
    return render(request, 'confirm_delete.html', {'employee': employee})

@login_required
def employee_list(request):
    form = SearchForm(request.GET or None)  # Inicializa o formulário com os dados da requisição GET
    employees = Employee.objects.all()

    if form.is_valid() and form.cleaned_data['query']:
        query = form.cleaned_data['query']
        # Filtra os funcionários pelo nome, cargo ou departamento
        employees = employees.filter(
            Q(name__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query)
        )

    return render(request, 'employee_list.html', {'form': form, 'employees': employees})


def attendance_list(request):
    employees = Employee.objects.all().order_by('name', 'shift')
    dates = Attendance.objects.values_list('date', flat=True).distinct().order_by('-date')[:7]  # Últimos 7 dias
    attendances = Attendance.objects.all()

    attendance_data = {}
    for employee in employees:
        attendance_data[employee] = {}
        for date in dates:
            try:
                record = attendances.get(employee=employee, date=date)
                attendance_data[employee][date] = record.status
            except Attendance.DoesNotExist:
                attendance_data[employee][date] = '-'  # Se não houver registro, exibe '-'

    return render(request, 'attendance_list.html', {
        'employees': employees,
        'dates': dates,
        'attendance_data': attendance_data,
    })

def add_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')  # Redireciona para a lista de chamadas
    else:
        form = AttendanceForm()

    return render(request, 'add_attendance.html', {'form': form})



def attendance_table(request):
    # Obter os parâmetros de filtro
    selected_month = request.GET.get('month', datetime.now().strftime('%Y-%m'))  # Padrão: mês atual
    search_query = request.GET.get('search', '').strip()  # Barra de pesquisa
    selected_shift = request.GET.get('shift', '')  # Filtro de turno

    # Filtrar funcionários pelo nome     employees = Employee.objects.all().order_by('name', 'shift')
    employees = Employee.objects.all()
    if search_query:
        employees = employees.filter(name__icontains=search_query).order_by('name')

    # Filtrar funcionários pelo turno
    if selected_shift:
        employees = employees.filter(shift=selected_shift)

    # Gerar todas as datas do mês selecionado
    selected_date = datetime.strptime(selected_month, '%Y-%m')
    start_date = datetime(selected_date.year, selected_date.month, 1)
    if selected_date.month == 12:
        end_date = datetime(selected_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(selected_date.year, selected_date.month + 1, 1) - timedelta(days=1)

    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Filtrar chamadas pelo mês selecionado
    attendances = Attendance.objects.filter(date__range=[start_date, end_date])

    # Organizar os dados para facilitar a exibição no template
    attendance_data = {}
    for employee in employees:
        attendance_data[employee] = {}
        for date in dates:
            try:
                record = attendances.get(employee=employee, date=date)
                attendance_data[employee][date] = record.status
            except Attendance.DoesNotExist:
                attendance_data[employee][date] = '-'  # Se não houver registro, exibe '-'

    # Gerar lista de meses para o filtro
    months = [(datetime.now() - timedelta(days=30 * i)).strftime('%Y-%m') for i in range(6)]  # Últimos 6 meses

    return render(request, 'attendance_table.html', {
        
        'employees': employees,
        'dates': dates,
        'attendance_data': attendance_data,
        'selected_month': selected_month,
        'months': months,
        'search_query': search_query,
        'selected_shift': selected_shift,
    })

def update_attendance(request, employee_pk, date):
    # Converte a data de string para objeto datetime.date
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()

    # Obtém ou cria o registro de chamada
    attendance, created = Attendance.objects.get_or_create(
        employee_id=employee_pk,
        date=date_obj,
        defaults={'status': '-'}  # Valor padrão se o registro não existir
    )

    # Atualiza o status se o método for POST
    if request.method == 'POST':
        status = request.POST.get('status')
        attendance.status = status
        attendance.save()

    # Redireciona para a página de chamadas
    return redirect('attendance_table')  # Certifique-se de que o nome está correto






def home(request):
    # Obter os parâmetros de filtro
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    selected_shift = request.GET.get('shift', '')  # Filtro de turno

    # Definir datas padrão (últimos 7 dias)
    if not start_date_str or not end_date_str:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=23)  # Últimos 7 dias
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Filtrar chamadas pelo intervalo de datas e turno selecionados
    attendances = Attendance.objects.filter(date__range=[start_date, end_date])
    if selected_shift:
        attendances = attendances.filter(employee__shift=selected_shift)

    # Contar presenças e faltas por dia
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    attendance_data = []
    total_presence = 0
    total_absence = 0

    for date in dates:
        presence_count = attendances.filter(date=date, status='P').count()
        absence_count = attendances.filter(date=date, status='F').count()
        total_presence += presence_count
        total_absence += absence_count
        attendance_data.append({
            'date': date.strftime('%d/%m'),
            'presence': presence_count,
            'absence': absence_count,
        })

        # Calcular absenteísmo
        total_records = total_presence + total_absence
        absenteeism = (total_absence / total_records * 100) if total_records > 0 else 0

        # Calcular a média de presenças e faltas por dia
        number_of_days = len(dates)
        average_presence_per_day = total_presence / number_of_days if number_of_days > 0 else 0
        average_absence_per_day = total_absence / number_of_days if number_of_days > 0 else 0

    return render(request, 'home.html', {
        'attendance_data': attendance_data,
        'start_date': start_date,
        'end_date': end_date,
        'absenteeism': round(absenteeism, 1),
        'selected_shift': selected_shift,
        'average_presence_per_day': round(average_presence_per_day),
        'average_absence_per_day': round(average_absence_per_day),
    })







def export_attendance_to_excel(request):
    # Obter os parâmetros de filtro (se houver)
    selected_month = request.GET.get('month', datetime.now().strftime('%Y-%m'))
    search_query = request.GET.get('search', '').strip()
    selected_shift = request.GET.get('shift', '')

    # Filtrar funcionários pelo nome (se houver pesquisa)
    employees = Employee.objects.all()
    if search_query:
        employees = employees.filter(name__icontains=search_query)

    # Filtrar funcionários pelo turno (se selecionado)
    if selected_shift:
        employees = employees.filter(shift=selected_shift)

    # Gerar todas as datas do mês selecionado
    selected_date = datetime.strptime(selected_month, '%Y-%m')
    start_date = datetime(selected_date.year, selected_date.month, 1)
    if selected_date.month == 12:
        end_date = datetime(selected_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(selected_date.year, selected_date.month + 1, 1) - timedelta(days=1)

    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Filtrar chamadas pelo mês selecionado
    attendances = Attendance.objects.filter(date__range=[start_date, end_date])

    # Organizar os dados para facilitar a exibição no Excel
    attendance_data = {}
    for employee in employees:
        attendance_data[employee] = {}
        for date in dates:
            try:
                record = attendances.get(employee=employee, date=date)
                attendance_data[employee][date] = record.status
            except Attendance.DoesNotExist:
                attendance_data[employee][date] = '-'  # Se não houver registro, exibe '-'

    # Criar o arquivo Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Chamada"

    # Adicionar cabeçalhos
    headers = ["Funcionário"] + [date.strftime("%d/%m") for date in dates]
    ws.append(headers)

    # Adicionar dados
    for employee, records in attendance_data.items():
        row = [f"{employee.name} (Turno {employee.get_shift_display})"]
        for date in dates:
            row.append(records[date])
        ws.append(row)

    # Configurar o response para download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=chamada.xlsx'
    wb.save(response)

    return response