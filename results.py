#!/usr/bin/env python3
"""
Moduł do zapisu i odczytu wyników faktoryzacji.
"""

import csv
from typing import List

from factorization import FactorRecord


class ResultsManager:
    """Klasa do zarządzania wynikami faktoryzacji."""
    
    @staticmethod
    def save_to_csv(records: List[FactorRecord], filename: str = "factorization_results.csv"):
        """
        Zapisuje wyniki faktoryzacji do pliku CSV.
        
        CSV zawiera kolumny:
        - bit_length: Długość klucza w bitach
        - method: Metoda faktoryzacji ("sympy")
        - n: Moduł RSA
        - p: Pierwszy czynnik pierwszy
        - q: Drugi czynnik pierwszy
        - time_sec: Czas faktoryzacji w sekundach
        - iterations: Liczba iteracji (-1 dla bibliotek)
        - success: 1 jeśli sukces, 0 jeśli niepowodzenie
        
        Args:
            records: Lista rekordów do zapisania
            filename: Nazwa pliku CSV
        """
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Nagłówek
            writer.writerow([
                'bit_length', 'method', 'n', 'p', 'q', 
                'time_sec', 'iterations', 'success'
            ])
            
            # Dane
            for record in records:
                writer.writerow([
                    record.bit_length,
                    record.method,
                    record.n,
                    record.p,
                    record.q,
                    f"{record.time_sec:.10f}",
                    record.iterations,
                    1 if record.success else 0
                ])
        
        print(f"\n✓ Wyniki zapisane do pliku: {filename}")
    
    @staticmethod
    def load_from_csv(filename: str = "factorization_results.csv") -> List[FactorRecord]:
        """
        Wczytuje wyniki faktoryzacji z pliku CSV.
        
        Args:
            filename: Nazwa pliku CSV
        
        Returns:
            Lista rekordów FactorRecord
        """
        records = []
        
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = FactorRecord(
                    bit_length=int(row['bit_length']),
                    method=row['method'],
                    n=int(row['n']),
                    p=int(row['p']),
                    q=int(row['q']),
                    time_sec=float(row['time_sec']),
                    iterations=int(row['iterations']),
                    success=bool(int(row['success']))
                )
                records.append(record)
        
        return records


