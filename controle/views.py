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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


#login e auth
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  
        else:
            return render(request, 'login.html', {'error': 'Credenciais inválidas'})
    return render(request, 'login.html')

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})


def home(request):
    if request.user.is_authenticated:
        return redirect('employee_list')
    else:
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

#delete functions
@login_required
def delete_attachment(request, attachment_pk):
    attachment = get_object_or_404(Attachment, pk=attachment_pk)
    employee_pk = attachment.warning.employee.pk  
    attachment.delete()  
    return redirect('employee_detail', pk=employee_pk)

@login_required
def delete_employee(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    if request.method == 'POST':  # Confirmação via POST
        employee.delete()
        messages.success(request, f'O funcionário "{employee.name}" foi removido com sucesso.')
        return redirect('employee_list')  # Redireciona para a lista de funcionários
    return render(request, 'confirm_delete.html', {'employee': employee})




#funçoes da home e chamada
@login_required
def home(request):
    # Obter os parâmetros de filtro
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    selected_shift = request.GET.get('shift', '')  # Filtro de turno

    #datas padroes ajustadas
    if not start_date_str or not end_date_str:
        today = datetime.now().date()
        start_date = today.replace(day=1)  # Primeiro dia do mês
        next_month = today.replace(day=28) + timedelta(days=4)  # Garante que vai para o próximo mês
        end_date = next_month.replace(day=1) - timedelta(days=1)  # Último dia do mês
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
    total_atestad = 0
    total_ausence = 0
    total_vacancy = 0

    for date in dates:
        presence_count = attendances.filter(date=date, status='P').count()
        absence_count = attendances.filter(date=date, status='F').count()
        atestad_count = attendances.filter(date=date, status='AT').count()
        ausence_count = attendances.filter(date=date, status='AF').count()
        vacancy_count = attendances.filter(date=date, status='FE').count()
        total_presence += presence_count
        total_absence += absence_count
        total_atestad += atestad_count
        total_ausence += ausence_count
        total_vacancy += vacancy_count
        attendance_data.append({
            'date': date.strftime('%d/%m'),
            'presence': presence_count,
            'absence': absence_count,
            'atestad': atestad_count,
            'ausence': ausence_count,
            'vacancy': vacancy_count,
        })

    # Calcular absenteísmo
    total_records = total_presence + total_absence
    absenteeism = (total_absence / total_records * 100) if total_records > 0 else 0

    # Calcular a média de presenças e faltas por dia
    number_of_days = len(dates)
    average_presence_per_day = total_presence / number_of_days if number_of_days > 0 else 0
    average_absence_per_day = total_absence / number_of_days if number_of_days > 0 else 0

    # Contagem por turno (Dinâmica)
    shifts = (
        attendances.values_list('employee__shift', flat=True)
        .distinct()
        .order_by('employee__shift')
    )  # Obtém os turnos existentes no intervalo de datas
    shift_data = []

    for shift in shifts:
        shift_attendances = attendances.filter(employee__shift=shift)
        shift_presence = shift_attendances.filter(status='P').count()
        shift_absence = shift_attendances.filter(status='F').count()
        shift_atestad = shift_attendances.filter(status='AT').count()
        shift_ausence = shift_attendances.filter(status='AF').count()
        shift_vacancy = shift_attendances.filter(status='FE').count()

        shift_data.append({
            'shift': shift,
            'presence': shift_presence,
            'absence': shift_absence,
            'atestad': shift_atestad,
            'ausence': shift_ausence,
            'vacancy': shift_vacancy,
        })

    return render(request, 'home.html', {
        'attendance_data': attendance_data,
        'start_date': start_date,
        'end_date': end_date,
        'absenteeism': round(absenteeism, 1),
        'selected_shift': selected_shift,
        'average_presence_per_day': round(average_presence_per_day),
        'average_absence_per_day': round(average_absence_per_day),
        'shift_data': shift_data,  # Dados por turno
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



def attendance_table(request):
    # Obter os parâmetros de filtro
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    selected_shift = request.GET.get('shift', '')  # Filtro de turno
    search_name = request.GET.get('name', '')      # Filtro de nome

    # Definir datas padrão (últimos 30 dias)
    if not start_date_str or not end_date_str:
        today = datetime.now().date()
        start_date = today.replace(day=1)  # Primeiro dia do mês atual
        next_month = today.replace(day=28) + timedelta(days=4)  # Primeiro dia do próximo mês
        end_date = next_month.replace(day=1) - timedelta(days=1)  # Último dia do mês atual
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Caso as datas sejam inválidas, use as datas padrão
            today = datetime.now().date()
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)

    # Filtrar funcionários pelo nome (se fornecido)
    employees = Employee.objects.all()
    if search_name:
        employees = employees.filter(name__icontains=search_name)  # Busca parcial no nome

    # Filtrar funcionários pelo turno (se fornecido)
    if selected_shift:
        employees = employees.filter(shift=selected_shift)

    # Ordenar funcionários por nome (ordem alfabética)
    employees = employees.order_by('name')

    # Filtrar chamadas pelo intervalo de datas e funcionários filtrados
    attendances = Attendance.objects.filter(
        date__range=[start_date, end_date],
        employee__in=employees
    )

    # Gerar todas as datas do intervalo
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Organizar os dados para facilitar a exibição na tabela
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
    months = []
    current_month = datetime.now()
    for i in range(6):  # Últimos 6 meses
        month = current_month - timedelta(days=i * 30)
        months.append(month.strftime('%Y-%m'))

    return render(request, 'attendance_table.html', {
        'employees': employees,
        'dates': dates,
        'start_date': start_date,
        'end_date': end_date,
        'attendance_data': attendance_data,
        'months': months,  # Passa a lista de meses para o template
        'selected_shift': selected_shift,
        'search_name': search_name,
    })


@csrf_exempt
def save_all_attendance(request):
    if request.method == 'POST':
        try:
            # Receber os dados enviados pelo JavaScript
            data = json.loads(request.body)
            print('Dados recebidos:', data)  # Depuração: Exibe os dados recebidos

            for item in data:
                employee_pk = item.get('employee_pk')
                date = item.get('date')
                status = item.get('status')

                # Validar os dados recebidos
                if not employee_pk or not date or not status:
                    return JsonResponse({'success': False, 'error': 'Dados incompletos'})

                # Garantir que o status seja válido
                valid_statuses = ['P', 'F', 'AT', 'AF','FE', '-']
                if status not in valid_statuses:
                    return JsonResponse({'success': False, 'error': f'Status inválido: {status}'})

                # Atualizar ou criar o registro no banco de dados
                Attendance.objects.update_or_create(
                    employee_id=employee_pk,
                    date=date,
                    defaults={'status': status}
                )

            return JsonResponse({'success': True})
        except Exception as e:
            print('Erro:', str(e))  # Depuração: Exibe o erro no terminal
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método inválido'})


@csrf_exempt
def update_attendance(request, employee_pk, date):
    if request.method == 'POST':
        try:
            # Obter o novo status do formulário
            status = request.POST.get('status')

            # Validar o status
            valid_statuses = ['P', 'F', 'AT', 'AF','FE', '-']
            if status not in valid_statuses:
                return JsonResponse({'success': False, 'error': f'Status inválido: {status}'})

            # Atualizar ou criar o registro no banco de dados
            Attendance.objects.update_or_create(
                employee_id=employee_pk,
                date=date,
                defaults={'status': status}
            )

            return JsonResponse({'success': True})
        except Exception as e:
            print('Erro:', str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método inválido'})













