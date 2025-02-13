/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["local buffer read","store"],
    "NPROCS": 2,
    "CONSISTENCY_CALLS": ["shmem_wait_until"],
    "SYNC_CALLS": ["shmem_put_signal,shmem_wait_until"],
    "DESCRIPTION": "Nonblocking signalled put from PE0 to PE1. The synchronization between PE0 and PE1 ensures that the local buffer access is safe."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>

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

    static uint64_t flag = 0;

    shmem_barrier_all();

    if (my_pe == 0) {
        localbuf = 42;
        // send data with signal (ping)
        shmem_int_put_signal_nbi(&remote, &localbuf, 1, &flag, 1, SHMEM_SIGNAL_SET, 1);
        // wait for pong from PE 1
        shmem_uint64_wait_until(&flag, SHMEM_CMP_EQ, 1);
        localbuf = 1337;
    }

    if (my_pe == 1) {
        localbuf = 1337;
        // wait for ping from PE 0
        shmem_uint64_wait_until(&flag, SHMEM_CMP_EQ, 1);
        // send data with signal (pong)
        shmem_int_put_signal(&remote, &localbuf, 1, &flag, 1, SHMEM_SIGNAL_SET, 0);
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
