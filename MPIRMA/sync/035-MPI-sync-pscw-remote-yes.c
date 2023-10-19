/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","rma read"],
    "RACE_PAIR": ["MPI_Put@67","MPI_Get@76"],
    "NPROCS": 3,
    "CONSISTENCY_CALLS": ["MPI_Win_start,MPI_Win_complete,MPI_Win_post,MPI_Win_wait"],
    "SYNC_CALLS": ["MPI_Win_start,MPI_Win_complete,MPI_Win_post,MPI_Win_wait"],
    "DESCRIPTION": "Two conflicting operations put and get which are not synchronized correcly in PSCW mode leading to a remote race."
}
*/
// RACE LABELS END

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 3
#define WIN_SIZE 10

int main(int argc, char** argv)
{
    int rank, size;
    MPI_Win win;
    int* win_base;
    int value = 1, value2 = 2;
    int result;
    int token = 42;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size != PROC_NUM) {
        printf("Wrong number of MPI processes: %d. Expected: %d\n", size, PROC_NUM);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    MPI_Win_allocate(WIN_SIZE * sizeof(int), sizeof(int), MPI_INFO_NULL, MPI_COMM_WORLD, &win_base, &win);
    for (int i = 0; i < WIN_SIZE; i++) {
        win_base[i] = 0;
    }
    int send_buf, recv_buf;
    MPI_Status status;
    MPI_Request request;
    MPI_Info info;

    MPI_Group world_group;
    MPI_Comm_group(MPI_COMM_WORLD, &world_group);

    MPI_Barrier(MPI_COMM_WORLD);

    if (rank == 0) {
        int destrank = 2;
        MPI_Group destgroup;
        MPI_Group_incl(world_group, 1, &destrank, &destgroup);

        MPI_Win_start(destgroup, 0, win);
        int value = 42;
        // CONFLICT
        MPI_Put(&value, 1, MPI_INT, 2, 0, 1, MPI_INT, win);
        MPI_Win_complete(win);
    } else if (rank == 1) {
        int destrank = 2;
        MPI_Group destgroup;
        MPI_Group_incl(world_group, 1, &destrank, &destgroup);
        MPI_Win_start(destgroup, 0, win);
        int value;
        // CONFLICT
        MPI_Get(&value, 1, MPI_INT, 2, 0, 1, MPI_INT, win);
        MPI_Win_complete(win);

    } else if (rank == 2) {
        const int srcrank[2] = {0, 1};
        MPI_Group srcgroup;
        MPI_Group_incl(world_group, 2, &srcrank[0], &srcgroup);

        MPI_Win_post(srcgroup, 0, win);
        MPI_Win_wait(win);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    printf(
        "Process %d: Execution finished, variable contents: value = %d, value2 = %d, win_base[0] = %d\n",
        rank,
        value,
        value2,
        win_base[0]);

    MPI_Win_free(&win);
    MPI_Finalize();

    return 0;
}
