/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma read","rma write"],
    "RACE_PAIR": ["shmem_int_get@46","shmem_int_put@52"],
    "NPROCS": 2,
    "CONSISTENCY_CALLS": ["shmem_fence"],
    "SYNC_CALLS": ["shmem_barrier_all"],
    "DESCRIPTION": "Two conflicting operations get_nbi and put that are not ordered via shmem_fence."
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
        // CONFLICT
        shmem_int_get_nbi(&localbuf, &remote, 1, 1);

        shmem_fence(); // Doesn't order "RMA loads" (e.g. non-blocking get or atomic fetch)

        int localbuf2 = 42;
        // CONFLICT
        shmem_int_put(&remote, &localbuf2, 1, 1);
    }

    shmem_barrier_all();

    printf("PE %d: localbuf = %d, remote = %d, \n", my_pe, localbuf, remote);

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
