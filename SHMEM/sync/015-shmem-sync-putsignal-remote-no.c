/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["rma write","local read"],
    "CONSISTENCY_CALLS": ["shmem_barrier_all"],
    "SYNC_CALLS": ["shmem_signal_fetch"],
    "NPROCS": 2,
    "DESCRIPTION": "Signalled put where PE 0 polls on the signal of PE1."
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
    static int data[PROC_NUM];
    static uint64_t signal = 0;

    shmem_barrier_all();

    if (my_pe == 0) {
        while (shmem_signal_fetch(&signal) != 1) // POLLING
        {
            continue;
        }

        printf("Data on PE 0:");
        for (int i = 0; i < PROC_NUM; ++i) {
            printf(" %d", data[i]); // Potential conflict
        }
        printf("\n");
    }

    if (my_pe == 1) {
        shmem_int_put_signal(&data[my_pe], &my_pe, 1, &signal, 1, SHMEM_SIGNAL_ADD,
                             0); // Potential conflict
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
