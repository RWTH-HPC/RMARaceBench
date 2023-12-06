/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["rma write","rma write"],
    "CONSISTENCY_CALLS": ["shmem_ctx_quiet"],
    "SYNC_CALLS": ["shmem_barrier_all"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting shmem_ctx_put operations with shmem_ctx_quiet called on the correct context."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 2

int main(int argc, char** argv)
{
    static int remote = 0;
    static int remote2 = 0;
    int localbuf = 1;

    shmem_init();

    int num_pe = shmem_n_pes();
    int my_pe = shmem_my_pe();

    if (num_pe != PROC_NUM) {
        printf("Got %d PEs, expected %d\n", num_pe, PROC_NUM);
        shmem_global_exit(1);
    }
    shmem_ctx_t ctx;

    shmem_ctx_create(0, &ctx);

    shmem_barrier_all();

    if (my_pe == 0) {
        localbuf = 42;
        // CONFLICT
        shmem_ctx_int_put(ctx, &remote, &localbuf, 1, 1);
        shmem_ctx_quiet(ctx);
        localbuf = 1337;
        // CONFLICT
        shmem_ctx_int_put(ctx, &remote, &localbuf, 1, 1);
    }

    shmem_barrier_all();

    printf("PE %d: %d\n", my_pe, remote);

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
