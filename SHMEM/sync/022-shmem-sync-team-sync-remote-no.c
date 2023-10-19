/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["rma write","load"],
    "CONSISTENCY_CALLS": ["shmem_quiet"],
    "SYNC_CALLS": ["shmem_team_sync"],
    "NPROCS": 4,
    "DESCRIPTION": "PE 0 is part of the team and puts to PE 2 which is also part of the team. There is synchronization between PE 0 and PE 2, since they are in the same team."
}
*/
// RACE LABELS END

#include <shmem.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 4

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
    shmem_team_t team = SHMEM_TEAM_INVALID;
    shmem_team_split_strided(SHMEM_TEAM_WORLD, 0, 2, num_pe / 2, NULL, 0lu, &team);

    shmem_barrier_all();

    if (SHMEM_TEAM_INVALID != team) {
        if (my_pe == 0) {
            localbuf = 42;
            shmem_int_put(&remote, &localbuf, 1, 2); // PE 0 puts to PE 2
        }
        shmem_quiet(); // Synchronisation
    }

    if (SHMEM_TEAM_INVALID != team)
        shmem_team_sync(team); // Synchronisation

    if (SHMEM_TEAM_INVALID != team) {
        if (my_pe == 2)
            printf("PE %d: %d\n", my_pe, remote);
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
