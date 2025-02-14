/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["local buffer read","load"],
    "NPROCS": 2,
    "DESCRIPTION": "Two non-conflicting operations putnbi and load executed concurrently with no race."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>

__attribute__((noinline)) void deeeeeeeeep(int* rem_ptr, int* lbuf_ptr) { shmem_int_put_nbi(rem_ptr, lbuf_ptr, 1, 1); }

__attribute__((noinline)) void deeeeeeeep(int* rem_ptr, int* lbuf_ptr) { deeeeeeeeep(rem_ptr, lbuf_ptr); }
__attribute__((noinline)) void deeeeeeep(int* rem_ptr, int* lbuf_ptr) { deeeeeeeep(rem_ptr, lbuf_ptr); }
__attribute__((noinline)) void deeeeeep(int* rem_ptr, int* lbuf_ptr) { deeeeeeep(rem_ptr, lbuf_ptr); }
__attribute__((noinline)) void deeeeep(int* rem_ptr, int* lbuf_ptr) { deeeeeep(rem_ptr, lbuf_ptr); }
__attribute__((noinline)) void deeeep(int* rem_ptr, int* lbuf_ptr) { deeeeep(rem_ptr, lbuf_ptr); }
__attribute__((noinline)) void deeep(int* rem_ptr, int* lbuf_ptr) { deeeep(rem_ptr, lbuf_ptr); }
__attribute__((noinline)) void deep(int* rem_ptr, int* lbuf_ptr) { deeep(rem_ptr, lbuf_ptr); }

void rank0(int* rem_ptr, int* lbuf_ptr)
{
    deep(rem_ptr, lbuf_ptr);
    printf("*lbuf_ptr is %d\n", *lbuf_ptr);
}

#define PROC_NUM 2

int main(int argc, char** argv)
{
    static int remote = 0;
    int localbuf = 1;

    shmem_init();

    int num_pe = shmem_n_pes();
    int my_pe = shmem_my_pe();

    if (num_pe != PROC_NUM) {
        printf("Got %d PEs, expected %d\n", num_pe, PROC_NUM);
        shmem_global_exit(1);
    }
    int* rem_ptr = &remote;
    int* lbuf_ptr = &localbuf;

    shmem_barrier_all();

    if (my_pe == 0) {
        rank0(rem_ptr, lbuf_ptr);
    }

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
