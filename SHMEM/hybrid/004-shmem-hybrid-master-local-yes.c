/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "local",
    "ACCESS_SET": ["rma read","load"],
    "RACE_PAIR": ["shmem_get_nbi@48","LOAD@53"],
    "CONSISTENCY_CALLS": ["shmem_quiet"],
    "SYNC_CALLS": ["shmem_sync_all"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations shmem_get_nbi and a local load with missing synchronization at process 0. Since the main thread of the target synchronizes with the origin, the access of the non-master thread leads to a local buffer race."
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

    if (my_pe == 0) {
#pragma omp parallel num_threads(2)
        {
#pragma omp master
            {
                // CONFLICT
                shmem_get_nbi(&localbuf, &remote, 1, 1);
                shmem_quiet();
            }

            // CONFLICT
            printf("localbuf is %d\n", localbuf);
        }
        shmem_sync_all();
    }

    if (my_pe == 1) {
        shmem_sync_all();
        printf("remote is %d\n", remote);
    }

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
