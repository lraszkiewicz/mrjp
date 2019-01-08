#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void printInt(int x) {
    printf("%d\n", x);
}

void printString(char *s) {
    puts(s);
}

void error() {
    puts("runtime error");
    exit(1);
}

int readInt() {
    int x;
    if (scanf("%d ", &x) == 1) {
        return x;
    } else {
        puts("Runtime error: read value is not an integer.");
        exit(1);
    }
}

char *readString() {
    size_t buf_size = 8;
    char *buf = malloc(buf_size);
    size_t read_chars = 0;
    char c = 1;
    while (c != 0) {
        if (read_chars == buf_size) {
            size_t new_buf_size = buf_size << 1;
            char *new_buf = malloc(new_buf_size);
            while (buf_size--) {
                new_buf[buf_size] = buf[buf_size];
            }
            buf_size = new_buf_size;
            free(buf);
            buf = new_buf;
        }
        c = getchar();
        if (c == EOF || c == '\n' || c == '\r') {
            c = 0;
        }
        buf[read_chars] = c;
        ++read_chars;
    }
    return buf;
}

char *strconcat(char *a, char *b) {
    size_t a_len = strlen(a);
    size_t b_len = strlen(b);
    char *s = malloc(a_len + b_len + 1);
    for (int i = 0; i < a_len; ++i) {
        s[i] = a[i];
    }
    for (int i = 0; i < b_len; ++i) {
        s[a_len + i] = b[i];
    }
    s[a_len + b_len] = 0;
    return s;
}
