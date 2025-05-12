
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void get_shell() {
    system("/bin/sh");
}

void check_null(char *buf, int len) {
    for (int i = 0; i < len; i++) {
        if (buf[i] == '\0') {
            puts("Null detected! Intent nullified.");
            memset((void *)get_shell, 0, 0x100);
            break;
        }
    }
}

void vuln() {
    char buf[64];
    puts("Give me your power:");
    read(0, buf, 256);
    check_null(buf, 256);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
