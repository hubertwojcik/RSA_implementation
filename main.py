import secrets
import math
import time
from sympy import isprime, factorint, pollard_rho, pollard_pm1
from math import gcd

# Próba importu dodatkowych bibliotek do faktoryzacji
try:
    from primefac import factorint as primefac_factorint
    PRIMEFAC_AVAILABLE = True
except ImportError:
    PRIMEFAC_AVAILABLE = False

try:
    import gmpy2
    GMPY2_AVAILABLE = True
except ImportError:
    GMPY2_AVAILABLE = False

try:
    import pyecm
    PYECM_AVAILABLE = True
except ImportError:
    PYECM_AVAILABLE = False


def read_message(file_path, alphabet_type='auto'):
    """
    Wczytuje wiadomość z pliku.
    
    Args:
        file_path (str): Ścieżka do pliku z wiadomością
        alphabet_type (str): Typ alfabetu - '26' (26-znakowy), '64' (64-znakowy), 
                           'ascii' (pełny ASCII), lub 'auto' (automatyczne wykrywanie)
    
    Returns:
        str: Wczytana wiadomość
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            message = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Plik '{file_path}' nie został znaleziony.")
    except Exception as e:
        raise Exception(f"Błąd podczas wczytywania pliku: {e}")
    
    
    if alphabet_type == 'auto':
        alphabet_type = detect_alphabet_type(message)
        print(f"Wykryto typ alfabetu: {alphabet_type}")
    
    return message


def detect_alphabet_type(wiadomosc):
    """
    Automatycznie wykrywa typ alfabetu w wiadomości.
    
    Args:
        wiadomosc (str): Wiadomość do analizy
    
    Returns:
        str: '26', '64', lub 'ascii'
    """
    if not wiadomosc:
        return 'ascii'
    
    # Alfabet 26-znakowy (tylko małe litery a-z)
    alphabet_26 = set('abcdefghijklmnopqrstuvwxyz')
    signs_in_message = set(wiadomosc.lower())
    
    # Sprawdź czy wszystkie znaki są w alfabecie 26-znakowym
    if signs_in_message.issubset(alphabet_26 | {' ', '\n', '\t', '\r'}):
        return '26'
    
    # Alfabet 64-znakowy (Base64: A-Z, a-z, 0-9, +, /)
    alfabet_64 = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    if signs_in_message.issubset(alfabet_64 | {' ', '\n', '\t', '\r'}):
        return '64'
    
    # W przeciwnym razie pełny ASCII
    return 'ascii'


def divide_into_blocks(message, num_of_blocks=10):
    """
    Dzieli wiadomość na określoną liczbę bloków.
    
    Args:
        message (str): Wiadomość do podziału
        num_of_blocks (int): Liczba bloków na które ma być podzielona wiadomość (domyślnie 10)
    
    Returns:
        list: Lista bloków tekstu
    """
    if not message:
        return [''] * num_of_blocks
    
    length = len(message)
    block_length = length // num_of_blocks
    rest = length % num_of_blocks
    
    blocks = []
    index = 0
    
    for i in range(num_of_blocks):
        # Pierwsze 'reszta' bloków będzie o 1 znak dłuższe
        current_length = block_length + (1 if i < rest else 0)
        block = message[index:index + current_length]
        blocks.append(block)
        index += current_length
    
    return blocks


def block_to_number(block, alphabet_type='ascii'):
    """
    Zamienia blok tekstu na liczbę (odwracalna operacja).
    
    Args:
        block (str): Blok tekstu do zamiany
        alphabet_type (str): Typ alfabetu - '26', '64', lub 'ascii'
    
    Returns:
        int: Liczba reprezentująca blok
    """
    if not block:
        return 0
    
    if alphabet_type == '26':
        # Alfabet 26-znakowy: a=0, b=1, ..., z=25
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        number = 0
        base = 26
        for char in block.lower():
            if char in alphabet:
                number = number * base + alphabet.index(char)                        
        return number
    
    elif alphabet_type == '64':
        # Alfabet 64-znakowy (Base64): A-Z, a-z, 0-9, +, /
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        number = 0
        base = 64
        for char in block:
            if char in alphabet:
                number = number * base + alphabet.index(char)
        return number
    
    else:  # 'ascii'
        # Pełny ASCII: każdy znak to jego kod ASCII
        number = 0
        base = 256
        for char in block:
            number = number * base + ord(char)
        return number


def number_to_block(number, block_length, alphabet_type='ascii'):
    """
    Zamienia liczbę z powrotem na blok tekstu (odwrotna operacja do block_to_number).
    
    Args:
        number (int): Liczba do zamiany na blok
        block_length (int): Długość bloku (liczba znaków)
        alphabet_type (str): Typ alfabetu - '26', '64', lub 'ascii'
    
    Returns:
        str: Blok tekstu
    """
    block = []
    
    if alphabet_type == '26':
        # Alfabet 26-znakowy: a=0, b=1, ..., z=25
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        base = 26
        temp_number = number
        for _ in range(block_length):
            block.append(alphabet[temp_number % base])
            temp_number //= base
        block.reverse()
        return ''.join(block)
    
    elif alphabet_type == '64':
        # Alfabet 64-znakowy (Base64)
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        base = 64
        temp_number = number
        for _ in range(block_length):
            block.append(alphabet[temp_number % base])
            temp_number //= base
        block.reverse()
        return ''.join(block)
    
    else:  # 'ascii'
        # Pełny ASCII
        base = 256
        temp_number = number
        for _ in range(block_length):
            block.append(chr(temp_number % base))
            temp_number //= base
        block.reverse()
        return ''.join(block)


class RSA:
    """
    Klasa implementująca algorytm szyfrowania RSA.
    """
    
    def __init__(self, key_length=768):
        """
        Inicjalizuje obiekt RSA.
        
        Args:
            key_length (int): Długość klucza w bitach (domyślnie 768)
        """
        self.key_length = key_length
        self.public_key = None
        self.private_key = None
        
    def is_prime(self, n):
        """
        Sprawdza czy liczba jest pierwsza używając biblioteki sympy.
        
        Args:
            n (int): Liczba do sprawdzenia
        
        Returns:
            bool: True jeśli liczba jest pierwsza
        """
        return isprime(n)
    
    def generate_large_prime(self, bits):
        """
        Generuje dużą liczbę pierwszą o określonej liczbie bitów.
        
        Args:
            bits (int): Liczba bitów liczby pierwszej
        
        Returns:
            int: Liczba pierwsza
        """
        while True:
            # Generuj losową liczbę o określonej liczbie bitów
            candidate = secrets.randbits(bits)
            candidate |= (1 << (bits - 1))  # Ustaw najwyższy bit
            candidate |= 1  # Ustaw najniższy bit (liczba nieparzysta)
            
            if self.is_prime(candidate):
                return candidate
    
    def extended_gcd(self, a, b):
        """
        Rozszerzony algorytm Euklidesa.
        Zwraca (gcd, x, y) takie, że gcd = a*x + b*y
        
        Args:
            a (int): Pierwsza liczba
            b (int): Druga liczba
        
        Returns:
            tuple: (gcd, x, y)
        """
        if a == 0:
            return b, 0, 1
        
        gcd_val, x1, y1 = self.extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        
        return gcd_val, x, y
    
    def mod_inverse(self, a, m):
        """
        Oblicza odwrotność modularną a^(-1) mod m używając rozszerzonego GCD.
        
        Args:
            a (int): Liczba
            m (int): Modulo
        
        Returns:
            int: Odwrotność modularna
        """
        if gcd(a, m) != 1:
            raise ValueError(f"Odwrotność modularna nie istnieje dla {a} mod {m}")
        
        gcd_val, x, _ = self.extended_gcd(a % m, m)
        return (x % m + m) % m
    
    def generate_keys(self, e=65537, allow_small_keys=False):
        """
        Generuje parę kluczy RSA (publiczny i prywatny).
        
        Args:
            e (int): Publiczny wykładnik (domyślnie 65537)
            allow_small_keys (bool): Pozwala na klucze mniejsze niż 768 bitów (tylko do testów!)
        
        Returns:
            tuple: ((n, e), (n, d)) - klucz publiczny i prywatny
        """
        if self.key_length < 768 and not allow_small_keys:
            raise ValueError("Długość klucza musi wynosić co najmniej 768 bitów (użyj allow_small_keys=True dla testów)")
        
        prime_bits = self.key_length // 2
        
        print(f"Generowanie kluczy RSA o długości {self.key_length} bitów...")
        
        # Generuj dwie liczby pierwsze
        p = self.generate_large_prime(prime_bits)
        print(f"Wygenerowano p ({p.bit_length()} bitów)")
        
        q = self.generate_large_prime(prime_bits)
        print(f"Wygenerowano q ({q.bit_length()} bitów)")
        
        # Oblicz n = p * q
        n = p * q
        print(f"n = p * q ({n.bit_length()} bitów)")
        
        # Oblicz φ(n) = (p-1)(q-1)
        phi_n = (p - 1) * (q - 1)
        
        # Dla małych kluczy, użyj mniejszego e jeśli 65537 jest za duże
        if e >= phi_n:
            # Znajdź mniejsze e (zwykle 3, 17, 257)
            for small_e in [3, 17, 257, 65537]:
                if small_e < phi_n and gcd(small_e, phi_n) == 1:
                    e = small_e
                    print(f"Dostosowano e do {e} (oryginalny był za duży)")
                    break
            else:
                # Jeśli żadne standardowe e nie działa, znajdź pierwsze działające
                e = 3
                while e < phi_n and gcd(e, phi_n) != 1:
                    e += 2
                print(f"Użyto niestandardowego e = {e}")
        
        # Sprawdź czy e jest względnie pierwsze z φ(n)
        if gcd(e, phi_n) != 1:
            raise ValueError(f"e={e} nie jest względnie pierwsze z φ(n)")
        
        # Oblicz d = e^(-1) mod φ(n)
        d = self.mod_inverse(e, phi_n)
        
        self.public_key = (n, e)
        self.private_key = (n, d)
        
        print(f"Klucze wygenerowane pomyślnie!")
        return self.public_key, self.private_key
    
    def encrypt_block(self, message_block, public_key=None):
        """
        Szyfruje pojedynczy blok używając klucza publicznego.
        
        Args:
            message_block (int): Blok wiadomości jako liczba
            public_key (tuple): Klucz publiczny (n, e). Jeśli None, użyje self.public_key
        
        Returns:
            int: Zaszyfrowany blok
        """
        if public_key is None:
            public_key = self.public_key
        
        if public_key is None:
            raise ValueError("Brak klucza publicznego. Wygeneruj klucze najpierw.")
        
        n, e = public_key
        
        if message_block >= n:
            raise ValueError(f"Blok wiadomości ({message_block}) jest większy niż n ({n})")
        
        # RSA szyfrowanie: c = m^e mod n
        return pow(message_block, e, n)
    
    def decrypt_block(self, encrypted_block, private_key=None):
        """
        Deszyfruje pojedynczy blok używając klucza prywatnego.
        
        Args:
            encrypted_block (int): Zaszyfrowany blok
            private_key (tuple): Klucz prywatny (n, d). Jeśli None, użyje self.private_key
        
        Returns:
            int: Odszyfrowany blok
        """
        if private_key is None:
            private_key = self.private_key
        
        if private_key is None:
            raise ValueError("Brak klucza prywatnego. Wygeneruj klucze najpierw.")
        
        n, d = private_key
        
        # RSA deszyfrowanie: m = c^d mod n
        return pow(encrypted_block, d, n)
    
    def encrypt_message(self, message, alphabet_type='auto', num_blocks=10):
        """
        Szyfruje całą wiadomość.
        
        Args:
            message (str): Wiadomość do zaszyfrowania
            alphabet_type (str): Typ alfabetu
            num_blocks (int): Liczba bloków
        
        Returns:
            list: Lista zaszyfrowanych bloków
        """
        if self.public_key is None:
            raise ValueError("Brak klucza publicznego. Wygeneruj klucze najpierw.")
        
        # Wykryj typ alfabetu jeśli auto
        if alphabet_type == 'auto':
            alphabet_type = detect_alphabet_type(message)
            print(f"Wykryto typ alfabetu: {alphabet_type}")
        
        # Podziel na bloki
        blocks = divide_into_blocks(message, num_blocks)
        print(f"Podzielono wiadomość na {len(blocks)} bloków")
        
        encrypted_blocks = []
        
        for i, block in enumerate(blocks):
            if block:  # Pomiń puste bloki
                # Zamień blok na liczbę
                number = block_to_number(block, alphabet_type)
                
                # Zaszyfruj blok
                encrypted_number = self.encrypt_block(number)
                encrypted_blocks.append((encrypted_number, len(block), alphabet_type))
                
                print(f"Blok {i+1}: '{block}' -> {number} -> {encrypted_number}")
            else:
                encrypted_blocks.append((0, 0, alphabet_type))
        
        return encrypted_blocks
    
    def decrypt_message(self, encrypted_blocks):
        """
        Deszyfruje całą wiadomość.
        
        Args:
            encrypted_blocks (list): Lista zaszyfrowanych bloków z metadanymi
        
        Returns:
            str: Odszyfrowana wiadomość
        """
        if self.private_key is None:
            raise ValueError("Brak klucza prywatnego. Wygeneruj klucze najpierw.")
        
        decrypted_blocks = []
        
        for i, (encrypted_number, block_length, alphabet_type) in enumerate(encrypted_blocks):
            if encrypted_number != 0:  # Pomiń puste bloki
                # Odszyfruj blok
                decrypted_number = self.decrypt_block(encrypted_number)
                
                # Zamień liczbę z powrotem na blok
                decrypted_block = number_to_block(decrypted_number, block_length, alphabet_type)
                decrypted_blocks.append(decrypted_block)
                
                print(f"Blok {i+1}: {encrypted_number} -> {decrypted_number} -> '{decrypted_block}'")
            else:
                decrypted_blocks.append('')
        
        return ''.join(decrypted_blocks)


class RSAFactorization:
    """
    Klasa zawierająca metody faktoryzacji liczb dla testowania bezpieczeństwa RSA.
    """
    
    @staticmethod
    def sympy_pollard_rho(n):
        """
        SymPy Pollard's Rho - konkretna implementacja.
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        try:
            factor = pollard_rho(n)
            if factor and 1 < factor < n:
                return (factor, n // factor)
        except Exception:
            pass
        return None
    
    @staticmethod
    def sympy_pollard_pm1(n):
        """
        SymPy Pollard's p-1 - konkretna implementacja.
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        try:
            factor = pollard_pm1(n)
            if factor and 1 < factor < n:
                return (factor, n // factor)
        except Exception:
            pass
        return None
    
    @staticmethod
    def simple_trial_division(n, limit=100000):
        """
        Prosta implementacja trial division z bezpiecznym limitem.
        
        Args:
            n (int): Liczba do sfaktoryzowania
            limit (int): Maksymalny dzielnik do sprawdzenia
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        if n <= 1:
            return None
        if n % 2 == 0:
            return (2, n // 2)
        
        # Sprawdź nieparzyste od 3 do limitu
        for i in range(3, min(int(n**0.5) + 1, limit), 2):
            if n % i == 0:
                return (i, n // i)
        
        return None
    
    @staticmethod
    def pyecm_factorization(n):
        """
        PyECM - Elliptic Curve Method faktoryzacja.
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        if not PYECM_AVAILABLE:
            return None
        
        try:
            # pyecm.factor zwraca listę czynników
            factors = pyecm.factor(n)
            if len(factors) >= 2:
                factors.sort(reverse=True)
                return (factors[0], factors[1])
            elif len(factors) == 1 and factors[0] != n:
                return (factors[0], n // factors[0])
        except Exception:
            pass
        return None
    
    @staticmethod
    def sympy_general_factorization(n):
        """
        SymPy ogólna faktoryzacja - automatyczny wybór najlepszego algorytmu.
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        try:
            factors = factorint(n)
            factor_list = []
            for prime, power in factors.items():
                factor_list.extend([prime] * power)
            
            if len(factor_list) >= 2:
                factor_list.sort(reverse=True)
                return (factor_list[0], factor_list[1])
            elif len(factor_list) == 1:
                return (factor_list[0], 1)
            
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def primefac_factorization(n):
        """
        Faktoryzacja używając biblioteki primefac - specjalizowana biblioteka do faktoryzacji.
        Implementuje: Pollard's rho, Pollard's p-1, Williams' p+1, ECM, MPQS, SIQS
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        if not PRIMEFAC_AVAILABLE:
            return None
        
        try:
            factors = list(primefac_factorint(n))
            if len(factors) >= 2:
                factors.sort(reverse=True)
                return (factors[0], factors[1])
            elif len(factors) == 1:
                return (factors[0], 1)
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def gmpy2_factorization(n):
        """
        Faktoryzacja używając gmpy2 - interfejs do biblioteki GMP (GNU Multiple Precision).
        Bardzo szybkie operacje na dużych liczbach napisane w C.
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        if not GMPY2_AVAILABLE:
            return None
        
        try:
            # gmpy2 nie ma wbudowanej faktoryzacji, ale ma szybkie operacje
            # Użyjemy prostego trial division z gmpy2
            n_gmpy = gmpy2.mpz(n)
            
            if gmpy2.is_even(n_gmpy):
                return (2, int(n_gmpy // 2))
            
            # Szybkie sprawdzenie małych dzielników
            limit = min(int(gmpy2.isqrt(n_gmpy)) + 1, 1000000)
            for i in range(3, limit, 2):
                if n_gmpy % i == 0:
                    return (int(i), int(n_gmpy // i))
            
        except Exception:
            pass
        
        return None
    
    
    @staticmethod
    def sympy_factorization(n):
        """
        Faktoryzacja używając biblioteki SymPy (zoptymalizowane algorytmy).
        
        Args:
            n (int): Liczba do sfaktoryzowania
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        try:
            factors = factorint(n)
            factor_list = []
            for prime, power in factors.items():
                factor_list.extend([prime] * power)
            
            if len(factor_list) >= 2:
                # Znajdź dwa największe czynniki
                factor_list.sort(reverse=True)
                return (factor_list[0], factor_list[1])
            elif len(factor_list) == 1:
                return (factor_list[0], 1)
            
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def quadratic_sieve_simple(n, max_iterations=10000):
        """
        Uproszczona implementacja Quadratic Sieve (metoda wykładnicza).
        UWAGA: To jest bardzo uproszczona wersja dla celów edukacyjnych!
        
        Args:
            n (int): Liczba do sfaktoryzowania
            max_iterations (int): Maksymalna liczba iteracji
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        if n <= 1:
            return None
        if n % 2 == 0:
            return (2, n // 2)
        
        # Wybierz bazę małych liczb pierwszych
        primes = []
        for i in range(2, min(1000, int(n**0.25) + 100)):
            if isprime(i):
                primes.append(i)
        
        if len(primes) < 10:
            return None
        
        # Szukaj gładkich liczb (B-smooth numbers)
        smooth_numbers = []
        sqrt_n = int(math.sqrt(n))
        
        for x in range(sqrt_n + 1, sqrt_n + max_iterations):
            y_squared = x * x - n
            if y_squared <= 0:
                continue
            
            # Sprawdź czy y² jest gładkie względem naszej bazy
            temp = y_squared
            factors = []
            
            for p in primes:
                count = 0
                while temp % p == 0:
                    temp //= p
                    count += 1
                if count > 0:
                    factors.append((p, count))
                
                if temp == 1:
                    # Znaleźliśmy gładką liczbę!
                    smooth_numbers.append((x, y_squared, factors))
                    break
                
                if len(smooth_numbers) >= len(primes) + 5:
                    break
            
            if len(smooth_numbers) >= len(primes) + 5:
                break
        
        # Próba znalezienia zależności liniowej (bardzo uproszczone)
        if len(smooth_numbers) >= 2:
            # Weź pierwsze dwie gładkie liczby i spróbuj kombinacji
            x1, y1_sq, _ = smooth_numbers[0]
            x2, y2_sq, _ = smooth_numbers[1]
            
            # Sprawdź czy (x1*x2)² ≡ (y1*y2)² (mod n)
            left = (x1 * x2) % n
            right_sq = (y1_sq * y2_sq) % n
            right = int(math.sqrt(right_sq)) % n
            
            if left != right and (left + right) % n != 0:
                gcd_result = gcd(abs(left - right), n)
                if 1 < gcd_result < n:
                    return (gcd_result, n // gcd_result)
        
        return None
    
    @staticmethod
    def dixon_factorization(n, max_iterations=10000):
        """
        Algorytm Dixona (prekursor Quadratic Sieve) - metoda wykładnicza.
        
        Args:
            n (int): Liczba do sfaktoryzowania
            max_iterations (int): Maksymalna liczba iteracji
        
        Returns:
            tuple: (p, q) jeśli znaleziono czynniki, None jeśli nie
        """
        if n <= 1:
            return None
        if n % 2 == 0:
            return (2, n // 2)
        
        # Baza małych liczb pierwszych
        B = int(math.log(n) * math.log(math.log(n)))
        primes = []
        for i in range(2, min(B, 1000)):
            if isprime(i):
                primes.append(i)
        
        if len(primes) < 5:
            return None
        
        # Zbieraj pary (x, x² mod n) gdzie x² mod n jest B-smooth
        relations = []
        
        for _ in range(max_iterations):
            x = secrets.randbelow(n - 2) + 2
            y = (x * x) % n
            
            # Sprawdź czy y jest B-smooth
            temp = y
            exponents = [0] * len(primes)
            
            for i, p in enumerate(primes):
                while temp % p == 0:
                    temp //= p
                    exponents[i] += 1
            
            if temp == 1:  # y jest B-smooth
                relations.append((x, exponents))
                
                # Jeśli mamy wystarczająco relacji, szukaj zależności
                if len(relations) >= len(primes) + 1:
                    # Uproszczone: weź pierwsze dwie relacje
                    if len(relations) >= 2:
                        x1, exp1 = relations[0]
                        x2, exp2 = relations[1]
                        
                        # Sprawdź czy suma wykładników jest parzysta
                        combined_exp = [(exp1[i] + exp2[i]) % 2 for i in range(len(primes))]
                        if all(e == 0 for e in combined_exp):
                            # Mamy kandydata!
                            left = (x1 * x2) % n
                            
                            # Oblicz prawą stronę
                            right = 1
                            for i, p in enumerate(primes):
                                right = (right * pow(p, (exp1[i] + exp2[i]) // 2, n)) % n
                            
                            if left != right:
                                gcd_result = gcd(abs(left - right), n)
                                if 1 < gcd_result < n:
                                    return (gcd_result, n // gcd_result)
        
        return None
    
    @staticmethod
    def trial_division_optimized(n, max_limit=1000000):
        """
        Zoptymalizowane dzielenie próbne (własna implementacja z licznikiem iteracji).
        
        Args:
            n (int): Liczba do sfaktoryzowania
            max_limit (int): Maksymalny dzielnik do sprawdzenia
        
        Returns:
            tuple: (factors, iterations) jeśli znaleziono, (None, iterations) jeśli nie
        """
        if n <= 1:
            return None, 0
        
        iterations = 0
        
        # Sprawdź 2
        if n % 2 == 0:
            return (2, n // 2), 1
        
        # Sprawdź nieparzyste od 3 do sqrt(n) lub max_limit
        limit = min(int(math.sqrt(n)) + 1, max_limit)
        for i in range(3, limit, 2):
            iterations += 1
            if n % i == 0:
                return (i, n // i), iterations
        
        return None, iterations
    
    @staticmethod
    def pollard_rho_with_counter(n, max_iterations=1000000):
        """
        Pollard's rho z licznikiem iteracji.
        
        Args:
            n (int): Liczba do sfaktoryzowania
            max_iterations (int): Maksymalna liczba iteracji
        
        Returns:
            tuple: (factors, iterations) jeśli znaleziono, (None, iterations) jeśli nie
        """
        if n <= 1:
            return None, 0
        if n % 2 == 0:
            return (2, n // 2), 1
        
        def f(x):
            return (x * x + 1) % n
        
        x = 2
        y = 2
        d = 1
        iterations = 0
        
        while d == 1 and iterations < max_iterations:
            x = f(x)
            y = f(f(y))
            d = gcd(abs(x - y), n)
            iterations += 1
        
        if d != n and d != 1:
            return (d, n // d), iterations
        
        return None, iterations
    
    @staticmethod
    def fermat_with_counter(n, max_iterations=1000000):
        """
        Metoda Fermata z licznikiem iteracji.
        
        Args:
            n (int): Liczba do sfaktoryzowania
            max_iterations (int): Maksymalna liczba iteracji
        
        Returns:
            tuple: (factors, iterations) jeśli znaleziono, (None, iterations) jeśli nie
        """
        if n <= 1:
            return None, 0
        if n % 2 == 0:
            return (2, n // 2), 1
        
        a = int(math.ceil(math.sqrt(n)))
        b_squared = a * a - n
        iterations = 0
        
        while iterations < max_iterations:
            b = int(math.sqrt(b_squared))
            if b * b == b_squared:
                p = a - b
                q = a + b
                if p > 1 and q > 1 and p * q == n:
                    return (p, q), iterations + 1
            
            a += 1
            b_squared = a * a - n
            iterations += 1
        
        return None, iterations
    
    @staticmethod
    def factorize_with_timing(n, method='sympy'):
        """
        Faktoryzuje liczbę z pomiarem czasu i szczegółowymi informacjami.
        
        Args:
            n (int): Liczba do sfaktoryzowania
            method (str): Metoda faktoryzacji
        
        Returns:
            tuple: (factors, time_taken, success, iterations)
        """
        start_time = time.time()
        iterations = 0
        
        if method == 'sympy_general':
            result = RSAFactorization.sympy_general_factorization(n)
            iterations = "N/A (auto)"
        elif method == 'sympy_pollard_rho':
            result = RSAFactorization.sympy_pollard_rho(n)
            iterations = "N/A (SymPy)"
        elif method == 'sympy_pollard_pm1':
            result = RSAFactorization.sympy_pollard_pm1(n)
            iterations = "N/A (SymPy)"
        elif method == 'simple_trial':
            result = RSAFactorization.simple_trial_division(n)
            iterations = "N/A (limit 100k)"
        elif method == 'pyecm':
            result = RSAFactorization.pyecm_factorization(n)
            iterations = "N/A (ECM)"
        elif method == 'primefac':
            result = RSAFactorization.primefac_factorization(n)
            iterations = "N/A (primefac)"
        elif method == 'gmpy2':
            result = RSAFactorization.gmpy2_factorization(n)
            iterations = "N/A (GMP)"
        elif method == 'pollard_rho_custom':
            result, iterations = RSAFactorization.pollard_rho_with_counter(n)
        elif method == 'fermat_custom':
            result, iterations = RSAFactorization.fermat_with_counter(n)
        else:
            raise ValueError(f"Nieznana metoda: {method}")
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        if result:
            return (result, time_taken, True, iterations)
        else:
            return (None, time_taken, False, iterations)


class RSATimingTest:
    """
    Klasa do przeprowadzania testów czasowych RSA.
    """
    
    @staticmethod
    def test_key_generation_and_factorization(key_sizes, factorization_methods=['trial_division']):
        """
        Testuje generowanie kluczy i ich faktoryzację dla różnych rozmiarów.
        
        Args:
            key_sizes (list): Lista rozmiarów kluczy w bitach
            factorization_methods (list): Lista metod faktoryzacji do przetestowania
        
        Returns:
            list: Lista wyników testów
        """
        results = []
        
        print("=" * 100)
        print("TEST CZASOWY RSA - GENEROWANIE KLUCZY I FAKTORYZACJA")
        print("=" * 100)
        print(f"{'Rozmiar':<8} {'Bity n':<8} {'Metoda':<15} {'Czas [s]':<12} {'Iteracje':<15} {'Sukces':<8} {'p, q znalezione'}")
        print("-" * 100)
        
        for key_size in key_sizes:
            print(f"\n--- Testowanie klucza {key_size}-bitowego ---")
            
            # Test generowania klucza
            rsa = RSA(key_length=key_size)
            
            gen_start = time.time()
            try:
                public_key, private_key = rsa.generate_keys(allow_small_keys=True)
                gen_time = time.time() - gen_start
                n, e = public_key
                
                n_bits = n.bit_length()
                
                # Test faktoryzacji dla każdej metody
                for method in factorization_methods:
                    factors, fact_time, success, iterations = RSAFactorization.factorize_with_timing(n, method)
                    
                    if success:
                        p, q = factors
                        factors_str = f"p={p}, q={q}"
                        if len(factors_str) > 30:
                            factors_str = f"p={hex(p)[:10]}..., q={hex(q)[:10]}..."
                    else:
                        factors_str = "Nie znaleziono"
                    
                    result = {
                        'key_size': key_size,
                        'generation_time': gen_time,
                        'n': n,
                        'n_bits': n_bits,
                        'factorization_method': method,
                        'factorization_time': fact_time,
                        'factorization_success': success,
                        'factors': factors,
                        'iterations': iterations
                    }
                    results.append(result)
                    
                    print(f"{key_size:<8} {n_bits:<8} {method:<15} {fact_time:<12.6f} {str(iterations):<15} {'TAK' if success else 'NIE':<8} {factors_str}")
                
            except Exception as e:
                print(f"{key_size:<8} BŁĄD: {str(e)}")
                result = {
                    'key_size': key_size,
                    'generation_time': None,
                    'error': str(e)
                }
                results.append(result)
        
        return results
    
    @staticmethod
    def print_summary(results):
        """
        Wyświetla podsumowanie wyników testów.
        
        Args:
            results (list): Lista wyników z test_key_generation_and_factorization
        """
        print("\n" + "=" * 80)
        print("PODSUMOWANIE WYNIKÓW")
        print("=" * 80)
        
        successful_results = [r for r in results if 'error' not in r]
        
        if not successful_results:
            print("Brak udanych testów do podsumowania.")
            return
        
        print(f"{'Rozmiar':<8} {'Bity n':<8} {'Metoda':<15} {'Czas [s]':<12} {'Iteracje':<15} {'Złamany':<8}")
        print("-" * 80)
        
        for result in successful_results:
            key_size = result['key_size']
            n_bits = result.get('n_bits', 0)
            method = result.get('factorization_method', 'N/A')
            fact_time = result.get('factorization_time', 0)
            success = result.get('factorization_success', False)
            iterations = result.get('iterations', 'N/A')
            
            print(f"{key_size:<8} {n_bits:<8} {method:<15} {fact_time:<12.6f} {str(iterations):<15} {'TAK' if success else 'NIE':<8}")
        
        # Statystyki
        print("\n" + "=" * 50)
        print("STATYSTYKI")
        print("=" * 50)
        
        factorized_count = sum(1 for r in successful_results if r.get('factorization_success', False))
        total_tests = len(successful_results)
        
        print(f"Łącznie testów: {total_tests}")
        print(f"Udanych faktoryzacji: {factorized_count}")
        print(f"Procent złamanych: {(factorized_count/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        if factorized_count > 0:
            avg_fact_time = sum(r.get('factorization_time', 0) for r in successful_results if r.get('factorization_success', False)) / factorized_count
            print(f"Średni czas faktoryzacji: {avg_fact_time:.6f}s")


def is_prime(n):
    """
    Sprawdza czy liczba jest pierwsza używając biblioteki sympy.
    
    Args:
        n (int): Liczba do sprawdzenia
    
    Returns:
        bool: True jeśli liczba jest pierwsza
    """
    return isprime(n)


def generate_large_prime(bits):
    """
    Generuje dużą liczbę pierwszą o określonej liczbie bitów.
    
    Args:
        bits (int): Liczba bitów liczby pierwszej
    
    Returns:
        int: Liczba pierwsza
    """
    while True:
        # Generuj losową liczbę o określonej liczbie bitów
        # Upewnij się, że najwyższy bit jest ustawiony (żeby miała dokładnie tyle bitów)
        candidate = secrets.randbits(bits)
        candidate |= (1 << (bits - 1))  # Ustaw najwyższy bit
        candidate |= 1  # Ustaw najniższy bit (liczba nieparzysta)
        
        if is_prime(candidate):
            return candidate


def extended_gcd(a, b):
    """
    Rozszerzony algorytm Euklidesa.
    Zwraca (gcd, x, y) takie, że gcd = a*x + b*y
    
    Args:
        a (int): Pierwsza liczba
        b (int): Druga liczba
    
    Returns:
        tuple: (gcd, x, y)
    """
    if a == 0:
        return b, 0, 1
    
    gcd_val, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    
    return gcd_val, x, y


def mod_inverse(a, m):
    """
    Oblicza odwrotność modularną a^(-1) mod m używając rozszerzonego GCD.
    
    Args:
        a (int): Liczba
        m (int): Modulo
    
    Returns:
        int: Odwrotność modularna
    """
    # Sprawdź czy a i m są względnie pierwsze używając wbudowanej funkcji gcd
    if gcd(a, m) != 1:
        raise ValueError(f"Odwrotność modularna nie istnieje dla {a} mod {m} (nie są względnie pierwsze)")
    
    # Użyj rozszerzonego GCD do znalezienia współczynników
    gcd_val, x, _ = extended_gcd(a % m, m)
    return (x % m + m) % m


def generate_rsa_keys(key_length=768, e=65537):
    """
    Generuje parę kluczy RSA (publiczny i prywatny).
    
    Args:
        key_length (int): Długość klucza w bitach (domyślnie 768, minimum 768)
        e (int): Publiczny wykładnik (domyślnie 65537)
    
    Returns:
        tuple: ((n, e), (n, d)) - klucz publiczny i prywatny
    """
    if key_length < 768:
        raise ValueError("Długość klucza musi wynosić co najmniej 768 bitów")
    
    # Długość każdej liczby pierwszej (około połowa długości klucza)
    prime_bits = key_length // 2
    
    print(f"Generowanie kluczy RSA o długości {key_length} bitów...")
    print(f"Generowanie liczb pierwszych o długości {prime_bits} bitów...")
    
    # Generuj dwie liczby pierwsze
    p = generate_large_prime(prime_bits)
    print(f"Wygenerowano p ({p.bit_length()} bitów)")
    
    q = generate_large_prime(prime_bits)
    print(f"Wygenerowano q ({q.bit_length()} bitów)")
    
    # Oblicz n = p * q
    n = p * q
    print(f"n = p * q ({n.bit_length()} bitów)")
    
    # Oblicz φ(n) = (p-1)(q-1)
    phi_n = (p - 1) * (q - 1)
    print(f"φ(n) = (p-1)(q-1)")
    
    # Sprawdź czy e jest względnie pierwsze z φ(n)
    if gcd(e, phi_n) != 1:
        raise ValueError(f"e={e} nie jest względnie pierwsze z φ(n). Spróbuj innej wartości e.")
    
    # Oblicz d = e^(-1) mod φ(n)
    d = mod_inverse(e, phi_n)
    print(f"Obliczono d (prywatny wykładnik)")
    
    public_key = (n, e)
    private_key = (n, d)
    
    print(f"\nKlucz publiczny (n, e):")
    print(f"  n: {n}")
    print(f"  e: {e}")
    print(f"\nKlucz prywatny (n, d):")
    print(f"  n: {n}")
    print(f"  d: {d}")
    
    return public_key, private_key


# Przykład użycia
if __name__ == "__main__":
    import sys
    
    # Sprawdź argumenty wiersza poleceń
    if len(sys.argv) > 1 and sys.argv[1] == "--timing-test":
        # Test czasowy dla różnych rozmiarów kluczy
        key_sizes = [32, 40, 48, 56, 64, 72, 80, 88, 96, 128]
        # Dostępne metody faktoryzacji - konkretne algorytmy (zawsze dostępne)
        available_methods = [
            'sympy_pollard_rho',    # SymPy Pollard's Rho - O(n^1/4)
            'sympy_pollard_pm1',    # SymPy Pollard's p-1 - gdy p-1 ma małe czynniki  
            'simple_trial',         # Trial Division z limitem 100k (bezpieczne)
            'sympy_general'         # SymPy automatyczny wybór najlepszego algorytmu
        ]
        
        # Dodatkowe biblioteki (jeśli dostępne)
        if PYECM_AVAILABLE:
            available_methods.append('pyecm')
        if PRIMEFAC_AVAILABLE:
            available_methods.append('primefac')
        if GMPY2_AVAILABLE:
            available_methods.append('gmpy2')
        
        factorization_methods = available_methods
        
        print("URUCHAMIANIE TESTÓW CZASOWYCH RSA")
        print("Testowane rozmiary kluczy:", key_sizes)
        print("Dostępne metody faktoryzacji:", available_methods)
        
        # Informacje o metodach
        print("\nSTATUS METOD FAKTORYZACJI:")
        print(f"  SymPy Pollard's Rho: ✅ - O(n^1/4), probabilistyczny")
        print(f"  SymPy Pollard's p-1: ✅ - Gdy p-1 ma małe czynniki")
        print(f"  Simple Trial Division: ✅ - Limit 100k (bezpieczne dla małych kluczy)")
        print(f"  SymPy General: ✅ - Automatyczny wybór algorytmu")
        print(f"  PyECM (ECM): {'✅' if PYECM_AVAILABLE else '❌ (pip install pyecm)'} - Elliptic Curve Method")
        print(f"  primefac: {'✅' if PRIMEFAC_AVAILABLE else '❌ (pip install primefac)'} - MPQS, SIQS")
        print(f"  gmpy2: {'✅' if GMPY2_AVAILABLE else '❌ (pip install gmpy2)'} - GMP w C")
        
        print("\nUWAGA: Test 128-bitowych kluczy może trwać kilka minut!")
        
        results = RSATimingTest.test_key_generation_and_factorization(key_sizes, factorization_methods)
        RSATimingTest.print_summary(results)
        
        # Zapisz wyniki do pliku
        with open("rsa_timing_results.txt", "w") as f:
            f.write("RSA Timing Test Results\n")
            f.write("=" * 50 + "\n\n")
            for result in results:
                f.write(f"Key size: {result.get('key_size', 'N/A')} bits\n")
                f.write(f"Generation time: {result.get('generation_time', 'N/A')} seconds\n")
                f.write(f"n bits: {result.get('n_bits', 'N/A')}\n")
                f.write(f"Factorization method: {result.get('factorization_method', 'N/A')}\n")
                f.write(f"Factorization time: {result.get('factorization_time', 'N/A')} seconds\n")
                f.write(f"Factorization success: {result.get('factorization_success', 'N/A')}\n")
                if result.get('factors'):
                    f.write(f"Factors: {result['factors']}\n")
                f.write("-" * 30 + "\n")
        
        print(f"\nWyniki zapisane do pliku: rsa_timing_results.txt")
        
    else:
        # Standardowy przykład użycia RSA
        # Stwórz obiekt RSA
        rsa = RSA(key_length=768)
        
        # Generowanie kluczy RSA
        print("=" * 60)
        print("GENEROWANIE KLUCZY RSA")
        print("=" * 60)
        public_key, private_key = rsa.generate_keys()
        print("\n" + "=" * 60 + "\n")
        
        # Przykład szyfrowania i deszyfrowania wiadomości
        try:
            message = read_message("message.txt")
            print(f"Oryginalna wiadomość:\n'{message}'\n")
            
            print("=" * 60)
            print("SZYFROWANIE WIADOMOŚCI")
            print("=" * 60)
            
            # Zaszyfruj wiadomość
            encrypted_blocks = rsa.encrypt_message(message, num_blocks=10)
            print(f"\nWiadomość zaszyfrowana w {len(encrypted_blocks)} blokach")
            
            print("\n" + "=" * 60)
            print("DESZYFROWANIE WIADOMOŚCI")
            print("=" * 60)
            
            # Odszyfruj wiadomość
            decrypted_message = rsa.decrypt_message(encrypted_blocks)
            print(f"\nOdszyfrowana wiadomość:\n'{decrypted_message}'")
            
            print("\n" + "=" * 60)
            print("WERYFIKACJA")
            print("=" * 60)
            print(f"Oryginał:     '{message}'")
            print(f"Odszyfrowane: '{decrypted_message}'")
            print(f"Czy identyczne: {message == decrypted_message}")
            
        except FileNotFoundError as e:
            print(f"Błąd: {e}")
            print("Utwórz plik 'message.txt' z wiadomością do zaszyfrowania.")
            print("\nPrzykład zawartości pliku message.txt:")
            print("Hello World!")
        except Exception as e:
            print(f"Błąd podczas szyfrowania/deszyfrowania: {e}")
        
        print("\n" + "=" * 60)
        print("INFORMACJA O TESTACH CZASOWYCH")
        print("=" * 60)
        print("Aby uruchomić testy czasowe dla kluczy 32-128 bitów, użyj:")
        print("python main.py --timing-test")
        print("\nUWAGA: Testy mogą trwać długo dla większych kluczy!")

