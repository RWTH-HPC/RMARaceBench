/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma atomic write","rma atomic write"],
    "RACE_PAIR": ["MPI_Accumulate@56","MPI_Accumulate@62"],
    "NPROCS": 3,
    "CONSISTENCY_CALLS": ["MPI_Win_fence"],
    "SYNC_CALLS": ["MPI_Barrier", "MPI_Win_fence"],
    "DESCRIPTION": "Two atomic operations acc and acc using different datatypes (float and int) such that there are no atomicity guarantees."
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

    MPI_Barrier(MPI_COMM_WORLD);

    MPI_Win_fence(0, win);
    if (rank == 0) {
        float value1[4] = {1.0, 1.0, 1.0, 1.0};
        // CONFLICT
        MPI_Accumulate(value1, 4, MPI_FLOAT, 1, 0, 4, MPI_FLOAT, MPI_SUM, win);
    }

    if (rank == 2) {
        int value2[4] = {1, 2, 3, 4};
        // CONFLICT
        MPI_Accumulate(value2, 4, MPI_INT, 1, 0, 4, MPI_INT, MPI_SUM, win);
    }

    MPI_Win_fence(0, win);

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
