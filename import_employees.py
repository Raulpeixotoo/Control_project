import os
import django
import csv

# Configurar o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jad_controle.settings') 
django.setup()

from controle.models import Employee  

def import_employees(file_path):
    try:
        # Abrir o arquivo com a codificação correta (ISO-8859-1 ou outra detectada)
        with open(file_path, newline='', encoding='ISO-8859-1') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                Employee.objects.create(
                    matricula=row['matricula']or None,
                    name=row['name'],
                    position=row['position']or None,
                    department=row['department']or None,
                    admission_date=row['admission_date'] or None,  # Tratar campos vazios
                    shift=row['shift']
                )
        print("Funcionários importados com sucesso!")
    except Exception as e:
        print(f"Erro ao importar funcionários: {e}")

if __name__ == "__main__":
    file_path = 'data/employees.csv'  
    import_employees(file_path)