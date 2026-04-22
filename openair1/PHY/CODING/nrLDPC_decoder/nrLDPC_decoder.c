

/*
 * Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The OpenAirInterface Software Alliance licenses this file to You under
 * the OAI Public License, Version 1.1  (the "License"); you may not use this file
 * except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.openairinterface.org/?page_id=698
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *-------------------------------------------------------------------------------
 * For more information about the OpenAirInterface (OAI) Software Alliance:
 *      contact@openairinterface.org
 */

/*!\file nrLDPC_decoder.c
 * \brief Defines thenrLDPC decoder
*/
#define _GNU_SOURCE
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include "PHY/sse_intrin.h"
#include "nrLDPCdecoder_defs.h"
#include "nrLDPC_types.h"
#include "nrLDPC_init.h"
#include "nrLDPC_mPass.h"
#include "nrLDPC_cnProc.h"
#include "nrLDPC_bnProc.h"
#include "openair1/PHY/CODING/coding_defs.h"
#include <sched.h>
#include "common/utils/perf.h"

static __thread ldpc_pmu_ctx_t g_ldpc_pmu_ctx;
static __thread int g_ldpc_pmu_init_done = 0;

static inline ldpc_pmu_ctx_t *get_ldpc_pmu_ctx(void)
{
  if (!g_ldpc_pmu_init_done) {
    if (ldpc_pmu_init(&g_ldpc_pmu_ctx) != 0) {
      return NULL;
    }
    g_ldpc_pmu_init_done = 1;
  }
  return &g_ldpc_pmu_ctx;
}


// #define PERF_L3_CACHE_RAW 83

// #define PERF_OpCacheMisses 0x428f
// #define PERF_OpCacheAccess 0x728f

// typedef struct {
//     int fd_cycles;
//     int fd_instr;
//     int fd_cache_ref;
//     int fd_cache_miss;
//     // int fd_OpCache_miss_raw;
//     // int fd_OpCache_access_raw;
//     int enabled;
//   } ldpc_pmu_ctx_t;
  
//   typedef struct {
//     uint64_t cycles;
//     uint64_t instr;
//     uint64_t cache_ref;
//     uint64_t cache_miss;
//     // uint64_t OpCache_miss_raw;
//     // uint64_t OpCache_access_raw;
//   } ldpc_pmu_result_t;

//   static __thread ldpc_pmu_ctx_t g_pmu_ctx;
//   static __thread int g_pmu_inited = 0;

//   static long ldpc_perf_event_open(struct perf_event_attr *hw_event, pid_t pid,
//                        int cpu, int group_fd, unsigned long flags)
//   {
//     return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
//   }
  
//   static int ldpc_open_event(uint32_t type, uint64_t config, int group_fd, int disabled)
// {
//     struct perf_event_attr pe;
//     memset(&pe, 0, sizeof(pe));
//     pe.type = type;
//     pe.size = sizeof(pe);
//     pe.config = config;
//     pe.disabled = disabled;
//     pe.exclude_kernel = 1;
//     pe.exclude_hv = 1;
//     pe.inherit = 0;

//     int fd = ldpc_perf_event_open(&pe, 0, -1, group_fd, 0);
//     return fd;
// }

// static int ldpc_open_hw_event(uint64_t config, int group_fd, int disabled)
// {
//     return ldpc_open_event(PERF_TYPE_HARDWARE, config, group_fd, disabled);
// }

// static int ldpc_open_raw_event(uint64_t raw_config, int group_fd, int disabled)
// {
//     return ldpc_open_event(PERF_TYPE_RAW, raw_config, group_fd, disabled);
// }
  
  
//   static void ldpc_pmu_init(ldpc_pmu_ctx_t *ctx)
//   {
//     memset(ctx, 0, sizeof(*ctx));
//     ctx->fd_cycles = -1;
//     ctx->fd_instr = -1;
//     ctx->fd_cache_ref = -1;
//     ctx->fd_cache_miss = -1;
//     // ctx->fd_OpCache_miss_raw = -1;
//     // ctx->fd_OpCache_access_raw = -1;
//     ctx->enabled = 0;
  
//     ctx->fd_cycles = ldpc_open_hw_event(PERF_COUNT_HW_CPU_CYCLES, -1, 1);
//     if (ctx->fd_cycles < 0) goto fail;
  
//     ctx->fd_instr = ldpc_open_hw_event(PERF_COUNT_HW_INSTRUCTIONS, ctx->fd_cycles, 0);
//     if (ctx->fd_instr < 0) goto fail;
  
//     ctx->fd_cache_ref = ldpc_open_hw_event(PERF_COUNT_HW_CACHE_REFERENCES, ctx->fd_cycles, 0);
//     if (ctx->fd_cache_ref < 0) goto fail;
  
