#!/usr/bin/env python3

import os
import subprocess


def test_good(test_dir):
    oks = 0
    errors = 0
    for f in sorted(os.listdir(test_dir)):
        if not f.endswith('.lat'):
            continue
        print()
        test_name = f.replace('.lat', '')
        print(test_name)
        lat_path = os.path.join(test_dir, f)
        with open(lat_path, 'r') as f:
            first_line = f.read().strip().split('\n')[0]
            if first_line[:2] in ('//', '/*'):
                print(first_line)
        out_path = os.path.join(test_dir, test_name + '.output')
        with open(out_path, 'r') as f:
            correct_out = f.read()
        ps = subprocess.Popen(['./latc_llvm', lat_path])
        ps.wait()
        if ps.returncode != 0:
            print('### COMPILATION ERROR')
            errors += 1
            continue
        program_input = None
        in_path = os.path.join(test_dir, test_name + '.input')
        if os.path.isfile(in_path):
            program_input = open(in_path, 'r')
        bc_path = os.path.join(test_dir, test_name + '.bc')
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
    return f'{test_dir}: OK {oks} / ERRORS {errors}'


def test_bad(test_dir):
    oks = 0
    errors = 0
    for f in sorted(os.listdir(test_dir)):
        if not f.endswith('.lat'):
            continue
        print()
        test_name = f.replace('.lat', '')
        print(test_name)
        lat_path = os.path.join(test_dir, f)
        with open(lat_path, 'r') as f:
            first_line = f.read().strip().split('\n')[0]
            if first_line[:2] in ('//', '/*'):
                print(first_line)
        ps = subprocess.Popen(['./latc_llvm', lat_path])
        ps.wait()
        if ps.returncode != 0:
            print('### COMPILATION ERROR (OK)')
            oks += 1
        else:
            print('### COMPILED SUCCESFULLY (ERROR)')
            errors += 1
    return f'{test_dir}: OK {oks} / ERRORS {errors}'


def main():
    reports = []
    reports.append(test_bad('./lattests/bad/'))
    reports.append(test_good('./lattests/good/'))
    reports.append(test_bad('./lattests/extensions/arrays1/'))
    reports.append(test_bad('./lattests/extensions/objects1/'))
    reports.append(test_bad('./lattests/extensions/objects2/'))
    reports.append(test_bad('./lattests/extensions/struct/'))
    print('\n'.join(reports))


if __name__ == '__main__':
    main()