compiler: download_warning grammar py3_venv/bin/python3 runtime

download_warning:
	@echo "A small (< 3 MB) amount of data might be downloaded."
	@echo

grammar: src/antlr_generated/LatteLexer.py src/antlr_generated/LatteParser.py

runtime: lib/runtime.bc

src/antlr_generated/LatteLexer.py src/antlr_generated/LatteParser.py: src/Latte.g4 lib/antlr-4.7.1-complete.jar
	set -e; \
	cd src; \
	mkdir -p antlr_generated; \
	java -jar ../lib/antlr-4.7.1-complete.jar Latte.g4 -no-listener -Dlanguage=Python3 -o antlr_generated

lib/antlr-4.7.1-complete.jar:
	wget https://www.antlr.org/download/antlr-4.7.1-complete.jar -O lib/antlr-4.7.1-complete.jar

py3_venv/bin/python3:
	./make_venv.sh

lib/runtime.bc: lib/runtime.ll
	llvm-as -o lib/runtime.bc lib/runtime.ll

lib/runtime.ll: lib/runtime.c
	clang -O3 -S -emit-llvm -o lib/runtime.ll lib/runtime.c

clean:
	rm -rf src/antlr_generated/ src/__pycache__/ py3_venv/ lib/antlr-4.7.1-complete.jar lib/runtime.bc lib/runtime.ll

.PHONY: download_warning grammar runtime clean
