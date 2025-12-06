#!/usr/bin/env python3
"""
Moduł implementacji RSA - generowanie kluczy, szyfrowanie i deszyfrowanie.
"""

import math
from dataclasses import dataclass
from typing import List
from pathlib import Path

import sympy
from sympy import mod_inverse

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
# KLASA RSA
# ============================================================================

@dataclass
class RSAKeyPair:
    """Para kluczy RSA: publiczny (n, e) i prywatny (n, d)."""
    n: int  # Moduł (iloczyn p * q)
    e: int  # Wykładnik publiczny
    d: int  # Wykładnik prywatny
    p: int  # Pierwsza liczba pierwsza
    q: int  # Druga liczba pierwsza


class RSACrypto:
    """Klasa do obsługi szyfrowania i deszyfrowania RSA."""
    
    def __init__(self, alphabet: str = ALPHABET_ASCII):
        """
        Inicjalizuje obiekt RSA z wybranym alfabetem.
        
        Args:
            alphabet: Alfabet do użycia (domyślnie ASCII)
        """
        self.alphabet = alphabet
    
    @staticmethod
    def generate_keypair(bit_length: int = 768) -> RSAKeyPair:
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
    
    def read_message(self, path: str) -> str:
        """
        Czyta wiadomość z pliku i normalizuje ją do wybranego alfabetu.
        
        Args:
            path: Ścieżka do pliku z wiadomością
        
        Returns:
            Znormalizowana wiadomość
        """
        with open(path, 'rb') as f:
            content_bytes = f.read()
        
        if self.alphabet == ALPHABET_26:
            try:
                content = content_bytes.decode('utf-8', errors='ignore')
            except:
                content = content_bytes.decode('latin-1', errors='ignore')
            normalized = ''.join(c.upper() for c in content if c.upper() in ALPHABET_26)
        elif self.alphabet == ALPHABET_64:
            try:
                content = content_bytes.decode('utf-8', errors='ignore')
            except:
                content = content_bytes.decode('latin-1', errors='ignore')
            normalized = ''.join(c for c in content if c in ALPHABET_64)
        else:  # ASCII
            normalized = ''.join(chr(b) for b in content_bytes)
        
        return normalized
    
    def split_into_blocks(self, message: str, block_size: int = 10) -> List[str]:
        """
        Dzieli wiadomość na bloki o zadanej długości.
        
        Args:
            message: Wiadomość do podziału
            block_size: Długość bloku (domyślnie 10)
        
        Returns:
            Lista bloków znaków
        """
        blocks = []
        padding_char = self.alphabet[0] if self.alphabet else ' '
        
        for i in range(0, len(message), block_size):
            block = message[i:i + block_size]
            if len(block) < block_size:
                block = block + padding_char * (block_size - len(block))
            blocks.append(block)
        
        return blocks
    
    def block_to_int(self, block: str) -> int:
        """
        Konwertuje blok znaków na liczbę całkowitą.
        
        Args:
            block: Blok znaków do konwersji
        
        Returns:
            Liczba całkowita reprezentująca blok
        """
        base = len(self.alphabet)
        result = 0
        
        for i, char in enumerate(block):
            if char not in self.alphabet:
                raise ValueError(f"Znak '{char}' nie znajduje się w alfabecie")
            index = self.alphabet.index(char)
            power = len(block) - 1 - i
            result += index * (base ** power)
        
        return result
    
    def int_to_block(self, value: int, block_size: int) -> str:
        """
        Konwertuje liczbę całkowitą z powrotem na blok znaków.
        
        Args:
            value: Liczba do konwersji
            block_size: Długość bloku wynikowego
        
        Returns:
            Blok znaków reprezentujący liczbę
        """
        base = len(self.alphabet)
        result = []
        
        temp = value
        for _ in range(block_size):
            result.append(self.alphabet[temp % base])
            temp //= base
        
        result.reverse()
        return ''.join(result)
    
    def encrypt_block(self, m_int: int, n: int, e: int) -> int:
        """
        Szyfruje pojedynczy blok (liczbę) używając klucza publicznego.
        
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
    
    def decrypt_block(self, c_int: int, n: int, d: int) -> int:
        """
        Deszyfruje pojedynczy blok (liczbę) używając klucza prywatnego.
        
        Args:
            c_int: Liczba reprezentująca zaszyfrowany blok
            n: Moduł RSA
            d: Wykładnik prywatny
        
        Returns:
            Odszyfrowana liczba
        """
        return pow(c_int, d, n)
    
    def encrypt_message_blocks(self, blocks: List[str], key: RSAKeyPair) -> List[int]:
        """
        Szyfruje listę bloków znaków używając klucza RSA.
        
        Args:
            blocks: Lista bloków znaków do zaszyfrowania
            key: Para kluczy RSA
        
        Returns:
            Lista zaszyfrowanych liczb
        """
        cipher_blocks = []
        
        for block in blocks:
            m_int = self.block_to_int(block)
            
            if m_int >= key.n:
                raise ValueError(
                    f"Blok '{block}' konwertuje się na liczbę {m_int}, "
                    f"która jest >= n={key.n}. Zwiększ długość klucza lub zmniejsz rozmiar bloku."
                )
            
            c_int = self.encrypt_block(m_int, key.n, key.e)
            cipher_blocks.append(c_int)
        
        return cipher_blocks
    
    def decrypt_message_blocks(
        self, 
        cipher_blocks: List[int], 
        key: RSAKeyPair, 
        block_size: int = 10
    ) -> List[str]:
        """
        Deszyfruje listę zaszyfrowanych liczb z powrotem na bloki znaków.
        
        Args:
            cipher_blocks: Lista zaszyfrowanych liczb
            key: Para kluczy RSA
            block_size: Długość bloku znaków
        
        Returns:
            Lista odszyfrowanych bloków znaków
        """
        decrypted_blocks = []
        
        for c_int in cipher_blocks:
            m_int = self.decrypt_block(c_int, key.n, key.d)
            block = self.int_to_block(m_int, block_size)
            decrypted_blocks.append(block)
        
        return decrypted_blocks


