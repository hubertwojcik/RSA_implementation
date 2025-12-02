#!/usr/bin/env python3
"""
Kompletna implementacja RSA z eksperymentem faktoryzacji.

Część I: Implementacja RSA
- Generowanie kluczy RSA
- Szyfrowanie i deszyfrowanie wiadomości
- Obsługa różnych alfabetów (26, 64, ASCII)
- Podział wiadomości na bloki

Część II: Eksperyment z faktoryzacją
- Faktoryzacja modułów RSA o różnych długościach
- Pomiar czasu faktoryzacji
- Zapis wyników do CSV
- Generowanie wykresów
"""

import time
import math
import random
import csv
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

import sympy
from sympy import mod_inverse
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


# ============================================================================
# ALFABETY
# ============================================================================

ALPHABET_26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABET_64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
ALPHABET_ASCII = ''.join(chr(i) for i in range(256))

ALPHABETS = {
    "26": ALPHABET_26,
    "64": ALPHABET_64,
    "ascii": ALPHABET_ASCII
}


def get_alphabet(choice: str) -> str:
    """
    Zwraca alfabet na podstawie wyboru użytkownika.
    
    Args:
        choice: "26", "64" lub "ascii"
    
    Returns:
        String zawierający alfabet
    """
    if choice not in ALPHABETS:
        raise ValueError(f"Nieprawidłowy wybór alfabetu: {choice}. Dozwolone: {list(ALPHABETS.keys())}")
    return ALPHABETS[choice]


# ============================================================================
# WCZYTYWANIE I PRZETWARZANIE WIADOMOŚCI
# ============================================================================

def read_message(path: str, alphabet: str) -> str:
    """
    Czyta wiadomość z pliku i normalizuje ją do wybranego alfabetu.
    
    Dla alfabetu 26: zamienia na wielkie litery i usuwa znaki spoza alfabetu.
    Dla alfabetu 64: usuwa znaki spoza alfabetu.
    Dla ASCII: czyta wszystkie znaki z zakresu 0-255 (konwertuje Unicode na ASCII).
    
    Args:
        path: Ścieżka do pliku z wiadomością
        alphabet: Alfabet docelowy
    
    Returns:
        Znormalizowana wiadomość
    """
    with open(path, 'rb') as f:
        content_bytes = f.read()
    
    if alphabet == ALPHABET_26:
        # Dla alfabetu 26, czytaj jako tekst i normalizuj
        try:
            content = content_bytes.decode('utf-8', errors='ignore')
        except:
            content = content_bytes.decode('latin-1', errors='ignore')
        # Zamień na wielkie litery i zostaw tylko litery z alfabetu
        normalized = ''.join(c.upper() for c in content if c.upper() in ALPHABET_26)
    elif alphabet == ALPHABET_64:
        # Dla alfabetu 64, czytaj jako tekst
        try:
            content = content_bytes.decode('utf-8', errors='ignore')
        except:
            content = content_bytes.decode('latin-1', errors='ignore')
        # Zostaw tylko znaki z alfabetu 64
        normalized = ''.join(c for c in content if c in ALPHABET_64)
    else:  # ASCII
        # Dla ASCII, konwertuj bajty na znaki (0-255)
        normalized = ''.join(chr(b) for b in content_bytes)
    
    return normalized


def split_into_blocks(message: str, block_size: int = 10, alphabet: str = ALPHABET_ASCII) -> List[str]:
    """
    Dzieli wiadomość na bloki o zadanej długości.
    
    Jeśli ostatni blok jest krótszy, dopełnia go pierwszym znakiem alfabetu
    (dla ASCII będzie to chr(0), dla innych alfabetów - pierwszy znak).
    
    Args:
        message: Wiadomość do podziału
        block_size: Długość bloku (domyślnie 10)
        alphabet: Alfabet używany do dopełnienia
    
    Returns:
        Lista bloków znaków
    """
    blocks = []
    padding_char = alphabet[0] if alphabet else ' '
    
    for i in range(0, len(message), block_size):
        block = message[i:i + block_size]
        # Dopełnij ostatni blok, jeśli jest krótszy
        if len(block) < block_size:
            block = block + padding_char * (block_size - len(block))
        blocks.append(block)
    
    return blocks


