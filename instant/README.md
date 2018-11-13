# Aktualizacja

Za oryginalną wersję kompilatora, umieszczoną na Moodle 7 listopada o 14:24,
otrzymałem ocenę 0/6 z komentarzem "Nie działa, proszę o osobistą prezentację".
Skrypt uruchamiający kompilator w tamtej wersji zawierał błąd niepozwalający
na uruchomienie go ścieżką bezwzględną (działało `./insc_jvm` lub `../insc_jvm`
itp., ale nie `/home/staff/iinf/ben/var/Mrj/2018/Instant/Raszkiewicz/insc_jvm`).

Ta paczka zawiera poprawki w skryptach naprawiające powyższy błąd, bez zmian
we właściwym kompilatorze (tj. zmieniły się tylko pliki `insc_jvm`, `insv_llvm`,
`main.py`).

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
Skrypt wymaga modułu `venv` do Pythona, na studensie jest zainstalowany,
w Ubuntu można zainstalować używając `sudo apt install python3-venv`.

Uruchomienie `make` generuje parser gramatyki za pomocą ANTLR.
Przy pierwszych uruchomieniu zostanie pobrany plik `antlr-4.7.1-complete.jar`,
który zajmuje około 2,2 MB.


# Używane bibliteki

* ANTLR4 (http://www.antlr.org/) - używany zamiast BNFC do generowania
  parsera języka Instant.


# Struktura projektu

* `src/main.py`, `src/JVMCompiler.py`, `src/LLVMCompiler.py` - pliki źródłowe
* `src/Instant.g4` - gramatyka Instant w formacie ANTLR
* `src/antlr_generated/*` - parser wygenerowany przez ANTLR
* `lib/antlr-4.7.1-complete.jar` - biblioteka ANTLR generująca parser
  (pobierana przez `make`)
* `lib/jasmin.jar` - Jasmin używany do kompilacji plików `.j` do `.class`
* `insc_jvm`, `insv_llvm` - skrypty uruchamiające kompilator
