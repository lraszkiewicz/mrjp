#!/usr/bin/env bash

for i in {01..12}
do
    ../insc_llvm test${i}.ins
    ../insc_jvm test${i}.ins
done

mkdir -p out bin
mv *.ll *.j out/
mv *.bc *.class bin/
