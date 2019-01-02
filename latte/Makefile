compiler: grammar py3_venv/bin/python3

grammar: src/antlr_generated/LatteLexer.py src/antlr_generated/LatteParser.py

py3_venv/bin/python3:
	./make_venv.sh

src/antlr_generated/LatteLexer.py src/antlr_generated/LatteParser.py: src/Latte.g4 lib/antlr-4.7.1-complete.jar
	set -e; \
	cd src; \
	mkdir -p antlr_generated; \
	java -jar ../lib/antlr-4.7.1-complete.jar Latte.g4 -no-listener -Dlanguage=Python3 -o antlr_generated

lib/antlr-4.7.1-complete.jar:
	wget https://www.antlr.org/download/antlr-4.7.1-complete.jar -O lib/antlr-4.7.1-complete.jar

clean:
	rm -rf src/antlr_generated/ src/__pycache__/ py3_venv/ lib/antlr-4.7.1-complete.jar

.PHONY: grammar clean
