/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","load"],
    "RACE_PAIR": ["MPI_Put@66","LOAD@86"],
    "CONSISTENCY_CALLS": ["MPI_Win_lock","MPI_Win_unlock"],
    "SYNC_CALLS": ["MPI_Barrier"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations MPI_Get and a local load with missing synchronization, because only the other thread at the origin synchronizes with the target."
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

    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_MULTIPLE, &provided);
    if (provided < MPI_THREAD_MULTIPLE) {
        printf("MPI_THREAD_MULTIPLE not supported\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
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
#pragma omp parallel num_threads(2)
        {
#pragma omp sections
            {
#pragma omp section
                {
                    int value = 42;
                    MPI_Win_lock(MPI_LOCK_EXCLUSIVE, 1, 0, win);
                    // CONFLICT
                    MPI_Put(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win); // Put on win_base[0] at process 1
                    MPI_Win_unlock(1, win);
                }

#pragma omp section
                {
                    sleep(1); // force that MPI_Put goes through first
                    int dummy = 1;
                    MPI_Send(&dummy, 1, MPI_INT, 1, 1, MPI_COMM_WORLD);
                }
            }
        }
    }

    if (rank == 1) {
        {
            int dummy;
            MPI_Recv(&dummy, 1, MPI_INT, 0, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
        // CONFLICT
        printf("win_base[0] is %d\n", win_base[0]);
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
