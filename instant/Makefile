compiler: grammar py3_venv/bin/python3

grammar: src/antlr_generated/InstantLexer.py src/antlr_generated/InstantParser.py

py3_venv/bin/python3:
	./make_venv.sh

src/antlr_generated/InstantLexer.py src/antlr_generated/InstantParser.py: src/Instant.g4 lib/antlr-4.7.1-complete.jar
	set -e; \
	cd src; \
	mkdir -p antlr_generated; \
	java -jar ../lib/antlr-4.7.1-complete.jar Instant.g4 -no-listener -Dlanguage=Python3 -o antlr_generated

lib/antlr-4.7.1-complete.jar:
	wget https://www.antlr.org/download/antlr-4.7.1-complete.jar -O lib/antlr-4.7.1-complete.jar

clean:
	rm -rf src/antlr_generated/ src/__pycache__/ py3_venv/ lib/antlr-4.7.1-complete.jar

.PHONY: grammar clean
