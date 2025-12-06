#!/usr/bin/env python3
"""
Główny plik programu - używa wszystkich modułów do implementacji RSA i eksperymentu faktoryzacji.
"""

import argparse
from collections import defaultdict
from pathlib import Path

from rsa_crypto import RSACrypto, get_alphabet
from factorization import FactorizationExperiment
from results import ResultsManager
from visualization import Visualization


class Application:
    """Główna klasa aplikacji zarządzająca wszystkimi modułami."""
    
    def __init__(self):
        """Inicjalizuje aplikację z wszystkimi potrzebnymi modułami."""
        self.rsa_crypto = None
        self.experiment = None
        self.results_manager = ResultsManager()
        self.visualizer = Visualization(extrapolation_bits=[256, 512])
    
    def run_rsa_demo(self, message_file: str, alphabet_choice: str, key_length: int):
        """
        Uruchamia demonstrację RSA.
        
        Args:
            message_file: Ścieżka do pliku z wiadomością
            alphabet_choice: Wybór alfabetu ('26', '64', 'ascii')
            key_length: Długość klucza RSA w bitach
        """
        print("\n" + "="*60)
        print("CZĘŚĆ I: IMPLEMENTACJA RSA")
        print("="*60)
        
        # Inicjalizuj obiekt RSA
        alphabet = get_alphabet(alphabet_choice)
        self.rsa_crypto = RSACrypto(alphabet=alphabet)        
        
        # Sprawdź, czy plik istnieje
        message_path = Path(message_file)
        if not message_path.exists():
            print(f"Błąd: Plik {message_file} nie istnieje!")
            return False
        
        # Wczytaj wiadomość
        original_message = self.rsa_crypto.read_message(str(message_path))
        
        # Podziel na bloki
        blocks = self.rsa_crypto.split_into_blocks(original_message, block_size=10)        
        
        # Wygeneruj klucz        
        key = RSACrypto.generate_keypair(bit_length=key_length)
        print(f"✓ Wygenerowano klucz:")
        print(f"  n = {key.n} ({key.n.bit_length()} bitów)")
        print(f"  e = {key.e}")
        print(f"  p = {key.p}")
        print(f"  q = {key.q}")
        
        # Szyfruj        
        try:
            cipher_blocks = self.rsa_crypto.encrypt_message_blocks(blocks, key)
            print(f"✓ Zaszyfrowano {len(cipher_blocks)} bloków")
        except ValueError as e:
            print(f"✗ Błąd szyfrowania: {e}")
            print("  Spróbuj zwiększyć długość klucza lub zmniejszyć rozmiar bloku.")
            return False
        
        # Deszyfruj
        decrypted_blocks = self.rsa_crypto.decrypt_message_blocks(cipher_blocks, key, block_size=10)
        print(f"✓ Odszyfrowano {len(decrypted_blocks)} bloków")
        decrypted_message = ''.join(decrypted_blocks)
        padding_char = alphabet[0]
        decrypted_message = decrypted_message.rstrip(padding_char)
        
        # Sprawdź zgodność
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
        
        return True
    
    def run_factorization_experiment(self):
        """
        Uruchamia eksperyment faktoryzacji.
        
        Returns:
            Lista rekordów z wynikami
        """
        print("\n" + "="*60)
        print("CZĘŚĆ II: EKSPERYMENT Z FAKTORYZACJĄ")
        print("="*60)
        
        # Uruchom eksperyment faktoryzacji
        self.experiment = FactorizationExperiment()
        records = self.experiment.run()
        
        return records
    
    def save_results(self, records, csv_filename: str = "factorization_results.csv"):
        """
        Zapisuje wyniki do pliku CSV.
        
        Args:
            records: Lista rekordów do zapisania
            csv_filename: Nazwa pliku CSV
        """
        self.results_manager.save_to_csv(records, csv_filename)
    
    def create_visualization(self, records, plot_filename: str = "factorization_times.png"):
        """
        Tworzy wizualizację wyników.
        
        Args:
            records: Lista rekordów z wynikami
            plot_filename: Nazwa pliku z wykresem
        """
        self.visualizer.plot_factorization_results(records, plot_filename)
    
    @staticmethod
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
    
    def display_factorization_details(self, records):
        """
        Wyświetla szczegóły wyników faktoryzacji w formie czytelnej tabeli.
        
        Args:
            records: Lista rekordów z wynikami faktoryzacji
        """
        print("\n" + "="*120)
        print("SZCZEGÓŁY WYNIKÓW EKSPERYMENTU FAKTORYZACJI RSA")
        print("="*120)
        
        # Konwertuj rekordy FactorRecord na format słownikowy dla kompatybilności
        dict_records = []
        for record in records:
            dict_records.append({
                'bit_length': record.bit_length,
                'method': record.method,
                'n': record.n,
                'p': record.p,
                'q': record.q,
                'time_sec': record.time_sec,
                'iterations': record.iterations,
                'success': record.success
            })
        
        # Sortuj po długości klucza
        records_sorted = sorted(dict_records, key=lambda x: (x['bit_length'], x['method']))
        
        # Nagłówek tabeli
        print(f"\n{'Długość':<10} {'Metoda':<8} {'Czas':<25} {'Sukces':<8} {'n (bity)':<12} {'p':<20} {'q':<20}")
        print("-" * 120)
        
        # Wyświetl każdy rekord
        for record in records_sorted:
            bit_len = record['bit_length']
            method = record['method']
            time_str = self.format_time(record['time_sec'])
            success = "✓ TAK" if record['success'] else "✗ NIE"
            n_bits = record['n'].bit_length()
            p = record['p']
            q = record['q']
            
            print(f"{bit_len:<10} {method:<8} {time_str:<25} {success:<8} {n_bits:<12} {p:<20} {q:<20}")
        
        # Statystyki
        print("\n" + "="*120)
        print("STATYSTYKI")
        print("="*120)
        
        # Grupuj po długości klucza
        grouped = defaultdict(list)
        for record in dict_records:
            if record['success']:
                grouped[record['bit_length']].append(record['time_sec'])
        
        print(f"\n{'Długość klucza':<20} {'Liczba próbek':<20} {'Średni czas':<25} {'Min czas':<25} {'Max czas':<25}")
        print("-" * 120)
        
        for bit_length in sorted(grouped.keys()):
            times = grouped[bit_length]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"{bit_length} bitów{'':<15} {len(times):<20} {self.format_time(avg_time):<25} "
                  f"{self.format_time(min_time):<25} {self.format_time(max_time):<25}")
        
        # Statystyki ogólne
        all_times = [r['time_sec'] for r in dict_records if r['success']]
        total_samples = len(dict_records)
        successful = sum(1 for r in dict_records if r['success'])
        
        print("\n" + "-" * 120)
        print(f"Łączna liczba próbek: {total_samples}")
        print(f"Udanych faktoryzacji: {successful} ({100*successful/total_samples:.1f}%)")
        if all_times:
            print(f"Średni czas faktoryzacji: {self.format_time(sum(all_times)/len(all_times))}")
            print(f"Najszybsza faktoryzacja: {self.format_time(min(all_times))}")
            print(f"Najwolniejsza faktoryzacja: {self.format_time(max(all_times))}")
    
    def print_summary(self, records, csv_filename: str, plot_filename: str):
        """
        Wypisuje podsumowanie eksperymentu.
        
        Args:
            records: Lista rekordów z wynikami
            csv_filename: Nazwa pliku CSV
            plot_filename: Nazwa pliku z wykresem
        """
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
    parser.add_argument(
        '--show-details',
        action='store_true',
        default=True,
        help='Wyświetl szczegóły wyników faktoryzacji (domyślnie włączone)'
    )
    parser.add_argument(
        '--no-show-details',
        dest='show_details',
        action='store_false',
        help='Nie wyświetlaj szczegółów wyników faktoryzacji'
    )
    
    args = parser.parse_args()
    
    # Utwórz główną aplikację
    app = Application()
    
    # ========================================================================
    # CZĘŚĆ I: DEMONSTRACJA RSA
    # ========================================================================
    
    if not args.skip_rsa:
        success = app.run_rsa_demo(args.message_file, args.alphabet, args.key_length)
        if not success:
            return
    
    # ========================================================================
    # CZĘŚĆ II: EKSPERYMENT Z FAKTORYZACJĄ
    # ========================================================================
    
    records = app.run_factorization_experiment()
    
    # Zapisz wyniki
    csv_filename = "factorization_results.csv"
    app.save_results(records, csv_filename)
    
    # Utwórz wykresy
    plot_filename = "factorization_times.png"
    app.create_visualization(records, plot_filename)
    
    # Wyświetl szczegóły faktoryzacji, jeśli włączone
    if args.show_details:
        app.display_factorization_details(records)
    
    # Podsumowanie
    app.print_summary(records, csv_filename, plot_filename)


if __name__ == "__main__":
    main()