//     ctx->fd_cache_miss = ldpc_open_hw_event(PERF_COUNT_HW_CACHE_MISSES, ctx->fd_cycles, 0);
//     if (ctx->fd_cache_miss < 0) goto fail;

//     // ctx->fd_OpCache_miss_raw = ldpc_open_raw_event(PERF_OpCacheMisses, ctx->fd_cycles, 0);
//     // if (ctx->fd_OpCache_miss_raw < 0) goto fail;
//     // ctx->fd_OpCache_access_raw = ldpc_open_raw_event(PERF_OpCacheAccess, ctx->fd_cycles, 0);
//     // if (ctx->fd_OpCache_access_raw < 0) goto fail;

//     ctx->enabled = 1;
//     return;
  
//   fail:
//     if (ctx->fd_cache_miss >= 0) close(ctx->fd_cache_miss);
//     if (ctx->fd_cache_ref >= 0) close(ctx->fd_cache_ref);
//     if (ctx->fd_instr >= 0) close(ctx->fd_instr);
//     if (ctx->fd_cycles >= 0) close(ctx->fd_cycles);
//     // if (ctx->fd_OpCache_access_raw) close(ctx->fd_OpCache_access_raw);
//     // if (ctx->fd_OpCache_miss_raw) close(ctx->fd_OpCache_miss_raw);
//     ctx->fd_cycles = ctx->fd_instr = ctx->fd_cache_ref = ctx->fd_cache_miss = -1;
//     ctx->enabled = 0;
//     assert(0);
//   }

//   static inline ldpc_pmu_ctx_t *ldpc_get_pmu_ctx(void)
// {
//     if (!g_pmu_inited) {
//         ldpc_pmu_init(&g_pmu_ctx);
//         g_pmu_inited = 1;
//     }
//     return &g_pmu_ctx;
// }

//   static void ldpc_pmu_reset_start(ldpc_pmu_ctx_t *ctx)
//   {
//     if (!ctx->enabled) return;
//     ioctl(ctx->fd_cycles, PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
//     ioctl(ctx->fd_cycles, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
//   }
  
//   static void ldpc_pmu_stop_read(ldpc_pmu_ctx_t *ctx, ldpc_pmu_result_t *res)
//   {
//     memset(res, 0, sizeof(*res));
//     if (!ctx->enabled) return;
  
//     ioctl(ctx->fd_cycles, PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
  
//     if (read(ctx->fd_cycles, &res->cycles, sizeof(res->cycles)) != sizeof(res->cycles))
//       res->cycles = 0;
//     if (read(ctx->fd_instr, &res->instr, sizeof(res->instr)) != sizeof(res->instr))
//       res->instr = 0;
//     if (read(ctx->fd_cache_ref, &res->cache_ref, sizeof(res->cache_ref)) != sizeof(res->cache_ref))
//       res->cache_ref = 0;
//     if (read(ctx->fd_cache_miss, &res->cache_miss, sizeof(res->cache_miss)) != sizeof(res->cache_miss))
//       res->cache_miss = 0;
//     // if (read(ctx->fd_OpCache_access_raw, &res->OpCache_access_raw ,sizeof(res->OpCache_access_raw)) != sizeof(res->OpCache_access_raw))
//     //   res->OpCache_access_raw = 0;
//     // if (read(ctx->fd_OpCache_miss_raw, &res->OpCache_miss_raw ,sizeof(res->OpCache_miss_raw)) != sizeof(res->OpCache_miss_raw))
//     //   res->OpCache_miss_raw = 0;
//   }
  
//   static void ldpc_pmu_close(ldpc_pmu_ctx_t *ctx)
//   {
//     if (ctx->fd_cache_miss >= 0) close(ctx->fd_cache_miss);
//     if (ctx->fd_cache_ref >= 0) close(ctx->fd_cache_ref);
//     if (ctx->fd_instr >= 0) close(ctx->fd_instr);
//     if (ctx->fd_cycles >= 0) close(ctx->fd_cycles);
//     // if (ctx->fd_OpCache_access_raw) close(ctx->fd_OpCache_access_raw);
//     // if (ctx->fd_OpCache_miss_raw) close(ctx->fd_OpCache_miss_raw);
//     ctx->fd_cycles = ctx->fd_instr = ctx->fd_cache_ref = ctx->fd_cache_miss = -1;
//     ctx->enabled = 0;
//   }
  
//   static void ldpc_log_pmu_stats(const char *tag, uint32_t iter, const ldpc_pmu_result_t *r,uint8_t codeblock_id)
//   {
//     double ipc = (r->cycles > 0) ? ((double)r->instr / (double)r->cycles) : 0.0;
//     double L3_miss_rate = (r->cache_ref > 0) ? ((double)r->cache_miss/ (double)r->cache_ref) : 0.0;
//     // double op_miss_rate = (r->OpCache_access_raw > 0) ? ((double)r->OpCache_miss_raw / (double)r->OpCache_access_raw) : 0.0;
  
