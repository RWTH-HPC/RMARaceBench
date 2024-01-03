/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","rma write"],
    "RACE_PAIR": ["shmem_int_put@53","shmem_int_put@63"],
    "NPROCS": 2,
    "CONSISTENCY_CALLS": ["shmem_set_lock,shmem_clear_lock"],
    "SYNC_CALLS": ["shmem_set_lock,shmem_clear_lock,shmem_barrier_all"],
    "DESCRIPTION": "Two conflicting operations put and put, where only the first access is correcly ordered by a lock."
}
*/
// RACE LABELS END

#include <unistd.h>

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
    static long lock;

    shmem_barrier_all();

    if (my_pe == 0) {
        // make it probable that PE 1 locks first to make race observable
        sleep(1);
        localbuf = 42;
        shmem_set_lock(&lock);
        // CONFLICT
        shmem_int_put(&remote, &localbuf, 1, 1);
        shmem_clear_lock(&lock);
    }

    if (my_pe == 1) {
        shmem_set_lock(&lock);
        shmem_clear_lock(&lock);

        localbuf = 1337;
        // CONFLICT
        shmem_int_put(&remote, &localbuf, 1, 1);
    }

    shmem_barrier_all();

    printf("PE %d: localbuf = %d, remote = %d, \n", my_pe, localbuf, remote);

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
