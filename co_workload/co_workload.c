// co_workload.c - 动态施加 stress 负载，模拟系统压力
// 用法: ./controller [-d <ms>] [-p <pattern>]
//   -d <ms>      每个等级持续时间，默认 500ms
//   -p <pattern> 负载 pattern，如 "0,1,2,3,4,5,6,5,4,3,2,1,0"，或 "random"
//
// 编译: gcc -o controller co_workload.c -lrt
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <time.h>
#include "shared.h"

enum {
    NC = INTERF_LEVEL_NO_CACHE,
    L = INTERF_LEVEL_L,
    L_C8 = INTERF_LEVEL_L_C8,
    M = INTERF_LEVEL_M,
    H = INTERF_LEVEL_H,
    XH = INTERF_LEVEL_XH,
    XXH = INTERF_LEVEL_XXH,
    NUM_LEVELS = INTERF_LEVEL_NUM
};

static const char *level_cmds[NUM_LEVELS] = {
    "sleep 6000s",
    "taskset -c 9 stress-ng --cache 4 --cache-level 3 --timeout 6000s",
    "taskset -c 8 stress-ng --cache 4 --cache-level 3 --timeout 6000s",
    "taskset -c 9-11 stress-ng --cache 4 --cache-level 3 --timeout 6000s",
    "taskset -c 9-15 stress-ng --cache 7 --cache-level 3 --timeout 6000s",
    "taskset -c 8-15 stress-ng --cache 8 --cache-level 3  --timeout 6000s",
    "taskset -c 8-15 stress-ng --cache 16 --cache-level 3 --timeout 6000s",
};

static pid_t pids[NUM_LEVELS];
static shm_state_t *S;
static volatile sig_atomic_t running = 1;

// ---- 进程管理 ----

// 启动 stress-ng 进程，放入独立进程组
static pid_t spawn(const char *cmd)
{
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return -1;
    }
    if (pid == 0) {
        setpgid(0, 0); // 子进程：自己作为进程组 leader
        execl("/bin/sh", "sh", "-c", cmd, NULL);
        perror("execl");
        _exit(1);
    }
    setpgid(pid, pid); // 父进程也设置，避免竞争
    return pid;
}

// 清理：杀掉所有 stress-ng 进程组，清理共享内存
static void cleanup(void)
{
    fprintf(stderr, "\n[controller] cleaning up...\n");
    for (int i = 0; i < NUM_LEVELS; i++) {
        if (pids[i] > 0) {
            killpg(pids[i], SIGTERM);
            killpg(pids[i], SIGCONT); // 确保未暂停的进程能收到 SIGTERM
            waitpid(pids[i], NULL, 0);
        }
    }
    shm_unlink(SHM_NAME);
    fprintf(stderr, "[controller] done.\n");
}

static void sig_handler(int sig)
{
    (void)sig;
    running = 0;
}

// ---- 负载切换 ----

static void publish(int level, int type)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    uint64_t ns = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;

    atomic_store(&S->ts_ns, ns);
    atomic_store(&S->level, (uint_fast32_t)level);
    atomic_store(&S->type, (uint_fast32_t)type);
}

static void switch_to(int new_level)
{
    static int cur = -1;

    if (cur == new_level)
        return;

    // 暂停当前等级的整个进程组
    if (cur >= 0 && pids[cur] > 0)
        killpg(pids[cur], SIGSTOP);

    // 恢复新等级的整个进程组
    if (pids[new_level] > 0)
        killpg(pids[new_level], SIGCONT);

    cur = new_level;
}

// ---- 参数解析 ----