//     LOG_W(PHY,
//           "[LDPC_PMU] id =%hhd, %s iter=%u cycles=%llu instr=%llu ipc=%.4f cache_ref=%llu cache_miss=%llu ,L3 miss rate = %.4f\n",
//           codeblock_id,
//           tag,
//           iter,
//           (unsigned long long)r->cycles,
//           (unsigned long long)r->instr,
//           ipc,
//           (unsigned long long)r->cache_ref,
//           (unsigned long long)r->cache_miss,
//           L3_miss_rate
//         );
//   }


#define UNROLL_CN_PROC 1
#define UNROLL_BN_PROC 1
#define UNROLL_BN_PROC_PC 1
#define UNROLL_BN2CN_PROC 1
/*----------------------------------------------------------------------
|                  cn processing files -->AVX512
/----------------------------------------------------------------------*/

//BG1-------------------------------------------------------------------
#if defined(__AVX512BW__)

#include "cnProc_avx512/nrLDPC_cnProc_BG1_R13_AVX512.h"
#include "cnProc_avx512/nrLDPC_cnProc_BG1_R23_AVX512.h"
#include "cnProc_avx512/nrLDPC_cnProc_BG1_R89_AVX512.h"
//BG2-------------------------------------------------------------------
#include "cnProc_avx512/nrLDPC_cnProc_BG2_R15_AVX512.h"
#include "cnProc_avx512/nrLDPC_cnProc_BG2_R13_AVX512.h"
#include "cnProc_avx512/nrLDPC_cnProc_BG2_R23_AVX512.h"

#elif defined(__AVX2__)

/*----------------------------------------------------------------------
|                  cn Processing files -->AVX2
/----------------------------------------------------------------------*/

//BG1------------------------------------------------------------------
#include "cnProc/nrLDPC_cnProc_BG1_R13_AVX2.h"
#include "cnProc/nrLDPC_cnProc_BG1_R23_AVX2.h"
#include "cnProc/nrLDPC_cnProc_BG1_R89_AVX2.h"
//BG2 --------------------------------------------------------------------
#include "cnProc/nrLDPC_cnProc_BG2_R15_AVX2.h"
#include "cnProc/nrLDPC_cnProc_BG2_R13_AVX2.h"
#include "cnProc/nrLDPC_cnProc_BG2_R23_AVX2.h"

#else

//BG1------------------------------------------------------------------
#include "cnProc128/nrLDPC_cnProc_BG1_R13_128.h"
#include "cnProc128/nrLDPC_cnProc_BG1_R23_128.h"
#include "cnProc128/nrLDPC_cnProc_BG1_R89_128.h"
//BG2 --------------------------------------------------------------------
#include "cnProc128/nrLDPC_cnProc_BG2_R15_128.h"
#include "cnProc128/nrLDPC_cnProc_BG2_R13_128.h"
#include "cnProc128/nrLDPC_cnProc_BG2_R23_128.h"
#endif

/*----------------------------------------------------------------------
|                 bn Processing files -->AVX2
/----------------------------------------------------------------------*/

//bnProcPc-------------------------------------------------------------
#ifdef __AVX2__
//BG1------------------------------------------------------------------
#include "bnProcPc/nrLDPC_bnProcPc_BG1_R13_AVX2.h"
#include "bnProcPc/nrLDPC_bnProcPc_BG1_R23_AVX2.h"
#include "bnProcPc/nrLDPC_bnProcPc_BG1_R89_AVX2.h"
//BG2 --------------------------------------------------------------------
#include "bnProcPc/nrLDPC_bnProcPc_BG2_R15_AVX2.h"
#include "bnProcPc/nrLDPC_bnProcPc_BG2_R13_AVX2.h"
#include "bnProcPc/nrLDPC_bnProcPc_BG2_R23_AVX2.h"
#else
#include "bnProcPc128/nrLDPC_bnProcPc_BG1_R13_128.h"
#include "bnProcPc128/nrLDPC_bnProcPc_BG1_R23_128.h"
#include "bnProcPc128/nrLDPC_bnProcPc_BG1_R89_128.h"
#include "bnProcPc128/nrLDPC_bnProcPc_BG2_R15_128.h"
#include "bnProcPc128/nrLDPC_bnProcPc_BG2_R13_128.h"
#include "bnProcPc128/nrLDPC_bnProcPc_BG2_R23_128.h"
#endif

//bnProc----------------------------------------------------------------

