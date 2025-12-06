# Implementacja RSA z eksperymentem faktoryzacji

Kompletna implementacja RSA w Pythonie z eksperymentem faktoryzacji dla różnych długości kluczy.

## Wymagania

- Python 3.7+
- Biblioteki: `sympy`, `matplotlib`, `numpy`

## Instalacja

```bash
pip install -r requirements.txt
```

## Użycie

### Podstawowe użycie (demonstracja RSA + eksperyment faktoryzacji)

```bash
python3 rsa_implementation.py message.txt --alphabet ascii --key-length 768
```

### Tylko eksperyment faktoryzacji (pomijając demonstrację RSA)

```bash
python3 rsa_implementation.py message.txt --skip-rsa
```

### Parametry

- `message_file`: Ścieżka do pliku z wiadomością (wymagane)
- `--alphabet`: Wybór alfabetu: `26` (litery), `64` (Base64), `ascii` (domyślnie)
- `--key-length`: Długość klucza RSA w bitach (domyślnie 768)
- `--skip-rsa`: Pomiń demonstrację RSA, uruchom tylko eksperyment faktoryzacji

## Gotowe skrypty testowe

### Test implementacji RSA z pliku message.txt

#### Test z alfabetem ASCII (domyślny)

```bash
python3 rsa_implementation.py message.txt --alphabet ascii --key-length 768
```

#### Test z alfabetem 26-literowym

```bash
python3 rsa_implementation.py message.txt --alphabet 26 --key-length 768
```

#### Test z alfabetem Base64

```bash
python3 rsa_implementation.py message.txt --alphabet 64 --key-length 768
```

#### Test z różnymi długościami klucza

```bash
# Klucz 1024-bitowy
python3 rsa_implementation.py message.txt --alphabet ascii --key-length 1024

# Klucz 2048-bitowy (może zająć więcej czasu)
python3 rsa_implementation.py message.txt --alphabet ascii --key-length 2048
```

### Test eksperymentu faktoryzacji

#### Tylko eksperyment faktoryzacji (bez demonstracji RSA)

```bash
python3 rsa_implementation.py message.txt --skip-rsa
```

Ten skrypt:

- Generuje losowe klucze RSA o długościach: 32, 40, 48, 56, 64, 72, 80, 88, 96, 128 bitów
- Dla każdej długości generuje 5 próbek
- Faktoryzuje każdy moduł używając `sympy.factorint()`
- Mierzy czas faktoryzacji
- Zapisuje wyniki do `factorization_results.csv`
- Generuje wykres z dopasowaniami krzywych (liniową, potęgową, wykładniczą)
- Ekstrapoluje czasy dla 512 i 1024 bitów
- Wyświetla analizę wiarygodności prognoz

**Uwaga:** Eksperyment może zająć kilka minut, szczególnie dla większych długości kluczy (96, 128 bitów).

### Szybki test (tylko małe klucze)

Jeśli chcesz przetestować tylko mniejsze klucze, możesz zmodyfikować w kodzie:

```python
BIT_LENGTHS = [32, 40, 48, 56, 64]  # Tylko mniejsze klucze
SAMPLES_PER_SIZE = 1  # Mniej próbek na długość
```

## Wyjście

Program generuje:

1. **factorization_results.csv** - Wyniki eksperymentu faktoryzacji z czasami dla różnych długości kluczy
2. **factorization_times.png** - Wykres średnich czasów faktoryzacji w zależności od długości klucza

### Wyświetlanie wyników w czytelnej formie

Aby wyświetlić dane z pliku CSV w formie czytelnej tabeli, użyj skryptu:

```bash
python3 view_results.py
```

Skrypt oferuje kilka trybów wyświetlania:

- **Tryb 1**: Tabela szczegółowa (wszystkie rekordy)
- **Tryb 2**: Statystyki (podsumowanie)
- **Tryb 3**: Pogrupowane po metodzie
- **Tryb 4**: Wszystko (domyślny)

Możesz też wybrać tryb bezpośrednio:

```bash
python3 view_results.py 2  # Tylko statystyki
python3 view_results.py 4  # Wszystko
```

## Struktura kodu

- **Alfabety**: Definicje trzech alfabetów (26, 64, ASCII)
- **Przetwarzanie wiadomości**: Wczytywanie, normalizacja, podział na bloki
- **Konwersja bloków**: Mapowanie bloków znaków na liczby i z powrotem
- **RSA**: Generowanie kluczy, szyfrowanie, deszyfrowanie
- **Eksperyment faktoryzacji**: Faktoryzacja modułów RSA o różnych długościach, pomiar czasu, zapis wyników
