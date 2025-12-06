#!/usr/bin/env python3
"""
Skrypt do obliczenia ekstrapolacji dla 256 i 512 bitów na podstawie danych z CSV.
"""

import csv
import numpy as np
from collections import defaultdict

def load_csv(filename):
    """Wczytuje dane z pliku CSV."""
    records = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['success']) == 1:  # Tylko udane próbki
                records.append({
                    'bit_length': int(row['bit_length']),
                    'method': row['method'],
                    'time_sec': float(row['time_sec'])
                })
    return records

def calculate_extrapolation(records):
    """Oblicza ekstrapolacje dla 256 i 512 bitów."""
    # Grupuj po metodzie
    methods = sorted(set(r['method'] for r in records))
    
    for method in methods:
        method_records = [r for r in records if r['method'] == method]
        
        # Grupuj po długości klucza i oblicz średnie
        grouped = defaultdict(list)
        for record in method_records:
            grouped[record['bit_length']].append(record['time_sec'])
        
        # Oblicz średnie czasy
        bit_lengths = sorted(grouped.keys())
        avg_times = [np.mean(grouped[bl]) for bl in bit_lengths]
        
        # Konwertuj na numpy arrays
        x_data = np.array(bit_lengths)
        y_data = np.array(avg_times)
        
        print(f"\n{'='*60}")
        print(f"EKSTRAPOLACJA DLA METODY: {method}")
        print(f"{'='*60}")
        print(f"\nDane eksperymentalne:")
        for bl, time in zip(bit_lengths, avg_times):
            print(f"  {bl} bitów: {time:.6e} s")
        
        # Dopasowania krzywych
        try:
            # 1. Dopasowanie liniowe: y = a*x + b
            linear_coeffs = np.polyfit(x_data, y_data, 1)
            linear_func = np.poly1d(linear_coeffs)
            
            # 2. Dopasowanie potęgowe: y = a * x^b
            mask = (x_data > 0) & (y_data > 0)
            if np.sum(mask) >= 3:
                x_log = np.log(x_data[mask])
                y_log = np.log(y_data[mask])
                power_coeffs = np.polyfit(x_log, y_log, 1)
                a_power = np.exp(power_coeffs[1])
                b_power = power_coeffs[0]
            else:
                a_power, b_power = None, None
            
            # 3. Dopasowanie wykładnicze: y = a * exp(b*x)
            mask = y_data > 0
            if np.sum(mask) >= 3:
                y_log = np.log(y_data[mask])
                exp_coeffs = np.polyfit(x_data[mask], y_log, 1)
                a_exp = np.exp(exp_coeffs[1])
                b_exp = exp_coeffs[0]
            else:
                a_exp, b_exp = None, None
            
            # Ekstrapolacja dla 256 i 512 bitów
            extrapolation_bits = [256, 512]
            
            # Przygotuj dane do tabeli
            table_data = []
            
            for ext_bits in extrapolation_bits:
                row = {'bits': ext_bits}
                
                # Liniowa
                time_linear = linear_func(ext_bits)
                if time_linear > 0:
                    hours = time_linear / 3600
                    days = time_linear / (3600 * 24)
                    years = time_linear / (3600 * 24 * 365.25)
                    if years >= 1:
                        row['linear'] = f"{years:.2e} lat"
                    elif days >= 1:
                        row['linear'] = f"{days:.2f} dni"
                    elif hours >= 1:
                        row['linear'] = f"{hours:.2f} h"
                    else:
                        row['linear'] = f"{time_linear:.3f} s"
                else:
                    row['linear'] = "N/A"
                
                # Potęgowa
                if a_power is not None and b_power is not None:
                    time_power = a_power * (ext_bits ** b_power)
                    if time_power > 0:
                        hours = time_power / 3600
                        days = time_power / (3600 * 24)
                        years = time_power / (3600 * 24 * 365.25)
                        if years >= 1:
                            row['power'] = f"{years:.2e} lat"
                        elif days >= 1:
                            row['power'] = f"{days:.2f} dni"
                        elif hours >= 1:
                            row['power'] = f"{hours:.2f} h"
                        else:
                            row['power'] = f"{time_power:.3f} s"
                    else:
                        row['power'] = "N/A"
                else:
                    row['power'] = "N/A"
                
                # Wykładnicza
                if a_exp is not None and b_exp is not None:
                    time_exp = a_exp * np.exp(b_exp * ext_bits)
                    if time_exp > 0:
                        hours = time_exp / 3600
                        days = time_exp / (3600 * 24)
                        years = time_exp / (3600 * 24 * 365.25)
                        if years >= 1:
                            row['exp'] = f"{years:.2e} lat"
                        elif days >= 1:
                            row['exp'] = f"{days:.2f} dni"
                        elif hours >= 1:
                            row['exp'] = f"{hours:.2f} h"
                        else:
                            row['exp'] = f"{time_exp:.3f} s"
                    else:
                        row['exp'] = "N/A"
                else:
                    row['exp'] = "N/A"
                
                table_data.append(row)
            
            # Wyświetl tabelę
            print(f"\n{'='*100}")
            print(f"TABELA EKSTRAPOLACJI - METODA: {method.upper()}")
            print(f"{'='*100}")
            print(f"\n{'Długość klucza':<20} {'Model liniowy':<25} {'Model potęgowy':<25} {'Model wykładniczy':<25}")
            print("-" * 100)
            
            for row in table_data:
                print(f"{row['bits']:<20} {row['linear']:<25} {row['power']:<25} {row['exp']:<25}")
            
            print(f"\n{'='*100}")
            print(f"Parametry modeli:")
            print(f"  Potęgowy: y = {a_power:.2e} * x^{b_power:.2f}" if a_power is not None else "  Potęgowy: N/A")
            print(f"  Wykładniczy: y = {a_exp:.2e} * exp({b_exp:.4f} * x)" if a_exp is not None else "  Wykładniczy: N/A")
            print(f"{'='*100}")
        
        except Exception as e:
            print(f"Błąd podczas obliczania ekstrapolacji: {e}")

def main():
    filename = "factorization_results.csv"
    records = load_csv(filename)
    
    if not records:
        print(f"Błąd: Brak danych w pliku {filename}")
        return
    
    calculate_extrapolation(records)

if __name__ == "__main__":
    main()