#if defined(__AVX512BW__)
//BG1-------------------------------------------------------------------
#include "bnProc_avx512/nrLDPC_bnProc_BG1_R13_AVX512.h"
#include "bnProc_avx512/nrLDPC_bnProc_BG1_R23_AVX512.h"
#include "bnProc_avx512/nrLDPC_bnProc_BG1_R89_AVX512.h"
//BG2 --------------------------------------------------------------------
#include "bnProc_avx512/nrLDPC_bnProc_BG2_R15_AVX512.h"
#include "bnProc_avx512/nrLDPC_bnProc_BG2_R13_AVX512.h"
#include "bnProc_avx512/nrLDPC_bnProc_BG2_R23_AVX512.h"

#elif defined(__AVX2__)
#include "bnProc/nrLDPC_bnProc_BG1_R13_AVX2.h"
#include "bnProc/nrLDPC_bnProc_BG1_R23_AVX2.h"
#include "bnProc/nrLDPC_bnProc_BG1_R89_AVX2.h"
//BG2 --------------------------------------------------------------------
#include "bnProc/nrLDPC_bnProc_BG2_R15_AVX2.h"
#include "bnProc/nrLDPC_bnProc_BG2_R13_AVX2.h"
#include "bnProc/nrLDPC_bnProc_BG2_R23_AVX2.h"
#else
#include "bnProc128/nrLDPC_bnProc_BG1_R13_128.h"
#include "bnProc128/nrLDPC_bnProc_BG1_R23_128.h"
#include "bnProc128/nrLDPC_bnProc_BG1_R89_128.h"
//BG2 --------------------------------------------------------------------
#include "bnProc128/nrLDPC_bnProc_BG2_R15_128.h"
#include "bnProc128/nrLDPC_bnProc_BG2_R13_128.h"
#include "bnProc128/nrLDPC_bnProc_BG2_R23_128.h"
#endif

//#define NR_LDPC_PROFILER_DETAIL(a) a
#define NR_LDPC_PROFILER_DETAIL(a)

#include "openair1/PHY/CODING/nrLDPC_extern.h"

#ifdef NR_LDPC_DEBUG_MODE
#include "nrLDPC_tools/nrLDPC_debug.h"
#endif

// decoder interface
/**
   \brief LDPC decoder API type definition
   \param p_decParams LDPC decoder parameters
   \param p_llr Input LLRs
   \param p_llrOut Output vector
   \param p_profiler LDPC profiler statistics
*/

static inline uint32_t nrLDPC_decoder_core(int8_t* p_llr,
                                           int8_t* p_out,
                                           uint32_t numLLR,
                                           t_nrLDPC_lut* p_lut,
                                           t_nrLDPC_dec_params* p_decParams,
                                           t_nrLDPC_time_stats* p_profiler,
                                           decode_abort_t* ab,
                                           uint8_t id);

int32_t LDPCinit()
{
  return 0;
}

int32_t LDPCshutdown()
{
  return 0;
}

int32_t LDPCdecoder(t_nrLDPC_dec_params* p_decParams,
                    uint8_t harq_pid,
                    uint8_t ulsch_id,
                    uint8_t C,
                    int8_t* p_llr,
                    int8_t* p_out,
                    t_nrLDPC_time_stats* p_profiler,
                    decode_abort_t* ab,
                    uint8_t id )
{


  uint32_t numLLR;
  t_nrLDPC_lut lut;
  t_nrLDPC_lut* p_lut = &lut;

  // Initialize decoder core(s) with correct LUTs
  numLLR = nrLDPC_init(p_decParams, p_lut);

  // Launch LDPC decoder core for one segment
  int numIter = nrLDPC_decoder_core(p_llr, p_out, numLLR, p_lut, p_decParams, p_profiler, ab, id);
  if (numIter > p_decParams->numMaxIter) {
    LOG_D(PHY, "set abort: %d, %d\n", numIter, p_decParams->numMaxIter);
    set_abort(ab, true);
  }
    return numIter;
}



