#!/usr/bin/env python3
"""
Moduł do wizualizacji wyników faktoryzacji.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List

from factorization import FactorRecord


class Visualization:
    """Klasa do tworzenia wykresów wyników faktoryzacji."""
    
    def __init__(self, extrapolation_bits: List[int] = None):
        """
        Inicjalizuje obiekt wizualizacji.
        
        Args:
            extrapolation_bits: Lista długości kluczy do ekstrapolacji
        """
        self.extrapolation_bits = extrapolation_bits if extrapolation_bits is not None else [256, 512]
    
    def plot_factorization_results(
        self, 
        records: List[FactorRecord], 
        filename: str = "factorization_times.png"
    ):
        """
        Rysuje wykres średnich czasów faktoryzacji w zależności od długości klucza.
        
        Dodaje dopasowania krzywych: liniową, potęgową i wykładniczą.
        Ekstrapoluje czasy dla określonych długości bitowych.
        
        Args:
            records: Lista rekordów z wynikami
            filename: Nazwa pliku z wykresem
        """
        # Pogrupuj rekordy po (bit_length, method)
        grouped = {}
        for record in records:
            key = (record.bit_length, record.method)
            if key not in grouped:
                grouped[key] = []
            if record.success:  # Tylko udane próbki
                grouped[key].append(record.time_sec)
        
        # Oblicz średnie czasy dla każdej pary (bit_length, method)
        methods = sorted(set(r.method for r in records))
        bit_lengths = sorted(set(r.bit_length for r in records))
        
        plt.figure(figsize=(14, 10))
        
        # Flaga do oznaczenia, czy już dodaliśmy etykietę ekstrapolacji
        extrapolation_labeled = False
        
        for method in methods:
            avg_times = []
            valid_bit_lengths = []
            for bit_length in bit_lengths:
                key = (bit_length, method)
                if key in grouped and grouped[key]:
                    avg_time = np.mean(grouped[key])
                    avg_times.append(avg_time)
                    valid_bit_lengths.append(bit_length)
            
            if not valid_bit_lengths:
                continue
            
            # Konwertuj na numpy arrays
            x_data = np.array(valid_bit_lengths)
            y_data = np.array(avg_times)
            
            # Rysuj dane eksperymentalne
            plt.plot(x_data, y_data, marker='o', label=f'Dane eksperymentalne ({method})', 
                    linewidth=2, markersize=8)
            
            # Dopasowania krzywych
            try:
                # 1. Dopasowanie liniowe: y = a*x + b
                linear_coeffs = np.polyfit(x_data, y_data, 1)
                linear_func = np.poly1d(linear_coeffs)
                x_fit = np.linspace(min(x_data), max(x_data), 200)
                y_linear = linear_func(x_fit)
                plt.plot(x_fit, y_linear, '--', label=f'Dopasowanie liniowe ({method})', 
                        linewidth=1.5, alpha=0.7)
                
                # 2. Dopasowanie potęgowe: y = a * x^b
                mask = (x_data > 0) & (y_data > 0)
                if np.sum(mask) >= 3:  # Potrzebujemy co najmniej 3 punktów
                    x_log = np.log(x_data[mask])
                    y_log = np.log(y_data[mask])
                    power_coeffs = np.polyfit(x_log, y_log, 1)
                    a_power = np.exp(power_coeffs[1])
                    b_power = power_coeffs[0]
                    y_power = a_power * (x_fit ** b_power)
                    plt.plot(x_fit, y_power, '--', 
                            label=f'Dopasowanie potęgowe ({method}): y={a_power:.2e}*x^{b_power:.2f}', 
                            linewidth=1.5, alpha=0.7)
                else:
                    a_power, b_power = None, None
                
                # 3. Dopasowanie wykładnicze: y = a * exp(b*x)
                mask = y_data > 0
                if np.sum(mask) >= 3:
                    y_log = np.log(y_data[mask])
                    exp_coeffs = np.polyfit(x_data[mask], y_log, 1)
                    a_exp = np.exp(exp_coeffs[1])
                    b_exp = exp_coeffs[0]
                    y_exp = a_exp * np.exp(b_exp * x_fit)
                    plt.plot(x_fit, y_exp, '--', 
                            label=f'Dopasowanie wykładnicze ({method}): y={a_exp:.2e}*exp({b_exp:.4f}*x)', 
                            linewidth=1.5, alpha=0.7)
                else:
                    a_exp, b_exp = None, None
                
                # Ekstrapolacja
                print(f"\n{'='*60}")
                print(f"EKSTRAPOLACJA DLA METODY: {method}")
                print(f"{'='*60}")
                
                for ext_bits in self.extrapolation_bits:
                    print(f"\nDługość klucza: {ext_bits} bitów")
                    
                    # Liniowa
                    time_linear = linear_func(ext_bits)
                    if time_linear > 0:
                        print(f"  Liniowa:     {time_linear:.6e} s = {time_linear/3600:.2f} h = {time_linear/(3600*24):.2f} dni")
                    
                    # Potęgowa
                    if a_power is not None and b_power is not None:
                        time_power = a_power * (ext_bits ** b_power)
                        if time_power > 0:
                            print(f"  Potęgowa:    {time_power:.6e} s = {time_power/3600:.2f} h = {time_power/(3600*24):.2f} dni")
                    
                    # Wykładnicza
                    if a_exp is not None and b_exp is not None:
                        time_exp = a_exp * np.exp(b_exp * ext_bits)
                        if time_exp > 0:
                            years = time_exp / (3600 * 24 * 365.25)
                            if years < 1:
                                print(f"  Wykładnicza: {time_exp:.6e} s = {time_exp/3600:.2f} h = {time_exp/(3600*24):.2f} dni")
                            else:
                                print(f"  Wykładnicza: {time_exp:.6e} s = {years:.2e} lat")
                
                # Rysuj punkty ekstrapolacji
                for ext_bits in self.extrapolation_bits:
                    if linear_func(ext_bits) > 0:
                        if not extrapolation_labeled:
                            bits_str = ', '.join(map(str, self.extrapolation_bits))
                            plt.plot(ext_bits, linear_func(ext_bits), 's', color='red', 
                                    markersize=10, markerfacecolor='none', markeredgewidth=2, 
                                    label=f'Ekstrapolacja ({bits_str} bity)')
                            extrapolation_labeled = True
                        else:
                            plt.plot(ext_bits, linear_func(ext_bits), 's', color='red', 
                                    markersize=10, markerfacecolor='none', markeredgewidth=2)
            
            except Exception as e:
                print(f"Ostrzeżenie: Nie udało się dopasować krzywych dla {method}: {e}")
        
        plt.xlabel('Długość klucza (bity)', fontsize=12)
        plt.ylabel('Średni czas faktoryzacji (sekundy)', fontsize=12)
        plt.title('Czas faktoryzacji RSA z dopasowaniami krzywych i ekstrapolacją', 
                  fontsize=14, fontweight='bold')
        plt.legend(fontsize=9, loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.yscale('log')  # Skala logarytmiczna dla lepszej czytelności
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✓ Wykres zapisany do pliku: {filename}")
        
        
        
    
