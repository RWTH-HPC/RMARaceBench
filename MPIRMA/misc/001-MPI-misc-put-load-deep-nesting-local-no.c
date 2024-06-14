/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["local buffer read","load"],
    "NPROCS": 2,
    "DESCRIPTION": "Two non-conflicting operations put and load executed concurrently with no race."
}
*/
// RACE LABELS END
// RACE_KIND: none
// ACCESS_SET: [local buffer read,load]

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

__attribute__((noinline)) void deeeeeeeeep(int* buf, MPI_Win win) { MPI_Put(buf, 1, MPI_INT, 1, 0, 1, MPI_INT, win); }

__attribute__((noinline)) void deeeeeeeep(int* buf, MPI_Win win) { deeeeeeeeep(buf, win); }
__attribute__((noinline)) void deeeeeeep(int* buf, MPI_Win win) { deeeeeeeep(buf, win); }
__attribute__((noinline)) void deeeeeep(int* buf, MPI_Win win) { deeeeeeep(buf, win); }
__attribute__((noinline)) void deeeeep(int* buf, MPI_Win win) { deeeeeep(buf, win); }
__attribute__((noinline)) void deeeep(int* buf, MPI_Win win) { deeeeep(buf, win); }
__attribute__((noinline)) void deeep(int* buf, MPI_Win win) { deeeep(buf, win); }
__attribute__((noinline)) void deep(int* buf, MPI_Win win) { deeep(buf, win); }

void rank0(int* buf, MPI_Win win)
{
    deep(buf, win);
    printf("value is %d\n", *buf);
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

    MPI_Win_fence(0, win);

    if (rank == 0) {
        rank0(buf, win);
    }
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