/**
   \brief PerformsnrLDPC decoding of one code block
   \param p_llr Input LLRs
   \param p_out Output vector
   \param numLLR Number of LLRs
   \param p_lut Pointer to decoder LUTs
   \param p_decParamsnrLDPC decoder parameters
   \param p_profilernrLDPC profiler statistics
*/
static inline uint32_t nrLDPC_decoder_core(int8_t* p_llr,
                                           int8_t* p_out,
                                           uint32_t numLLR,
                                           t_nrLDPC_lut* p_lut,
                                           t_nrLDPC_dec_params* p_decParams,
                                           t_nrLDPC_time_stats* p_profiler,
                                           decode_abort_t* ab,
                                           uint8_t id)
{ 
   // -------------------- for perf -------------------
    time_stats_t iter_time = {0};
    start_meas(&iter_time);
    ldpc_pmu_ctx_t *pmu_ctx = get_ldpc_pmu_ctx();
    if (!pmu_ctx) assert(0);
    ldpc_pmu_snapshot_t s0, s1;
    ldpc_pmu_result_t diff;
    ldpc_pmu_snapshot(pmu_ctx, &s0);
    // ldpc_pmu_reset_start(pmu_ctx);
    // CPU LDPC decoder hit here 
    uint16_t Z          = p_decParams->Z;
    uint8_t  BG         = p_decParams->BG;
    uint8_t  R         = p_decParams->R; //Decoding rate: Format 15,13,... for code rates 1/5, 1/3,... */
    uint8_t  numMaxIter = p_decParams->numMaxIter;
    e_nrLDPC_outMode outMode = p_decParams->outMode;
   // int8_t* cnProcBuf=  cnProcBuf;
   // int8_t* cnProcBufRes= cnProcBufRes;

    int8_t cnProcBuf[NR_LDPC_SIZE_CN_PROC_BUF]    __attribute__ ((aligned(64))) = {0};
    int8_t cnProcBufRes[NR_LDPC_SIZE_CN_PROC_BUF] __attribute__ ((aligned(64))) = {0};
    int8_t bnProcBuf[NR_LDPC_SIZE_BN_PROC_BUF]    __attribute__ ((aligned(64))) = {0};
    int8_t bnProcBufRes[NR_LDPC_SIZE_BN_PROC_BUF] __attribute__ ((aligned(64))) = {0};
    int8_t llrRes[NR_LDPC_MAX_NUM_LLR]            __attribute__ ((aligned(64))) = {0};
    int8_t llrProcBuf[NR_LDPC_MAX_NUM_LLR] __attribute__((aligned(64))) = {0};

    // stop_meas(&total_time);
    // LOG_W(PHY,"init time 1:%.2f\n",get_time_meas_us(&total_time));

    // Minimum number of iterations is 1
    // 0 iterations means hard-decision on input LLRs
    // Initialize with parity check fail != 0
    
    if (!(*pmu_ctx).enabled) {
      LOG_W(PHY, "[LDPC_PMU] PMU unavailable, errno=%d\n", errno);
    }
    // stop_meas(&total_time);
    // LOG_W(PHY,"init time 2:%.2f\n",get_time_meas_us(&total_time));
    // Initialization
    NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->llr2llrProcBuf));
    nrLDPC_llr2llrProcBuf(p_lut, p_llr, llrProcBuf, Z, BG);
    NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->llr2llrProcBuf));
#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_initBuffer2File(nrLDPC_buffers_LLR_PROC);
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_LLR_PROC, llrProcBuf);
#endif

    NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->llr2CnProcBuf));
    if (BG == 1)
      nrLDPC_llr2CnProcBuf_BG1(p_lut, p_llr, cnProcBuf, Z);
    else
      nrLDPC_llr2CnProcBuf_BG2(p_lut, p_llr, cnProcBuf, Z);
    NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->llr2CnProcBuf));

#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_initBuffer2File(nrLDPC_buffers_CN_PROC);
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_CN_PROC, cnProcBuf);
#endif

    // init stage
    // stop_meas(&total_time);
    // LOG_W(PHY,"init time 3:%.2f\n",get_time_meas_us(&total_time));
    
    
    // CN processing
    NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->cnProc));
    if (BG==1) {
#ifndef UNROLL_CN_PROC
      nrLDPC_cnProc_BG1(p_lut, cnProcBuf, cnProcBufRes, Z);
#else        
        switch (R)
        {
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG1_R13_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG1_R13_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG1_R13_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }

            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG1_R23_AVX512(cnProcBuf,cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG1_R23_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else                
                nrLDPC_cnProc_BG1_R23_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }

            case 89:
            {
                #if defined(__AVX512BW__)
                 nrLDPC_cnProc_BG1_R89_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG1_R89_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG1_R89_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }

        }
#endif        
    } else {
#ifndef UNROLL_CN_PROC
        nrLDPC_cnProc_BG2(p_lut, cnProcBuf, cnProcBufRes, Z);
#else
        switch (R) {
            case 15:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG2_R15_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG2_R15_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG2_R15_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG2_R13_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG2_R13_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG2_R13_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG2_R23_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG2_R23_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG2_R23_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }

        }
#endif        
    }
    NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->cnProc));

#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_initBuffer2File(nrLDPC_buffers_CN_PROC_RES);
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_CN_PROC_RES, cnProcBufRes);
#endif

    NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->cn2bnProcBuf));
    if (BG == 1)
      nrLDPC_cn2bnProcBuf_BG1(p_lut, cnProcBufRes, bnProcBuf, Z);
    else
      nrLDPC_cn2bnProcBuf_BG2(p_lut, cnProcBufRes, bnProcBuf, Z);
    NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->cn2bnProcBuf));