# ============================================================================
# KONWERSJA BLOKÓW NA LICZBY I Z POWROTEM
# ============================================================================

def block_to_int(block: str, alphabet: str) -> int:
    """
    Konwertuje blok znaków na liczbę całkowitą.
    
    Blok jest traktowany jako zapis liczby w systemie o podstawie len(alphabet).
    Dla każdego znaku znajdujemy jego indeks w alfabecie (0..len(alphabet)-1).
    Liczba = Σ index_i * base^(k-1-i), gdzie k to długość bloku.
    
    Przykład dla alfabetu 26 i bloku "ABC":
    A=0, B=1, C=2
    liczba = 0*26^2 + 1*26^1 + 2*26^0 = 0 + 26 + 2 = 28
    
    Args:
        block: Blok znaków do konwersji
        alphabet: Alfabet używany do mapowania
    
    Returns:
        Liczba całkowita reprezentująca blok
    """
    base = len(alphabet)
    result = 0
    
    for i, char in enumerate(block):
        if char not in alphabet:
            raise ValueError(f"Znak '{char}' nie znajduje się w alfabecie")
        index = alphabet.index(char)
        # Najbardziej znaczący znak ma najwyższą potęgę
        power = len(block) - 1 - i
        result += index * (base ** power)
    
    return result


def int_to_block(value: int, alphabet: str, block_size: int) -> str:
    """
    Konwertuje liczbę całkowitą z powrotem na blok znaków.
    
    Wykonuje dzielenie i modulo przez base (len(alphabet)), aby odzyskać
    oryginalne znaki. Jest to odwrotna operacja do block_to_int.
    
    Args:
        value: Liczba do konwersji
        alphabet: Alfabet używany do mapowania
        block_size: Długość bloku wynikowego
    
    Returns:
        Blok znaków reprezentujący liczbę
    """
    base = len(alphabet)
    result = []
    
    # Konwertuj liczbę na reprezentację w systemie o podstawie base
    temp = value
    for _ in range(block_size):
        result.append(alphabet[temp % base])
        temp //= base
    
    # Odwróć, bo zaczęliśmy od najmniej znaczącej cyfry
    result.reverse()
    
    return ''.join(result)


# ============================================================================
# GENEROWANIE KLUCZY RSA
# ============================================================================

@dataclass
class RSAKeyPair:
    """Para kluczy RSA: publiczny (n, e) i prywatny (n, d)."""
    n: int  # Moduł (iloczyn p * q)
    e: int  # Wykładnik publiczny
    d: int  # Wykładnik prywatny
    p: int  # Pierwsza liczba pierwsza
    q: int  # Druga liczba pierwsza


def generate_rsa_keypair(bit_length: int = 768) -> RSAKeyPair:
    """
    Generuje parę kluczy RSA o zadanej długości bitowej.
    
    Algorytm:
    1. Generuje dwie losowe liczby pierwsze p i q, każda o długości ~bit_length/2
    2. Oblicza n = p * q (moduł)
    3. Sprawdza, czy n.bit_length() >= bit_length
    4. Wybiera standardowy wykładnik publiczny e = 65537
    5. Oblicza phi = (p-1) * (q-1) (funkcja Eulera)
    6. Oblicza wykładnik prywatny d = e^(-1) mod phi
    
    Args:
        bit_length: Docelowa długość modułu n w bitach (min. 768)
    
    Returns:
        RSAKeyPair zawierający wszystkie parametry klucza
    """
    if bit_length < 768:
        raise ValueError("Minimalna długość klucza to 768 bitów")
    
    # Długość każdej liczby pierwszej to około połowa docelowej długości
    prime_bits = bit_length // 2
    
    # Generuj p i q jako losowe liczby pierwsze
    # Używamy randprime do generowania losowej liczby pierwszej w zakresie
    min_prime = 2 ** (prime_bits - 1)
    max_prime = 2 ** prime_bits - 1
    
    p = sympy.randprime(min_prime, max_prime)
    q = sympy.randprime(min_prime, max_prime)
    
    # Upewnij się, że p i q są różne
    while p == q:
        q = sympy.randprime(min_prime, max_prime)
    
    n = p * q
    
    # Sprawdź długość bitową n
    if n.bit_length() < bit_length:
        # Jeśli n jest za krótkie, wygeneruj większe liczby pierwsze
        p = sympy.nextprime(p)
        q = sympy.nextprime(q)
        n = p * q
    
    # Standardowy wykładnik publiczny
    e = 65537
    
    # Funkcja Eulera
    phi = (p - 1) * (q - 1)
    
    # Sprawdź, czy e i phi są względnie pierwsze
    if math.gcd(e, phi) != 1:
        # Jeśli nie, wybierz inne e (rzadko się zdarza dla e=65537)
        e = 3
        while math.gcd(e, phi) != 1:
            e += 2
    
    # Oblicz wykładnik prywatny d = e^(-1) mod phi
    d = mod_inverse(e, phi)
    
    return RSAKeyPair(n=n, e=e, d=d, p=p, q=q)


