compiler: grammar

grammar: src/antlr_generated/InstantLexer.py src/antlr_generated/InstantListener.py src/antlr_generated/InstantParser.py

src/antlr_generated/InstantLexer.py src/antlr_generated/InstantListener.py src/antlr_generated/InstantParser.py: src/Instant.g4
	cd src && \
	mkdir -p antlr_generated && \
	java -jar ../antlr-4.7.1-complete.jar Instant.g4 -listener -Dlanguage=Python3 -o antlr_generated

clean:
	rm -rf src/antlr_generated

.PHONY: grammar clean
