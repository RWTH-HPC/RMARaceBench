/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","load"],
    "RACE_PAIR": ["shmem_int_put@49","LOAD@60"],
    "NPROCS": 2,
    "CONSISTENCY_CALLS": ["shmem_fence"],
    "SYNC_CALLS": ["shmem_atomic_set,shmem_wait_until"],
    "DESCRIPTION": "Two conflicting operations put and load, where the load is executed before the wait_until."
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

    static int flag = 0;

    shmem_barrier_all();

    if (my_pe == 0) {
        int myval = 42;
        // CONFLICT
        shmem_int_put(&remote, &myval, 1, 1);

        shmem_fence();

        shmem_int_atomic_set(&flag, 1, 1);
    }

    shmem_quiet();

    if (my_pe == 1) {
        // CONFLICT
        printf("remote is %d", remote);
        shmem_int_wait_until(&flag, SHMEM_CMP_EQ, 1);
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
