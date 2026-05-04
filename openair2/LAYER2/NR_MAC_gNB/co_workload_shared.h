// shared.h
#ifndef SHARED_H
#define SHARED_H

#include <stdint.h>
#include <stdatomic.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>

// 干扰强度等级
typedef enum {
    INTERF_LEVEL_L = 0,
    INTERF_LEVEL_M = 1,
    INTERF_LEVEL_H = 2
} interf_level_t;

// 干扰类型
typedef enum {
    INTERF_TYPE_CPU = 0,
    INTERF_TYPE_MEM = 1,
    INTERF_TYPE_MIX = 2
} interf_type_t;

// 等级名称（用于日志打印）
static const char* const INTERF_LEVEL_NAMES[] = {"LOW", "MED", "HIGH"};
static const char* const INTERF_TYPE_NAMES[]  = {"CPU", "MEM", "MIX"};

// 共享状态结构（一个 cache line 内，避免 false sharing）
typedef struct __attribute__((aligned(64))) {
    atomic_uint_fast64_t ts_ns;   // 时间戳（CLOCK_MONOTONIC_RAW）
    atomic_uint_fast32_t level;   // L/M/H
    atomic_uint_fast32_t type;    // CPU/MEM/MIX
} shm_state_t;

#define SHM_NAME "/oai_interf"

// 初始化共享内存
// create=1: controller 端，创建并清零
// create=0: gNB 端，只读方式打开（打开失败返回 NULL）
static inline shm_state_t* shm_init(int create) {
    int fd;

    if (create) {
        fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
        if (fd < 0) { perror("shm_open create"); return NULL; }
        if (ftruncate(fd, sizeof(shm_state_t)) < 0) { perror("ftruncate"); close(fd); return NULL; }
    } else {
        fd = shm_open(SHM_NAME, O_RDONLY, 0666);
        if (fd < 0) return NULL;  // controller 未启动，静默返回 NULL
    }

    int prot = create ? (PROT_READ | PROT_WRITE) : PROT_READ;
    shm_state_t *p = (shm_state_t*)mmap(NULL, sizeof(shm_state_t), prot, MAP_SHARED, fd, 0);
    close(fd);

    if (p == MAP_FAILED) { perror("mmap"); return NULL; }
    return p;
}

#endif
