#!/usr/bin/env python3

import os
import subprocess


oks = 0
errors = 0

GOOD_PATH = './lattests/good/'
for f in sorted(os.listdir(GOOD_PATH)):
    if not f.endswith('.lat'):
        continue
    print()
    test_name = f.replace('.lat', '')
    print(test_name)
    lat_path = os.path.join(GOOD_PATH, f)
    out_path = os.path.join(GOOD_PATH, test_name + '.output')
    with open(out_path, 'r') as f:
        correct_out = f.read()
    ps = subprocess.Popen(['./latc_llvm', lat_path])
    ps.wait()
    if ps.returncode != 0:
        print('### COMPILATION ERROR')
        errors += 1
        continue
    program_input = None
    in_path = os.path.join(GOOD_PATH, test_name + '.input')
    if os.path.isfile(in_path):
        program_input = open(in_path, 'r')
    bc_path = os.path.join(GOOD_PATH, test_name + '.bc')
    ps2 = subprocess.Popen(['lli', bc_path],
        stdin=program_input, stdout=subprocess.PIPE)
    my_out = str(ps2.communicate()[0], 'ascii')
    if program_input:
        program_input.close()
    if correct_out == my_out:
        print('### OUTPUTS OK')
        oks += 1
    else:
        print('### OUTPUTS MISMATCH')
        print('Correct output:')
        print(correct_out)
        print('My output:')
        print(my_out)
        errors += 1

print(f'OK {oks} / ERRORS {errors}')
