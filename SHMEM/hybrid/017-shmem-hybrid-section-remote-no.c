/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "CONSISTENCY_CALLS": ["shmem_quiet"],
    "SYNC_CALLS": ["shmem_sync_all"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations shmem_put_nbi and a local load at process 1. Since the setions are in seperate constructs they are not run in parallel and therefore all threads of the processes synchronize using the barrier."
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
    int localbuf = 1;

    shmem_init();

    int num_pe = shmem_n_pes();
    int my_pe = shmem_my_pe();

    if (num_pe != PROC_NUM) {
        printf("Got %d PEs, expected %d\n", num_pe, PROC_NUM);
        shmem_global_exit(1);
    }

    if (my_pe == 0) {
        shmem_put_nbi(&remote, &localbuf, 1, 1);
        shmem_quiet();
        shmem_sync_all();
    }

    if (my_pe == 1) {
#pragma omp parallel num_threads(2)
        {
#pragma omp sections
            {
#pragma omp section
                shmem_sync_all();
            }

#pragma omp sections
            {
#pragma omp section
                printf("remote is %d\n", remote);
            }
        }
    }

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
