# Uruchamianie

W skrócie:
* wymagany Python >= 3.6.0
* `source make_venv.sh`
* `make`
* `./insc_jvm file.ins` lub `./insc_llvm file.ins`

Kompilator jest napisany w Pythonie 3 i był testowany z wersjami:
3.7.0 (dostępna na students) oraz 3.6.1. Powinien działać z dowolnym
Pythonem w wersji >= 3.6.0, na pewno nie zadziała z wersjami < 3.6.

Do uruchomienia kompilatora niezbędne jest zainstalowanie używanych bibliotek,
co można zrobić za pomocą `pip3 install -r requirements.txt`
(powinno pobrać tylko około 110 kB danych).

W przypadku uruchamiania kompilatora w środowisku bez uprawnień do instalacji
bibliotek (np. students), dostarczony jest skrypt `make_venv.sh` tworzący
środowisko wirtualne i instalujący w nim zależności. Można go uruchomić
za pomocą `./make_venv.sh` i później aktywować środowisko
(`source py3_venv/bin/activate`) lub uruchomić `source make_venv.sh`,
co utworzy i od razu aktywuje środowisko
(również pobierając około 110 kB danych).

Uruchomienie `make` generuje parser gramatyki za pomocą ANTLR.


# Używane bibliteki

* ANTLR4 (http://www.antlr.org/) - używany zamiast BNFC do generowania
  parsera języka Instant.


# Struktura projektu

* `src/main.py`, `src/JVMCompiler.py`, `src/LLVMCompiler.py` - pliki źródłowe
* `src/Instant.g4` - gramatyka Instant w formacie ANTLR
* `src/antlr_generated/*` - parser wygenerowany przez ANTLR
* `lib/antlr-4.7.1-complete.jar` - biblioteka ANTLR generująca parser
* `lib/jasmin.jar` - Jasmin używany do kompilacji plików `.j` do `.class`
* `insc_jvm`, `insv_llvm` - skrypty uruchamiające kompilator