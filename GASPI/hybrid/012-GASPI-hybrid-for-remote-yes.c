/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "remote",
    "ACCESS_SET": ["rma read","load"],
    "RACE_PAIR": ["gaspi_read@69","STORE@83"],
    "CONSISTENCY_CALLS": ["gaspi_wait"],
    "SYNC_CALLS": ["gaspi_barrier"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations gaspi_read and a local store with missing synchronization at process 1. Since the iterations of the loop can be scheduled arbitrarily, the local store and MPI_Barrier are concurrent, resulting in a remote race."
}
*/
// RACE LABELS END

#include <GASPI.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define PROC_NUM 2

int main(int argc, char* argv[])
{
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_MULTIPLE, &provided);
    if (provided < MPI_THREAD_MULTIPLE) {
        printf("MPI_THREAD_MULTIPLE not supported\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
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

    if (rank == 0) {
        // CONFLICT
        gaspi_read(loc_seg_id, 0, 1, remote_seg_id, 0, sizeof(int), queue_id, GASPI_BLOCK);
        gaspi_wait(queue_id, GASPI_BLOCK);
        gaspi_barrier(GASPI_GROUP_ALL, GASPI_BLOCK);
    }

    if (rank == 1) {
#pragma omp parallel num_threads(2)
        {
#pragma omp for schedule(static, 1)
            for (int i = 0; i < 2; ++i) {
                if (i == 0) {
                    gaspi_barrier(GASPI_GROUP_ALL, GASPI_BLOCK);
                } else {
                    // CONFLICT
                    remote_data[0] = 42;
                }
            }
        }
    }

    gaspi_wait(queue_id, GASPI_BLOCK);
    gaspi_barrier(GASPI_GROUP_ALL, GASPI_BLOCK);

    // ensure synchronization between all ranks by using notifications
    // to avoid race with printf statement (gaspi_wait + gaspi_barrier
    // is not enough in some cases), both ranks send a notification to
    // the other rank and wait for the notification from the other rank.
    for (int i = 0; i < num; i++) {
        gaspi_notify(remote_seg_id, i, rank, 1, queue_id, GASPI_BLOCK);
    }
    for (int i = 0; i < num; i++) {
        gaspi_notification_id_t firstId;
        gaspi_notify_waitsome(remote_seg_id, i, 1, &firstId, GASPI_BLOCK);
    }

    printf(
        "Process %d: Execution finished, variable contents: localbuf[0] = %d, remote_data[0] = %d\n",
        rank,
        localbuf[0],
        remote_data[0]);
    gaspi_proc_term(GASPI_BLOCK);

    MPI_Finalize();

    return EXIT_SUCCESS;
}
