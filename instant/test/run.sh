#!/usr/bin/env bash

cd bin

for i in {01..12}
do
    echo test${i}
    echo llvm
    lli test${i}.bc
    echo jvm
    java test${i}
done
