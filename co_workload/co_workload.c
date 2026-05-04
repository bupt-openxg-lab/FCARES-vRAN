// controller.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <time.h>
#include "shared.h"

enum { L=0, M=1, H=2 };

pid_t pids[3];
shm_state_t* S;

pid_t spawn(const char* cmd) {
    pid_t pid = fork();
    if (pid == 0) {
        execl("/bin/sh", "sh", "-c", cmd, NULL);
        exit(1);
    }
    return pid;
}

void publish(int level) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    uint64_t ns = ts.tv_sec * 1000000000ULL + ts.tv_nsec;

    atomic_store(&S->ts_ns, ns);
    atomic_store(&S->level, level);
    atomic_store(&S->type, 2); // MIX
}

void switch_to(int new_level) {
    static int cur = -1;

    if (cur == new_level) return;

    if (cur != -1) kill(pids[cur], SIGSTOP);
    kill(pids[new_level], SIGCONT);

    cur = new_level;
}

int main() {
    int fd = shm_open("/oai_interf", O_CREAT|O_RDWR, 0666);
    ftruncate(fd, sizeof(shm_state_t));
    S = mmap(NULL, sizeof(*S), PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

    // 预启动
    pids[L] = spawn("stress-ng --cpu 1 --vm 1 --vm-bytes 256M");
    pids[M] = spawn("stress-ng --cpu 2 --vm 2 --vm-bytes 1G");
    pids[H] = spawn("stress-ng --cpu 4 --vm 4 --vm-bytes 4G");

    sleep(1); // 等进程起来

    for (int i=0;i<3;i++) kill(pids[i], SIGSTOP);

    int pattern[] = {L,M,H,M,L};
    int idx = 0;

    while (1) {
        int level = pattern[idx];

        switch_to(level);
        publish(level);

        usleep(10000); // 10ms

        idx = (idx+1)%5;
    }
}