#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_initBuffer2File(nrLDPC_buffers_BN_PROC);
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_BN_PROC, bnProcBuf);
#endif

    // BN processing
    NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->bnProcPc));

#ifndef UNROLL_BN_PROC_PC
    nrLDPC_bnProcPc(p_lut, bnProcBuf, bnProcBufRes, llrProcBuf, llrRes, Z);
#else        
    if (BG==1) {
        switch (R) {
            case 13:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG1_R13_AVX2(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#else
		nrLDPC_bnProcPc_BG1_R13_128(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#endif 
 		break;
            }
            case 23:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG1_R23_AVX2(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG1_R23_128(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#endif		
                break;
            }
            case 89:
            {
#ifdef __AVX2__
                nrLDPC_bnProcPc_BG1_R89_AVX2(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG1_R89_128(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#endif
                break;
            }
        }
    } else {
        switch (R) {
            case 15:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG2_R15_AVX2(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG2_R15_128(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#endif
                break;
            }
            case 13:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG2_R13_AVX2(bnProcBuf,bnProcBufRes,llrRes,llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG2_R13_128(bnProcBuf,bnProcBufRes,llrRes,llrProcBuf, Z);
#endif
                break;
            }

            case 23:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG2_R23_AVX2(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG2_R23_128(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#endif
                break;
            }
        }
    }
#endif

    NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->bnProcPc));

#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_initBuffer2File(nrLDPC_buffers_LLR_RES);
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_LLR_RES, llrRes);
#endif

    NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->bnProc));

    if (BG==1) {
#ifndef UNROLL_BN_PROC
        nrLDPC_bnProc(p_lut, bnProcBuf, bnProcBufRes, llrRes, Z);
#else
        switch (R) {
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG1_R13_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined (__AVX2__)
                nrLDPC_bnProc_BG1_R13_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG1_R13_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG1_R23_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
		nrLDPC_bnProc_BG1_R23_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG1_R23_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 89:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG1_R89_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG1_R89_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG1_R89_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
        }
#endif
    } else {
#ifndef UNROLL_BN2CN_PROC
        nrLDPC_bn2cnProcBuf_BG2(p_lut, bnProcBufRes, cnProcBuf, Z);
#else
        switch (R) {
            case 15:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG2_R15_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG2_R15_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG2_R15_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG2_R13_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG2_R13_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG2_R13_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }

            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG2_R23_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG2_R23_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG2_R23_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
        }
#endif        
   }

#ifdef NR_LDPC_PROFILER_DETAIL
    stop_meas(&p_profiler->bnProc);
#endif

#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_initBuffer2File(nrLDPC_buffers_BN_PROC_RES);
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_BN_PROC_RES, bnProcBufRes);
#endif

    // BN results to CN processing buffer
#ifdef NR_LDPC_PROFILER_DETAIL
    start_meas(&p_profiler->bn2cnProcBuf);
#endif
    if (BG == 1) nrLDPC_bn2cnProcBuf_BG1(p_lut, bnProcBufRes, cnProcBuf, Z);
    else         nrLDPC_bn2cnProcBuf_BG2(p_lut, bnProcBufRes, cnProcBuf, Z);
#ifdef NR_LDPC_PROFILER_DETAIL
    stop_meas(&p_profiler->bn2cnProcBuf);
#endif

#ifdef NR_LDPC_DEBUG_MODE
    nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_CN_PROC, cnProcBuf);