# ============================================================================
# SZYFROWANIE I DESZYFROWANIE
# ============================================================================

def encrypt_block(m_int: int, n: int, e: int) -> int:
    """
    Szyfruje pojedynczy blok (liczbę) używając klucza publicznego.
    
    Szyfrowanie: c = m^e mod n
    
    Args:
        m_int: Liczba reprezentująca blok wiadomości (musi być < n)
        n: Moduł RSA
        e: Wykładnik publiczny
    
    Returns:
        Zaszyfrowana liczba
    """
    if m_int >= n:
        raise ValueError(f"Wiadomość {m_int} jest większa lub równa modułowi {n}")
    return pow(m_int, e, n)


def decrypt_block(c_int: int, n: int, d: int) -> int:
    """
    Deszyfruje pojedynczy blok (liczbę) używając klucza prywatnego.
    
    Deszyfrowanie: m = c^d mod n
    
    Args:
        c_int: Liczba reprezentująca zaszyfrowany blok
        n: Moduł RSA
        d: Wykładnik prywatny
    
    Returns:
        Odszyfrowana liczba
    """
    return pow(c_int, d, n)


def encrypt_message_blocks(blocks: List[str], key: RSAKeyPair, alphabet: str) -> List[int]:
    """
    Szyfruje listę bloków znaków używając klucza RSA.
    
    Dla każdego bloku:
    1. Konwertuje blok na liczbę (block_to_int)
    2. Sprawdza, czy liczba < n (warunek RSA)
    3. Szyfruje blok (encrypt_block)
    
    Args:
        blocks: Lista bloków znaków do zaszyfrowania
        key: Para kluczy RSA
        alphabet: Alfabet używany do konwersji
    
    Returns:
        Lista zaszyfrowanych liczb
    """
    cipher_blocks = []
    
    for block in blocks:
        m_int = block_to_int(block, alphabet)
        
        if m_int >= key.n:
            raise ValueError(
                f"Blok '{block}' konwertuje się na liczbę {m_int}, "
                f"która jest >= n={key.n}. Zwiększ długość klucza lub zmniejsz rozmiar bloku."
            )
        
        c_int = encrypt_block(m_int, key.n, key.e)
        cipher_blocks.append(c_int)
    
    return cipher_blocks


def decrypt_message_blocks(
    cipher_blocks: List[int], 
    key: RSAKeyPair, 
    alphabet: str, 
    block_size: int = 10
) -> List[str]:
    """
    Deszyfruje listę zaszyfrowanych liczb z powrotem na bloki znaków.
    
    Dla każdej zaszyfrowanej liczby:
    1. Deszyfruje liczbę (decrypt_block)
    2. Konwertuje liczbę z powrotem na blok znaków (int_to_block)
    
    Args:
        cipher_blocks: Lista zaszyfrowanych liczb
        key: Para kluczy RSA
        alphabet: Alfabet używany do konwersji
        block_size: Długość bloku znaków
    
    Returns:
        Lista odszyfrowanych bloków znaków
    """
    decrypted_blocks = []
    
    for c_int in cipher_blocks:
        m_int = decrypt_block(c_int, key.n, key.d)
        block = int_to_block(m_int, alphabet, block_size)
        decrypted_blocks.append(block)
    
    return decrypted_blocks


# ============================================================================
# CZĘŚĆ II: EKSPERYMENT Z FAKTORYZACJĄ
# ============================================================================

# Parametry eksperymentu
BIT_LENGTHS = [32, 40, 48, 56, 64, 72, 80, 88, 96, 128,]
SAMPLES_PER_SIZE = 5


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


