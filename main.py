#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='Обработка логов')
    parser.add_argument('--file', nargs='+', required=True, help='Файл(ы) логов')
    parser.add_argument('--report', choices=['average'], default='average', help='Тип отчета')
    parser.add_argument('--date', help='Фильтр по дате')
    return parser.parse_args()

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except:
        return False

def process_logs(file_paths, date_filter=None):
    # Словарь для хранения статистики
    stats = defaultdict(lambda: {'count': 0, 'total_time': 0.0})
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Проверяем пустую строку
                        if not line.strip():
                            continue
                            
                        # Парсим JSON
                        data = json.loads(line.strip())
                        
                        # Фильтр по дате если указан
                        if date_filter:
                            timestamp = data.get('@timestamp', '')
                            if timestamp:
                                date_part = timestamp.split('T')[0]
                                if date_part != date_filter:
                                    continue
                        
                        # Получаем данные (соответствует вашему формату)
                        endpoint = data.get('url', '/')
                        response_time = data.get('response_time', 0.0)
                        
                        # Собираем статистику
                        stats[endpoint]['count'] += 1
                        stats[endpoint]['total_time'] += response_time
                        
                    except json.JSONDecodeError:
                        # Пропускаем невалидные строки
                        continue
                    except Exception as e:
                        # Пропускаем ошибочные строки
                        continue
                        
        except FileNotFoundError:
            print(f"Ошибка: Файл {file_path} не найден", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Ошибка чтения файла {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    return stats

def generate_report(stats):
    # Создаем список для отчета
    report = []
    
    # Вычисляем среднее время для каждого эндпоинта
    for endpoint, data in stats.items():
        if data['count'] > 0:
            avg_time = data['total_time'] / data['count']
            report.append((endpoint, data['count'], round(avg_time, 3)))
    
    # Сортируем по имени эндпоинта
    report.sort(key=lambda x: x[0])
    return report

def print_report(report_data):
    try:
        # Пытаемся использовать tabulate для красивого вывода
        from tabulate import tabulate
        headers = ['Endpoint', 'Requests', 'Avg Response Time']
        table_data = [[item[0], item[1], f"{item[2]}ms"] for item in report_data]
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    except ImportError:
        # Если tabulate не установлен - выводим вручную
        print("Endpoint".ljust(30) + "Requests".ljust(10) + "Avg Response Time")
        print("-" * 50)
        for endpoint, count, avg_time in report_data:
            print(f"{endpoint}".ljust(30) + f"{count}".ljust(10) + f"{avg_time}ms")

def main():
    # Парсим аргументы
    args = parse_args()
    
    # Проверяем дату
    if args.date and not validate_date(args.date):
        print("Ошибка: Неверный формат даты. Используйте YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)
    
    # Обрабатываем логи
    stats = process_logs(args.file, args.date)
    
    # Генерируем отчет
    report = generate_report(stats)
    
    # Выводим результат
    print_report(report)

if __name__ == '__main__':
    main()