#endif

    // Parity Check not necessary here since it will fail
    // because first 2 cols/BNs in BG are punctured and cannot be
    // estimated after only one iteration

    // First iteration finished
    uint32_t numIter = 1;
    int32_t pcRes = 1; // pcRes is 0 if the ldpc decoder is succesful
    //first iteration perf test
    ldpc_pmu_snapshot(pmu_ctx, &s1);
    char buffer[20];
    // 格式化为 "init42" 或 "init 42" 等格式
    sprintf(buffer, "init (id = %hhd)", id);  // 将uint8_t作为整数打印
    ldpc_pmu_diff(&s0, &s1, &diff);
    ldpc_log_pmu_stats(buffer, 1, &diff);
    stop_meas(&iter_time);
    double init_time = get_time_meas_us(&iter_time);
    // ldpc_log_pmu_stats("init", 1, &pmu_res,id);
    
    // LOG_W(PHY,"init time %.2f\n",init_time);
    // ldpc_pmu_reset_start(pmu_ctx);
    start_meas(&iter_time);
    while ((numIter <= numMaxIter) && (pcRes != 0)) {
    
      // Increase iteration counter
      // start_meas(&iter_time);
      numIter++;
      if (check_abort(ab)) {
        numIter = numMaxIter + 2;
        break;
      }
      // 
      // CN processing
#ifdef NR_LDPC_PROFILER_DETAIL
        start_meas(&p_profiler->cnProc);
#endif
        if (BG==1) {
#ifndef UNROLL_CN_PROC
           nrLDPC_cnProc_BG1(p_lut, cnProcBuf, cnProcBufRes, Z);
#else        
           switch (R) {
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG1_R13_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG1_R13_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG1_R13_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG1_R23_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG1_R23_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG1_R23_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
            case 89:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG1_R89_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG1_R89_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG1_R89_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
           }
#endif        
        } else {
#ifndef UNROLL_CN_PROC
           nrLDPC_cnProc_BG2(p_lut, cnProcBuf, cnProcBufRes, Z);
#else
           switch (R) {
            case 15:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG2_R15_AVX512(cnProcBuf,cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG2_R15_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG2_R15_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG2_R13_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG2_R13_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG2_R13_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            } 
            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_cnProc_BG2_R23_AVX512(cnProcBuf, cnProcBufRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_cnProc_BG2_R23_AVX2(cnProcBuf, cnProcBufRes, Z);
                #else
                nrLDPC_cnProc_BG2_R23_128(cnProcBuf, cnProcBufRes, Z);
                #endif
                break;
            }
          }  
#endif
        }
#ifdef NR_LDPC_PROFILER_DETAIL
        stop_meas(&p_profiler->cnProc);
#endif

#ifdef NR_LDPC_DEBUG_MODE
        nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_CN_PROC_RES, cnProcBufRes);
#endif

        // Send CN results back to BNs
#ifdef NR_LDPC_PROFILER_DETAIL
        start_meas(&p_profiler->cn2bnProcBuf);
#endif
        if (BG == 1) nrLDPC_cn2bnProcBuf_BG1(p_lut, cnProcBufRes, bnProcBuf, Z);
        else         nrLDPC_cn2bnProcBuf_BG2(p_lut, cnProcBufRes, bnProcBuf, Z);
#ifdef NR_LDPC_PROFILER_DETAIL
        stop_meas(&p_profiler->cn2bnProcBuf);
#endif

#ifdef NR_LDPC_DEBUG_MODE
        nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_BN_PROC, bnProcBuf);
#endif

        // BN Processing
        NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->bnProcPc));

#ifndef UNROLL_BN_PROC_PC
        nrLDPC_bnProcPc(p_lut, bnProcBuf, bnProcBufRes, llrProcBuf, llrRes, Z);
#else
        if (BG==1) {
          switch (R) {
            case 13:
            {
#ifdef __AVX2__
                nrLDPC_bnProcPc_BG1_R13_AVX2(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#else		
                nrLDPC_bnProcPc_BG1_R13_128(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#endif
                break;
            }
            case 23:
            {
#ifdef __AVX2__
                nrLDPC_bnProcPc_BG1_R23_AVX2(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#else		
                nrLDPC_bnProcPc_BG1_R23_128(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#endif
                break;
            }
            case 89:
            {
#ifdef __AVX2__
                nrLDPC_bnProcPc_BG1_R89_AVX2(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#else		
                nrLDPC_bnProcPc_BG1_R89_128(bnProcBuf,bnProcBufRes, llrRes, llrProcBuf, Z);
#endif
                break;
            }
          }
        } else {
          switch (R)
          {
            case 15:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG2_R15_AVX2(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG2_R15_128(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#endif
                break;
            }
            case 13:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG2_R13_AVX2(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG2_R13_128(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#endif
                break;
            }
            case 23:
            {
#ifdef __AVX2__		    
                nrLDPC_bnProcPc_BG2_R23_AVX2(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#else
                nrLDPC_bnProcPc_BG2_R23_128(bnProcBuf,bnProcBufRes,llrRes, llrProcBuf, Z);
#endif
                break;
            }
          }
        }
#endif
        NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->bnProcPc));

#ifdef NR_LDPC_DEBUG_MODE
        nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_LLR_RES, llrRes);
#endif

        NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->bnProc));
#ifndef UNROLL_BN_PROC
        nrLDPC_bnProc(p_lut, bnProcBuf, bnProcBufRes, llrRes, Z);
#else     
        if (BG==1) {
          switch (R) {
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG1_R13_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG1_R13_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG1_R13_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG1_R23_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG1_R23_AVX2(bnProcBuf,bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG1_R23_128(bnProcBuf,bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 89:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG1_R89_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG1_R89_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG1_R89_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
          }
        } else {
          switch (R)
          {
            case 15:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG2_R15_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG2_R15_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG2_R15_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 13:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG2_R13_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG2_R13_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG2_R13_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
            case 23:
            {
                #if defined(__AVX512BW__)
                nrLDPC_bnProc_BG2_R23_AVX512(bnProcBuf, bnProcBufRes,llrRes, Z);
                #elif defined(__AVX2__)
                nrLDPC_bnProc_BG2_R23_AVX2(bnProcBuf, bnProcBufRes,llrRes, Z);
                #else
                nrLDPC_bnProc_BG2_R23_128(bnProcBuf, bnProcBufRes,llrRes, Z);
                #endif
                break;
            }
          }
        }
#endif

        NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->bnProc));

#ifdef NR_LDPC_DEBUG_MODE
        nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_BN_PROC_RES, bnProcBufRes);
#endif

        // BN results to CN processing buffer
        NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->bn2cnProcBuf));
        if (BG == 1)
          nrLDPC_bn2cnProcBuf_BG1(p_lut, bnProcBufRes, cnProcBuf, Z);
        else
          nrLDPC_bn2cnProcBuf_BG2(p_lut, bnProcBufRes, cnProcBuf, Z);
        NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->bn2cnProcBuf));

