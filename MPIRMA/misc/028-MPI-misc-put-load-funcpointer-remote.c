/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma write","load"],
    "RACE_PAIR": ["MPI_Put@29","LOAD@35"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations put and load executed concurrently which leads to a race."
}
*/
// RACE LABELS END
// RACE_KIND: remote
// ACCESS_SET: [rma write,load]
// RACE_PAIR: [MPI_Put@29,LOAD@35]

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

void rank0(int* buf, MPI_Win win, int* win_base)
{
    /* conflicting put and load */
    // CONFLICT
    MPI_Put(buf, 1, MPI_INT, 1, 0, 1, MPI_INT, win);
}

void rank1(int* buf, MPI_Win win, int* win_base)
{
    // CONFLICT
    printf("win_base[0] is %d\n", win_base[0]);
}

#define PROC_NUM 2
#define WIN_SIZE 10

int main(int argc, char** argv)
{
    int rank, size;
    MPI_Win win;
    int* win_base;
    int value = 1, value2 = 2;
    int* buf = &value;
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

    void (*rankfunc)(int* buf, MPI_Win win, int* win_base);

    MPI_Win_fence(0, win);

    if (rank == 0) {
        rankfunc = rank0;
    } else {
        rankfunc = rank1;
    }
    (*rankfunc)(buf, win, win_base);

    MPI_Win_fence(0, win);

    MPI_Barrier(MPI_COMM_WORLD);
    printf(
        "Process %d: Execution finished, variable contents: value = %d, value2 = %d, win_base[0] = %d\n",
        rank,
        *buf,
        value2,
        win_base[0]);

    MPI_Win_free(&win);
    MPI_Finalize();

    return 0;
}
