/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","load"],
    "RACE_PAIR": ["shmem_int_put@50","LOAD@61"],
    "CONSISTENCY_CALLS": ["shmem_quiet"],
    "SYNC_CALLS": ["shmem_team_sync"],
    "NPROCS": 4,
    "DESCRIPTION": "PE 2 part of the team puts to PE 3 which is *not* part of the team. There is no synchronization between PE 2 and PE3, since they are not in the same team."
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
        if (my_pe == 2) {
            localbuf = 42;
            // CONFLICT
            shmem_int_put(&remote, &localbuf, 1, 3); // P2 puts to P3
        }
        shmem_quiet(); // Synchronisation
    }

    if (SHMEM_TEAM_INVALID != team)
        shmem_team_sync(team); // Synchronisation

    if (SHMEM_TEAM_INVALID == team) {
        if (my_pe == 3)
            // CONFLICT
            printf("PE %d: %d\n", my_pe, remote);
    }

    shmem_barrier_all();

    shmem_barrier_all();
    printf("Process %d: Execution finished, variable contents: remote = %d, localbuf = %d\n", my_pe, remote, localbuf);
    shmem_finalize();

    return 0;
}
