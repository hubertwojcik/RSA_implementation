#!/usr/bin/env python3
"""
Moduł eksperymentu faktoryzacji RSA.
"""

import time
from dataclasses import dataclass
from typing import List, Tuple

import sympy


# Parametry eksperymentu
BIT_LENGTHS = [32, 40, 48, 56, 64, 72, 80, 88, 96, 128]
SAMPLES_PER_SIZE = 1


@dataclass
class FactorRecord:
    """Rekord wyników faktoryzacji."""
    bit_length: int
    method: str      # np. "sympy" / "gmpy2"
    n: int
    p: int
    q: int
    time_sec: float
    iterations: int  # dla bibliotek – wpisz -1
    success: bool


class FactorizationExperiment:
    """Klasa do przeprowadzania eksperymentów faktoryzacji."""
    
    def __init__(self, bit_lengths: List[int] = None, samples_per_size: int = None):
        """
        Inicjalizuje eksperyment faktoryzacji.
        
        Args:
            bit_lengths: Lista długości kluczy do przetestowania
            samples_per_size: Liczba próbek dla każdej długości klucza
        """
        self.bit_lengths = bit_lengths if bit_lengths is not None else BIT_LENGTHS
        self.samples_per_size = samples_per_size if samples_per_size is not None else SAMPLES_PER_SIZE
    
    @staticmethod
    def generate_semiprime_for_bits(bit_length: int) -> Tuple[int, int, int]:
        """
        Generuje półpierwszą liczbę n = p * q o zadanej długości bitowej.
        
        Args:
            bit_length: Docelowa długość modułu n w bitach
        
        Returns:
            Krotka (n, p, q) gdzie n = p * q
        """
        prime_bits = bit_length // 2
        
        min_prime = 2 ** (prime_bits - 1)
        max_prime = 2 ** prime_bits - 1
        
        p = sympy.randprime(min_prime, max_prime)
        q = sympy.randprime(min_prime, max_prime)
        
        # Upewnij się, że p i q są różne
        while p == q:
            q = sympy.randprime(min_prime, max_prime)
        
        n = p * q
        
        # Jeśli n jest za krótkie, zwiększ liczby pierwsze
        if n.bit_length() < bit_length:
            p = sympy.nextprime(p)
            q = sympy.nextprime(q)
            n = p * q
        
        return (n, p, q)
    
    @staticmethod
    def factor_with_sympy(n: int) -> Tuple[List[int], float, int, bool]:
        """
        Faktoryzuje liczbę n używając sympy.factorint.
        
        Args:
            n: Liczba do faktoryzacji
        
        Returns:
            Krotka (factors, time_sec, iterations, success):
            - factors: Lista czynników pierwszych [p, q]
            - time_sec: Czas faktoryzacji w sekundach
            - iterations: -1 (biblioteka nie zwraca liczby iteracji)
            - success: True jeśli faktoryzacja się powiodła i iloczyn = n
        """
        start = time.perf_counter()
        factors_dict = sympy.factorint(n)
        end = time.perf_counter()
        time_sec = end - start
        
        # Konwertuj słownik czynników na listę (uwzględniając wykładniki)
        factors = []
        for prime, exponent in factors_dict.items():
            factors.extend([prime] * exponent)
        
        # Sprawdź, czy mamy dokładnie 2 czynniki pierwsze (p i q)
        if len(factors) != 2:
            return (factors, time_sec, -1, False)
        
        p, q = factors[0], factors[1]
        
        # Sprawdź, czy iloczyn czynników = n
        if p * q != n:
            return (factors, time_sec, -1, False)
        
        return ([p, q], time_sec, -1, True)
    
    def run(self) -> List[FactorRecord]:
        """
        Uruchamia eksperyment faktoryzacji dla różnych długości kluczy.
        
        Returns:
            Lista rekordów FactorRecord z wynikami eksperymentu
        """
        records = []
        
        print("\n" + "="*60)
        print("EKSPERYMENT Z FAKTORYZACJĄ RSA")
        print("="*60)
        
        for bit_length in self.bit_lengths:
            print(f"\nDługość klucza: {bit_length} bitów")
            
            for sample_num in range(1, self.samples_per_size + 1):
                # Generuj półpierwszą liczbę
                n, p_true, q_true = self.generate_semiprime_for_bits(bit_length)
                
                # Faktoryzuj używając sympy
                factors, time_sec, iterations, success = self.factor_with_sympy(n)
                
                if success:
                    p_found, q_found = factors[0], factors[1]
                else:
                    p_found, q_found = 0, 0
                
                # Zapisz rekord
                record = FactorRecord(
                    bit_length=bit_length,
                    method="sympy",
                    n=n,
                    p=p_found,
                    q=q_found,
                    time_sec=time_sec,
                    iterations=iterations,
                    success=success
                )
                records.append(record)
                
                # Krótkie logowanie
                status = "✓" if success else "✗"
                print(f"  Próbka {sample_num}/{self.samples_per_size}: {status} "
                      f"czas={time_sec:.6f}s, n={n.bit_length()} bitów")
        
        return records