def generate_semiprime_for_bits(bit_length: int) -> Tuple[int, int, int]:
    """
    Generuje półpierwszą liczbę n = p * q o zadanej długości bitowej.
    
    Używane do eksperymentu faktoryzacji - generuje mniejsze klucze niż
    standardowa implementacja RSA.
    
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


def factor_with_sympy(n: int) -> Tuple[List[int], float, int, bool]:
    """
    Faktoryzuje liczbę n używając sympy.factorint.
    
    Mierzy czas faktoryzacji i zwraca czynniki pierwsze.
    Ponieważ factorint nie zwraca liczby iteracji, ustawiamy iterations = -1.
    
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


def run_factorization_experiment() -> List[FactorRecord]:
    """
    Uruchamia eksperyment faktoryzacji dla różnych długości kluczy.
    
    Dla każdej długości bitowej z BIT_LENGTHS:
    - Generuje SAMPLES_PER_SIZE losowych półpierwszych liczb
    - Próbuje zfaktoryzować każdą używając sympy
    - Zapisuje wyniki (czas, sukces, czynniki)
    
    Returns:
        Lista rekordów FactorRecord z wynikami eksperymentu
    """
    records = []
    
    print("\n" + "="*60)
    print("EKSPERYMENT Z FAKTORYZACJĄ RSA")
    print("="*60)
    
    for bit_length in BIT_LENGTHS:
        print(f"\nDługość klucza: {bit_length} bitów")
        
        for sample_num in range(1, SAMPLES_PER_SIZE + 1):
            # Generuj półpierwszą liczbę
            n, p_true, q_true = generate_semiprime_for_bits(bit_length)
            
            # Faktoryzuj używając sympy
            factors, time_sec, iterations, success = factor_with_sympy(n)
            
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
            print(f"  Próbka {sample_num}/{SAMPLES_PER_SIZE}: {status} "
                  f"czas={time_sec:.6f}s, n={n.bit_length()} bitów")
    
    return records


def save_factor_records_to_csv(records: List[FactorRecord], filename: str = "factorization_results.csv"):
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


def plot_factorization_results(records: List[FactorRecord], filename: str = "factorization_times.png"):
    """
    Rysuje wykres średnich czasów faktoryzacji w zależności od długości klucza.
    
    Dodaje dopasowania krzywych: liniową, potęgową i wykładniczą.
    Ekstrapoluje czasy dla 512 i 1024 bitów.
    
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
            # Logarytmujemy: log(y) = log(a) + b*log(x)
            # Używamy tylko dodatnich wartości
            mask = (x_data > 0) & (y_data > 0)
            if np.sum(mask) >= 3:  # Potrzebujemy co najmniej 3 punktów
                x_log = np.log(x_data[mask])
                y_log = np.log(y_data[mask])
                power_coeffs = np.polyfit(x_log, y_log, 1)
                a_power = np.exp(power_coeffs[1])
                b_power = power_coeffs[0]
                y_power = a_power * (x_fit ** b_power)
                plt.plot(x_fit, y_power, '--', label=f'Dopasowanie potęgowe ({method}): y={a_power:.2e}*x^{b_power:.2f}', 
                        linewidth=1.5, alpha=0.7)
            else:
                a_power, b_power = None, None
            
            # 3. Dopasowanie wykładnicze: y = a * exp(b*x)
            # Logarytmujemy: log(y) = log(a) + b*x
            mask = y_data > 0
            if np.sum(mask) >= 3:
                y_log = np.log(y_data[mask])
                exp_coeffs = np.polyfit(x_data[mask], y_log, 1)
                a_exp = np.exp(exp_coeffs[1])
                b_exp = exp_coeffs[0]
                y_exp = a_exp * np.exp(b_exp * x_fit)
                plt.plot(x_fit, y_exp, '--', label=f'Dopasowanie wykładnicze ({method}): y={a_exp:.2e}*exp({b_exp:.4f}*x)', 
                        linewidth=1.5, alpha=0.7)
            else:
                a_exp, b_exp = None, None
            
            # Ekstrapolacja dla 512 i 1024 bitów
            extrapolation_bits = [512, 1024]
            print(f"\n{'='*60}")
            print(f"EKSTRAPOLACJA DLA METODY: {method}")
            print(f"{'='*60}")
            
            for ext_bits in extrapolation_bits:
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
            
            # Rysuj punkty ekstrapolacji (tylko raz, żeby uniknąć duplikatów w legendzie)
            for ext_bits in extrapolation_bits:
                if linear_func(ext_bits) > 0:
                    if not extrapolation_labeled:
                        plt.plot(ext_bits, linear_func(ext_bits), 's', color='red', 
                                markersize=10, markerfacecolor='none', markeredgewidth=2, 
                                label='Ekstrapolacja (512, 1024 bity)')
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
    
    # Analiza wiarygodności prognoz
    print(f"\n{'='*60}")
    print("ANALIZA WIARYGODNOŚCI PROGNOZ")
    print(f"{'='*60}")
    print("""
