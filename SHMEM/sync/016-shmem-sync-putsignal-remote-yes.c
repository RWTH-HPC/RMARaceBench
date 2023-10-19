/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","local read"],
    "RACE_PAIR": ["LOAD@47","shmem_int_put_signal@57"],
    "CONSISTENCY_CALLS": ["shmem_barrier_all"],
    "SYNC_CALLS": ["shmem_signal_fetch"],
    "NPROCS": 2,
    "DESCRIPTION": "Signalled put where PE 0 polls with plain LOADs on the signal instead of using shmem_signal_fetch."
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
    static uint64_t signal = 0;

    shmem_barrier_all();

    if (my_pe == 0) {
        // CONFLICT
        while (signal < PROC_NUM - 1) {
            continue;
        }

        printf("Remote: %d\n", remote);
    }

    if (my_pe == 1) {
        localbuf = 2;
        // CONFLICT
        shmem_int_put_signal(&remote, &my_pe, 1, &signal, 1, SHMEM_SIGNAL_ADD, 0);
    }
    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
