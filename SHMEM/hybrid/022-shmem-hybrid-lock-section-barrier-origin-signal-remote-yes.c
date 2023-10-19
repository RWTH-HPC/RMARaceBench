/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","load"],
    "RACE_PAIR": ["shmem_put@52","LOAD@68"],
    "CONSISTENCY_CALLS": ["shmem_quiet"],
    "SYNC_CALLS": ["MPI_Barrier"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations shmem_put and a local load with missing synchronization, because only the other thread at the origin synchronizes with the target."
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
    shmem_barrier_all();

    if (my_pe == 0) {
#pragma omp parallel num_threads(2)
        {
#pragma omp sections
            {
#pragma omp section
                {
                    int value = 42;
                    // CONFLICT
                    shmem_int_put(&remote, &value, 1, 1); // Put on remote at process 1
                    shmem_fence();
                }

#pragma omp section
                {
                    sleep(1); // force that shmem_put goes through first
                    shmem_atomic_set(&remote2, 1, 1);
                }
            }
        }
    }

    if (my_pe == 1) {
        shmem_wait_until(&remote2, SHMEM_CMP_EQ, 1);
        // CONFLICT
        printf("remote is %d\n", remote);
    }

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
