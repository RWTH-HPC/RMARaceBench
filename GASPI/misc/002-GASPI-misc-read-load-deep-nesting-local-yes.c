/* Part of RMARaceBench, under BSD-3-Clause License
 * See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
 * SPDX-License-Identifier: BSD-3-Clause
 */

// RACE LABELS BEGIN
/*
{
    "RACE_KIND": "local",
    "ACCESS_SET": ["local buffer write","load"],
    "RACE_PAIR": ["gaspi_read@27","LOAD@47"],
    "NPROCS": 2,
    "DESCRIPTION": "Two conflicting operations read and load executed concurrently which leads to a race."
}
*/
// RACE LABELS END

#include <GASPI.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

__attribute__((noinline)) void deeeeeeeeep(int* localbuf)
{
    /* conflicting read and load */
    // CONFLICT
    printf("localbuf[0] is %d\n", localbuf[0]);
}

__attribute__((noinline)) void deeeeeeeep(int* localbuf) { deeeeeeeeep(localbuf); }
__attribute__((noinline)) void deeeeeeep(int* localbuf) { deeeeeeeep(localbuf); }
__attribute__((noinline)) void deeeeeep(int* localbuf) { deeeeeeep(localbuf); }
__attribute__((noinline)) void deeeeep(int* localbuf) { deeeeeep(localbuf); }
__attribute__((noinline)) void deeeep(int* localbuf) { deeeeep(localbuf); }
__attribute__((noinline)) void deeep(int* localbuf) { deeeep(localbuf); }
__attribute__((noinline)) void deep(int* localbuf) { deeep(localbuf); }

void rank0(
    gaspi_segment_id_t loc_seg_id,
    gaspi_segment_id_t remote_seg_id,
    gaspi_queue_id_t queue_id,
    int* localbuf,
    int* remote_data)
{
    deep(localbuf);
    // CONFLICT
    gaspi_read(loc_seg_id, 0, 1, remote_seg_id, 0, sizeof(int), queue_id, GASPI_BLOCK);
}

#define PROC_NUM 2

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

    if (rank == 0) {
        rank0(loc_seg_id, remote_seg_id, queue_id, localbuf, remote_data);
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
