/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "local",
    "ACCESS_SET": ["local buffer read","local buffer write"],
    "RACE_PAIR": ["MPI_Put@56","MPI_Get@59"],
    "NPROCS": 2,
    "CONSISTENCY_CALLS": ["MPI_Win_lock,MPI_Win_unlock,MPI_Win_flush_local"],
    "SYNC_CALLS": ["MPI_Barrier"],
    "DESCRIPTION": "Two conflicting operations put and get issued from the same origin where MPI_Win_flush_local is not enough to ensure consistency."
}
*/
// RACE LABELS END

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 2
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

    MPI_Barrier(MPI_COMM_WORLD);

    if (rank == 0) {
        value = 1;
        MPI_Win_lock(MPI_LOCK_SHARED, 1, 0, win);
        // CONFLICT
        MPI_Put(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win);
        MPI_Win_flush_local(1, win);
        // CONFLICT
        MPI_Get(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win);
        MPI_Win_unlock(1, win); // consistent
    }

    MPI_Barrier(MPI_COMM_WORLD); // synchronized

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