static void parse_pattern(const char *str, int **out_pattern, int *out_len)
{
    // "random" 模式
    if (strcmp(str, "random") == 0) {
        *out_pattern = NULL;
        *out_len = 0;
        return;
    }

    // 解析逗号分隔的数字，如 "0,1,2,3,4,5,6,5,4,3,2,1,0"
    int cap = 16, len = 0;
    int *pat = malloc(cap * sizeof(int));
    const char *p = str;
    while (*p) {
        int val = (int)strtol(p, (char **)&p, 10);
        if (val < 0 || val >= NUM_LEVELS) {
            fprintf(stderr, "[controller] invalid level %d in pattern, clamping to 0\n", val);
            val = 0;
        }
        if (len >= cap) {
            cap *= 2;
            pat = realloc(pat, cap * sizeof(int));
        }
        pat[len++] = val;
        if (*p == ',') p++;
    }
    *out_pattern = pat;
    *out_len = len;
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s [-d <ms>] [-p <pattern>]\n"
            "  -d <ms>      Duration per level in ms (default: 500)\n"
            "  -p <pattern> Level pattern, e.g. \"0,1,2,3,4,5,6,5,4,3,2,1,0\" or \"random\"\n"
            "               0=NO_CACHE, 1=LOW, 2=LOW_C8, 3=MED, 4=HIGH, 5=XHIGH, 6=XXHIGH\n"
            "               default: \"0,1,2,3,4,5,6,5,4,3,2,1,0\"\n",
            prog);
}

// ---- main ----

int main(int argc, char *argv[])
{
    int duration_ms = 500;
    const char *pattern_str = "0,1,2,3,4,5,6,5,4,3,2,1,0";
    int *pattern = NULL;
    int pattern_len = 0;
    int random_mode = 0;

    int opt;
    while ((opt = getopt(argc, argv, "d:p:h")) != -1) {
        switch (opt) {
        case 'd':
            duration_ms = atoi(optarg);
            if (duration_ms < 10) {
                fprintf(stderr, "[controller] duration too small, setting to 10ms\n");
                duration_ms = 10;
            }
            break;
        case 'p':
            pattern_str = optarg;
            break;
        case 'h':
        default:
            usage(argv[0]);
            return opt == 'h' ? 0 : 1;
        }
    }

    parse_pattern(pattern_str, &pattern, &pattern_len);
    random_mode = (pattern == NULL);

    // 注册信号处理
    struct sigaction sa = {.sa_handler = sig_handler};
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    // 初始化共享内存
    S = shm_init(1);
    if (!S) {
        fprintf(stderr, "[controller] failed to init shared memory\n");
        return 1;
    }

    // 初始状态
    publish(NC, INTERF_TYPE_MIX);

    fprintf(stderr, "[controller] starting stress-ng processes...\n");

    // 预启动各档负载进程。NO_CACHE 使用 sleep 占位，不产生 stress-ng 负载。
    for (int i = 0; i < NUM_LEVELS; i++) {
        pids[i] = spawn(level_cmds[i]);
        if (pids[i] < 0) {
            fprintf(stderr, "[controller] failed to spawn level %d\n", i);
            cleanup();
            return 1;
        }
    }

    // 等待 stress-ng 的 worker 启动完成
    sleep(2);

    // 全部暂停
    for (int i = 0; i < NUM_LEVELS; i++)
        killpg(pids[i], SIGSTOP);

    fprintf(stderr, "[controller] all processes paused. duration=%dms mode=%s\n",
            duration_ms, random_mode ? "random" : pattern_str);

    // 主循环
    int idx = 0;
    srand((unsigned)time(NULL));

    while (running) {
        int level;
        if (random_mode) {
            level = rand() % NUM_LEVELS;
        } else {
            level = pattern[idx];
            idx = (idx + 1) % pattern_len;
        }

        switch_to(level);
        publish(level, INTERF_TYPE_MIX);

        fprintf(stderr, "[controller] level=%s (%d)\n", INTERF_LEVEL_NAMES[level], level);

        // 使用 usleep 循环，便于快速响应退出信号
        int elapsed_ms = 0;
        while (running && elapsed_ms < duration_ms) {
            usleep(10000); // 10ms
            elapsed_ms += 10;
        }
    }

    cleanup();
    free(pattern);
    return 0;
}
