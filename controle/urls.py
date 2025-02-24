from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Página inicial
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('employee/add/', views.add_employee, name='add_employee'),
    path('employee_list/', views.employee_list, name='employee_list'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/<int:employee_pk>/add_warning/', views.add_warning, name='add_warning'),
    path('warning/<int:warning_pk>/add_attachment/', views.add_attachment, name='add_attachment'),
    path('attachment/<int:attachment_pk>/delete/', views.delete_attachment, name='delete_attachment'),
    path('employee/<int:employee_pk>/delete/', views.delete_employee, name='delete_employee'),
    path('attendance/', views.attendance_table, name='attendance_table'),  # Certifique-se de que o nome está correto
    path('attendance/update/<int:employee_pk>/<str:date>/', views.update_attendance, name='update_attendance'),
    path('attendance/export/', views.export_attendance_to_excel, name='export_attendance'),
]