UWAGI O EKSTRAPOLACJI:

1. ZAKRES DANYCH: Dane eksperymentalne obejmują klucze 32-128 bitów.
   Ekstrapolacja do 512 i 1024 bitów to znaczne rozszerzenie (4-8x większe wartości).

2. MODELE MATEMATYCZNE:
   - Liniowy: Zakłada stały przyrost czasu na bit (najmniej realistyczny dla faktoryzacji)
   - Potęgowy: Zakłada wzrost typu O(n^k) - bardziej realistyczny dla algorytmów faktoryzacji
   - Wykładniczy: Zakłada wykładniczy wzrost - może być zbyt pesymistyczny

3. RZECZYWISTOŚĆ:
   - Faktoryzacja RSA jest sub-wykładnicza (około O(exp(c * n^(1/3) * log(n)^(2/3))))
   - Dla małych kluczy (32-128 bitów) może wydawać się wykładnicza
   - Dla większych kluczy (512+) algorytmy jak GNFS (General Number Field Sieve) 
     są znacznie szybsze niż proste metody

4. WIARYGODNOŚĆ:
   - Prognozy dla 512 bitów: UMIARKOWANIE WIARYGODNE
     * Rzeczywisty czas faktoryzacji 512-bitowego RSA: kilka miesięcy do lat
     * (zależnie od sprzętu i algorytmów)
   
   - Prognozy dla 1024 bitów: MAŁO WIARYGODNE
     * Rzeczywisty czas: dziesiątki do setek lat (lub więcej)
     * Ekstrapolacja z danych 32-128 bitów jest zbyt daleka
     * Algorytmy dla dużych kluczy używają zupełnie innych metod

