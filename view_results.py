#!/usr/bin/env python3
"""
Skrypt do czytelnego wyświetlania wyników faktoryzacji z pliku CSV.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

def format_time(seconds):
    """Formatuje czas w sekundach na czytelną formę."""
    if seconds < 0.001:
        return f"{seconds*1000:.3f} ms"
    elif seconds < 1:
        return f"{seconds*1000:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.3f} s"
    elif seconds < 3600:
        return f"{seconds/60:.2f} min ({seconds:.3f} s)"
    else:
        return f"{seconds/3600:.2f} h ({seconds:.3f} s)"


def load_csv(filename):
    """Wczytuje dane z pliku CSV."""
    records = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'bit_length': int(row['bit_length']),
                'method': row['method'],
                'n': int(row['n']),
                'p': int(row['p']),
                'q': int(row['q']),
                'time_sec': float(row['time_sec']),
                'iterations': int(row['iterations']),
                'success': bool(int(row['success']))
            })
    return records


def display_table(records):
    """Wyświetla dane w formie czytelnej tabeli."""
    print("\n" + "="*120)
    print("WYNIKI EKSPERYMENTU FAKTORYZACJI RSA")
    print("="*120)
    
    # Sortuj po długości klucza
    records_sorted = sorted(records, key=lambda x: (x['bit_length'], x['method']))
    
    # Nagłówek tabeli
    print(f"\n{'Długość':<10} {'Metoda':<8} {'Czas':<25} {'Sukces':<8} {'n (bity)':<12} {'p':<20} {'q':<20}")
    print("-" * 120)
    
    # Wyświetl każdy rekord
    for record in records_sorted:
        bit_len = record['bit_length']
        method = record['method']
        time_str = format_time(record['time_sec'])
        success = "✓ TAK" if record['success'] else "✗ NIE"
        n_bits = record['n'].bit_length()
        p = record['p']
        q = record['q']
        
        print(f"{bit_len:<10} {method:<8} {time_str:<25} {success:<8} {n_bits:<12} {p:<20} {q:<20}")


def display_statistics(records):
    """Wyświetla statystyki z wyników."""
    print("\n" + "="*120)
    print("STATYSTYKI")
    print("="*120)
    
    # Grupuj po długości klucza
    grouped = defaultdict(list)
    for record in records:
        if record['success']:
            grouped[record['bit_length']].append(record['time_sec'])
    
    print(f"\n{'Długość klucza':<20} {'Liczba próbek':<20} {'Średni czas':<25} {'Min czas':<25} {'Max czas':<25}")
    print("-" * 120)
    
    for bit_length in sorted(grouped.keys()):
        times = grouped[bit_length]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"{bit_length} bitów{'':<15} {len(times):<20} {format_time(avg_time):<25} "
              f"{format_time(min_time):<25} {format_time(max_time):<25}")
    
    # Statystyki ogólne
    all_times = [r['time_sec'] for r in records if r['success']]
    total_samples = len(records)
    successful = sum(1 for r in records if r['success'])
    
    print("\n" + "-" * 120)
    print(f"Łączna liczba próbek: {total_samples}")
    print(f"Udanych faktoryzacji: {successful} ({100*successful/total_samples:.1f}%)")
    if all_times:
        print(f"Średni czas faktoryzacji: {format_time(sum(all_times)/len(all_times))}")
        print(f"Najszybsza faktoryzacja: {format_time(min(all_times))}")
        print(f"Najwolniejsza faktoryzacja: {format_time(max(all_times))}")


def display_by_method(records):
    """Wyświetla wyniki pogrupowane po metodzie."""
    methods = sorted(set(r['method'] for r in records))
    
    for method in methods:
        method_records = [r for r in records if r['method'] == method]
        print(f"\n{'='*120}")
        print(f"METODA: {method.upper()}")
        print("="*120)
        
        # Grupuj po długości klucza
        grouped = defaultdict(list)
        for record in method_records:
            if record['success']:
                grouped[record['bit_length']].append(record['time_sec'])
        
        print(f"\n{'Długość klucza':<20} {'Próbek':<10} {'Średni czas':<25} {'Min':<25} {'Max':<25}")
        print("-" * 120)
        
        for bit_length in sorted(grouped.keys()):
            times = grouped[bit_length]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"{bit_length} bitów{'':<15} {len(times):<10} {format_time(avg_time):<25} "
                  f"{format_time(min_time):<25} {format_time(max_time):<25}")


def main():
    """Główna funkcja."""
    filename = "factorization_results.csv"
    
    if not Path(filename).exists():
        print(f"Błąd: Plik {filename} nie istnieje!")
        print("Najpierw uruchom eksperyment faktoryzacji:")
        print("  python3 rsa_implementation.py message.txt --skip-rsa")
        sys.exit(1)
    
    # Wczytaj dane
    records = load_csv(filename)
    
    if not records:
        print(f"Błąd: Plik {filename} jest pusty lub nie zawiera danych!")
        sys.exit(1)
    
    # Wyświetl opcje
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        print("\nWybierz tryb wyświetlania:")
        print("  1 - Tabela szczegółowa (wszystkie rekordy)")
        print("  2 - Statystyki (podsumowanie)")
        print("  3 - Pogrupowane po metodzie")
        print("  4 - Wszystko")
        mode = input("\nWybór (1-4, domyślnie 4): ").strip() or "4"
    
    # Wyświetl dane
    if mode in ["1", "4"]:
        display_table(records)
    
    if mode in ["2", "4"]:
        display_statistics(records)
    
    if mode in ["3", "4"]:
        display_by_method(records)
    
    print("\n" + "="*120)


if __name__ == "__main__":
    main()

