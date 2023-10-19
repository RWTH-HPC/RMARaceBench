/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["rma write","rma write"],
    "CONSISTENCY_CALLS": ["shmem_quiet"],
    "SYNC_CALLS": ["shmem_barrier_all"],
    "NPROCS": 4,
    "DESCRIPTION": "Two conflicting operations shmem_int_sum_reduce and shmem_int_put synchronized through shmem_barrier_all."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 4

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
    remote = 1;
    static int reduced;

    shmem_barrier_all();

    shmem_int_sum_reduce(SHMEM_TEAM_WORLD, &reduced, &remote, 1); // Potential conflict

    shmem_barrier_all(); // Synchronization

    if (my_pe == 0) {
        int localbuf = 0;
        shmem_int_put(&remote, &localbuf, 1, 1); // Potential conflict
    }

    shmem_barrier_all();

    printf("PE %d: %d\n", my_pe, reduced);

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