5. WNIOSEK:
   Prognozy oparte na danych z małych kluczy (32-128 bitów) NIE SĄ 
   wiarygodne dla dużych kluczy (512+ bitów), ponieważ:
   - Skalowanie złożoności zmienia się dla większych liczb
   - Używane są inne algorytmy (GNFS zamiast prostych metod)
   - Czynniki sprzętowe i optymalizacje mają większy wpływ
   
   Ekstrapolacja pokazuje jedynie TREND, nie rzeczywiste czasy!
    """)


# ============================================================================
# GŁÓWNA FUNKCJA I INTERFEJS
# ============================================================================

def main():
    """Główna funkcja programu."""
    parser = argparse.ArgumentParser(
        description='Implementacja RSA z eksperymentem faktoryzacji',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'message_file',
        type=str,
        help='Ścieżka do pliku z wiadomością do zaszyfrowania'
    )
    parser.add_argument(
        '--alphabet',
        type=str,
        choices=['26', '64', 'ascii'],
        default='ascii',
        help='Alfabet do użycia: 26 (litery), 64 (Base64), ascii (domyślnie)'
    )
    parser.add_argument(
        '--key-length',
        type=int,
        default=768,
        help='Długość klucza RSA w bitach (domyślnie 768)'
    )
    parser.add_argument(
        '--skip-rsa',
        action='store_true',
        help='Pomiń demonstrację RSA, uruchom tylko eksperyment faktoryzacji'
    )
    
    args = parser.parse_args()
    
    # ========================================================================
    # CZĘŚĆ I: DEMONSTRACJA RSA
    # ========================================================================
    
    if not args.skip_rsa:
        print("\n" + "="*60)
        print("CZĘŚĆ I: IMPLEMENTACJA RSA")
        print("="*60)
                
        alphabet = get_alphabet(args.alphabet)
        print(f"\nUżywany alfabet: {args.alphabet} ({len(alphabet)} znaków)")
                
        message_path = Path(args.message_file)
        if not message_path.exists():
            print(f"Błąd: Plik {args.message_file} nie istnieje!")
            return
        
        original_message = read_message(str(message_path), alphabet)
        print(f"Wczytano wiadomość: {len(original_message)} znaków")
        if len(original_message) > 100:
            print(f"  (pierwsze 100 znaków: {original_message[:100]}...)")
        else:
            print(f"  (treść: {original_message})")
                
        blocks = split_into_blocks(original_message, block_size=10, alphabet=alphabet)
        print(f"Podzielono na {len(blocks)} bloków po 10 znaków")
                
        print(f"\nGenerowanie klucza RSA ({args.key_length} bitów)...")
        key = generate_rsa_keypair(bit_length=args.key_length)
        print(f"✓ Wygenerowano klucz:")
        print(f"  n = {key.n} ({key.n.bit_length()} bitów)")
        print(f"  e = {key.e}")
        print(f"  p = {key.p}")
        print(f"  q = {key.q}")
        
        print("\nSzyfrowanie wiadomości...")
        try:
            cipher_blocks = encrypt_message_blocks(blocks, key, alphabet)
            print(f"✓ Zaszyfrowano {len(cipher_blocks)} bloków")
        except ValueError as e:
            print(f"✗ Błąd szyfrowania: {e}")
            print("  Spróbuj zwiększyć długość klucza lub zmniejszyć rozmiar bloku.")
            return
        
        print("Deszyfrowanie wiadomości...")
        decrypted_blocks = decrypt_message_blocks(cipher_blocks, key, alphabet, block_size=10)
        print(f"✓ Odszyfrowano {len(decrypted_blocks)} bloków")
        decrypted_message = ''.join(decrypted_blocks)
        padding_char = alphabet[0]
        decrypted_message = decrypted_message.rstrip(padding_char)
        
        print("\n" + "-"*60)
        print("SPRAWDZENIE ZGODNOŚCI:")
        print("-"*60)
        
        if original_message == decrypted_message:
            print("✓ SUKCES: Wiadomość po odszyfrowaniu jest identyczna z oryginalną!")
        else:
            print("✗ BŁĄD: Wiadomość po odszyfrowaniu różni się od oryginalnej.")
            print(f"  Długość oryginału: {len(original_message)}")
            print(f"  Długość odszyfrowanej: {len(decrypted_message)}")
            if len(original_message) <= 200 and len(decrypted_message) <= 200:
                print(f"  Oryginał: {repr(original_message)}")
                print(f"  Odszyfrowana: {repr(decrypted_message)}")
        
        print("\nPorównanie blok po bloku:")
        all_match = True
        for i, (orig_block, decr_block) in enumerate(zip(blocks, decrypted_blocks)):
            match = orig_block == decr_block
            if not match:
                all_match = False
            status = "✓" if match else "✗"
            if i < 5 or not match:
                print(f"  Blok {i}: {status} {repr(orig_block)} vs {repr(decr_block)}")
        
        if all_match:
            print("  Wszystkie bloki się zgadzają!")
    
    # ========================================================================
    # CZĘŚĆ II: EKSPERYMENT Z FAKTORYZACJĄ
    # ========================================================================
    
    print("\n" + "="*60)
    print("CZĘŚĆ II: EKSPERYMENT Z FAKTORYZACJĄ")
    print("="*60)
    
    records = run_factorization_experiment()
    
    csv_filename = "factorization_results.csv"
    save_factor_records_to_csv(records, csv_filename)
    
    plot_filename = "factorization_times.png"
    plot_factorization_results(records, plot_filename)
    
    print("\n" + "="*60)
    print("PODSUMOWANIE")
    print("="*60)
    total_samples = len(records)
    successful = sum(1 for r in records if r.success)
    print(f"Łączna liczba próbek: {total_samples}")
    print(f"Udanych faktoryzacji: {successful} ({100*successful/total_samples:.1f}%)")
    print(f"Wyniki zapisane w: {csv_filename}")
    print(f"Wykres zapisany w: {plot_filename}")
    print("\n✓ Program zakończony pomyślnie!")


if __name__ == "__main__":
    main()

