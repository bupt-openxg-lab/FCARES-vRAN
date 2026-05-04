// shared.h
#ifndef SHARED_H
#define SHARED_H

#include <stdint.h>
#include <stdatomic.h>

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

// 共享状态结构（一个 cache line 内，避免 false sharing）
typedef struct {
    atomic_uint_fast64_t ts_ns;   // 时间戳（CLOCK_MONOTONIC_RAW）
    atomic_uint_fast32_t level;   // L/M/H
    atomic_uint_fast32_t type;    // CPU/MEM/MIX
} shm_state_t;

#define SHM_NAME "/oai_interf"

// 初始化共享内存（controller 和 gNB 都可以用）
static inline shm_state_t* shm_init(int create) {
    int fd;

    if (create) {
        fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
        ftruncate(fd, sizeof(shm_state_t));
    } else {
        fd = shm_open(SHM_NAME, O_RDWR, 0666);
    }

    return (shm_state_t*)mmap(NULL,
                              sizeof(shm_state_t),
                              PROT_READ | PROT_WRITE,
                              MAP_SHARED,
                              fd,
                              0);
}

#endif