/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["rma atomic write","rma atomic read"],
    "NPROCS": 3,
    "DESCRIPTION": "Two non-conflicting operations atomicset and atomicfetch executed concurrently with no race."
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
    shmem_barrier_all();

    if (my_pe == 0) {
        shmem_int_atomic_set(&remote, 1, 1);
    }

    if (my_pe == 2) {
        localbuf = 2;

        localbuf = shmem_int_atomic_fetch(&remote, 1);
    }

    shmem_barrier_all();

    printf("PE %d: localbuf = %d, remote = %d, \n", my_pe, localbuf, remote);

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
