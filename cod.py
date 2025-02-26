import chardet

file_path = 'data/employees.csv'  # Altere conforme necessário
with open(file_path, 'rb') as f:
    result = chardet.detect(f.read())
    print(result)