#ifdef NR_LDPC_DEBUG_MODE
        nrLDPC_debug_writeBuffer2File(nrLDPC_buffers_CN_PROC, cnProcBuf);
#endif

   // Parity Check
        if (!p_decParams->check_crc) {
          NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->cnProcPc));
          if (BG == 1)
            pcRes = nrLDPC_cnProcPc_BG1(p_lut, cnProcBuf, cnProcBufRes, Z);
          else
            pcRes = nrLDPC_cnProcPc_BG2(p_lut, cnProcBuf, cnProcBufRes, Z);
          NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->cnProcPc));
        } else {
          if (numIter > 2) {
            int8_t llrOut[NR_LDPC_MAX_NUM_LLR] __attribute__((aligned(64))) = {0};
            int8_t* p_llrOut = outMode == nrLDPC_outMode_LLRINT8 ? p_out : llrOut;
            nrLDPC_llrRes2llrOut(p_lut, p_llrOut, llrRes, Z, BG);
            if (outMode == nrLDPC_outMode_BIT)
              nrLDPC_llr2bitPacked(p_out, p_llrOut, numLLR);
            else // if (outMode == nrLDPC_outMode_BITINT8)
              nrLDPC_llr2bit(p_out, p_llrOut, numLLR);
            if (p_decParams->check_crc((uint8_t*)p_out, p_decParams->Kprime, p_decParams->crc_type)) {
              LOG_D(PHY, "Segment CRC OK, exiting LDPC decoder\n");
              break;
            }
          }
        }
        // ldpc_pmu_stop_read(pmu_ctx, &pmu_res);
        // ldpc_log_pmu_stats("while_iter", numIter, &pmu_res);
        // stop_meas(&iter_time);
        // LOG_W(PHY,"iter time %.2f\n",get_time_meas_us(&iter_time));
    }
    if (!p_decParams->check_crc) {
      int8_t llrOut[NR_LDPC_MAX_NUM_LLR] __attribute__((aligned(64))) = {0};
      int8_t* p_llrOut = outMode == nrLDPC_outMode_LLRINT8 ? p_out : llrOut;
      // Assign results from processing buffer to output
      NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->llrRes2llrOut));
      nrLDPC_llrRes2llrOut(p_lut, p_llrOut, llrRes, Z, BG);
      NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->llrRes2llrOut));
      // Hard-decision
      NR_LDPC_PROFILER_DETAIL(start_meas(&p_profiler->llr2bit));
      if (outMode == nrLDPC_outMode_BIT)
        nrLDPC_llr2bitPacked(p_out, p_llrOut, numLLR);
      else // if (outMode == nrLDPC_outMode_BITINT8)
        nrLDPC_llr2bit(p_out, p_llrOut, numLLR);
      NR_LDPC_PROFILER_DETAIL(stop_meas(&p_profiler->llr2bit));
    }
    stop_meas(&iter_time);
    double iters_time_us = get_time_meas_us(&iter_time);
    // LOG_W(PHY,"init time %.2f, iter time %.2f, iteration times = %d\n",init_time, get_time_meas_us(&iter_time),numIter - 1);
    LOG_W(PHY,
      "id = %d, init time %.2f, iter time %.2f, iteration times = %d\n",
      id,
      init_time,
      iters_time_us,
      numIter - 1);
    // ldpc_pmu_stop_read(pmu_ctx, &pmu_res);
    // ldpc_log_pmu_stats("decoding codeBlock", numIter, &pmu_res);
    // ldpc_pmu_close(&pmu_ctx);
    // stop_meas(&total_time);
    // LOG_W(PHY,"total time %.2f\n",get_time_meas_us(&total_time));
    return numIter;
}




