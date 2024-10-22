/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma read","store"],
    "RACE_PAIR": ["shmem_int_get@52","STORE@55"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations get and store executed concurrently which leads to a race."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>
#include <string.h>

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

    shmem_barrier_all();

    int* rem_ptr = &remote;
    int* lbuf_ptr = &localbuf;
    int* rem_ptr_alias;
    int* lbuf_ptr_alias;

    memcpy(&rem_ptr_alias, &rem_ptr, sizeof(int*));
    memcpy(&lbuf_ptr_alias, &lbuf_ptr, sizeof(int*));

    if (my_pe == 0) {
        /* conflicting get and store */
        // CONFLICT
        shmem_int_get(lbuf_ptr, rem_ptr, 1, 1);
    } else {
        // CONFLICT
        *rem_ptr_alias = 42;
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
