
/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma atomic write","rma atomic write"],
    "RACE_PAIR": ["shmem_ctx_int_atomic_add@49","shmem_ctx_int_atomic_add@54"],
    "CONSISTENCY_CALLS": ["shmem_barrier_all"],
    "SYNC_CALLS": ["shmem_barrier_all"],
    "NPROCS": 3,
    "DESCRIPTION": "Two concurrent conflicting atomic operations used on different context in different atomicity domains, no atomicity guarantees."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 3

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
    shmem_ctx_t ctx_world;
    shmem_ctx_t ctx_shared;
    shmem_team_create_ctx(SHMEM_TEAM_WORLD, 0, &ctx_world);
    shmem_team_create_ctx(SHMEM_TEAM_SHARED, 0, &ctx_shared);

    if (my_pe == 0) {
        // CONFLICT
        shmem_ctx_int_atomic_add(ctx_world, &remote, 1, 1);
    }

    if (my_pe == 2) {
        // CONFLICT
        shmem_ctx_int_atomic_add(
            ctx_shared,
            &remote,
            1,
            shmem_team_translate_pe(SHMEM_TEAM_WORLD, 1, SHMEM_TEAM_SHARED));
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
