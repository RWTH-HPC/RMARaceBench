/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "none",
    "ACCESS_SET": ["rma atomic write","rma atomic write"],
    "CONSISTENCY_CALLS": [""],
    "SYNC_CALLS": ["gaspi_barrier"],
    "NPROCS": 3,
    "DESCRIPTION": "Two conflicting operations gaspi_write and a local load with correct synchronization."
}
*/
// RACE LABELS END

#include <GASPI.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 3

int main(int argc, char* argv[])
{
    MPI_Init(&argc, &argv);
    gaspi_proc_init(GASPI_BLOCK);

    gaspi_rank_t rank;
    gaspi_rank_t num;

    gaspi_proc_rank(&rank);
    gaspi_proc_num(&num);

    if (num != PROC_NUM) {
        printf("Wrong number of processes: %d. Expected: %d\n", num, PROC_NUM);
        gaspi_proc_term(GASPI_BLOCK);
    }

    const gaspi_segment_id_t loc_seg_id = 0;
    const gaspi_segment_id_t remote_seg_id = 1;
    const gaspi_queue_id_t queue_id = 0;
    gaspi_size_t const seg_size = 10 * sizeof(int);

    // local segment (for local buffers)
    gaspi_segment_alloc(loc_seg_id, seg_size, GASPI_ALLOC_DEFAULT);
    // remote segment (for one-sided accesses)
    gaspi_segment_create(remote_seg_id, seg_size, GASPI_GROUP_ALL, GASPI_BLOCK, GASPI_ALLOC_DEFAULT);

    gaspi_pointer_t src_segment_data;
    gaspi_pointer_t dst_segment_data;
    gaspi_segment_ptr(loc_seg_id, &src_segment_data);
    gaspi_segment_ptr(remote_seg_id, &dst_segment_data);
    int* localbuf = (int*)src_segment_data;
    int* remote_data = (int*)dst_segment_data;

    gaspi_barrier(GASPI_GROUP_ALL, GASPI_BLOCK);
    gaspi_atomic_value_t old;

    if (rank == 0) {
        // CONFLICT
        gaspi_atomic_fetch_add(remote_seg_id, 0, 1, 1, &old, GASPI_BLOCK);
        printf("rank 0 old value = %lu\n", old);
    }

    if (rank == 2) {
        // CONFLICT
        gaspi_atomic_fetch_add(remote_seg_id, 0, 1, 1, &old, GASPI_BLOCK);
        printf("rank 2 old value = %lu\n", old);
    }

    gaspi_barrier(GASPI_GROUP_ALL, GASPI_BLOCK);

    if (rank == 1) {
        printf("rank 1 value = %lu\n", ((gaspi_atomic_value_t*)remote_data)[0]);
    }

    gaspi_barrier(GASPI_GROUP_ALL, GASPI_BLOCK);
    printf(
        "Process %d: Execution finished, variable contents: localbuf[0] = %d, remote_data[0] = %d\n",
        rank,
        localbuf[0],
        remote_data[0]);
    gaspi_proc_term(GASPI_BLOCK);

    MPI_Finalize();

    return EXIT_SUCCESS;
}

// CHECK-NOT: data race
