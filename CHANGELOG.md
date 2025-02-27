# Changelog

## 1.2.0 - (2025-02-25)

* Add `misc` tests also for SHMEM and GASPI
* Add test cases for local completion via notifications
* `misc` tests: Revert buf usage to &value usage and use manual replacements in misc category to make alias tests work
* `misc` tests: Remove the number of redundant tests
* `misc` tests: Rearrange order of tests
* Fix shared memory data races in GASPI hybrid test cases (OpenMP master, single)
* SHMEM: Remove obsolete variables
* SHMEM: Remove unnecessary barrier in misc testcases
* MPI RMA: Ensure that MPI groups in PSCW are freed to avoid resource leak
* GASPI: Use MPI_Init_thread in hybrid test cases
* Update jinja2 dependency


## 1.1.0 - (2024-06-14)

* Add new category 'misc' that adds test cases challenging for static tools
  * Aliasing between buffers introduced in a function (interprocedural analysis required for detection)
  * Deeply nested function calls (buffers still have to be attributed correctly by an analysis within the deeply nested function)
  * Function pointers (difficult to determine statically which function is called)
  * External function calls that generate aliases (here: memcpy)
  * The 'misc' tests are currently only generated for MPI RMA.
* Use pointer variable in MPI RMA test case template (required for some 'misc' test cases)

## 1.0.3 - (2024-06-12)

* Add missing `unistd` header for sleep functions
* MPI RMA: Fix wrong race categorization of MPI-atomic-disp-remote-no (was "yes", but should be "no")
* SHMEM: Avoid conflicting signal address use, fix wrong type of signal address
* SHMEM lock test: Add sleep to make race observable (locking order)
* GASPI: Fix missing / wrong synchronization in some GASPI test cases
* GASPI: Fix wrong name of some conflict test cases (name contained "load" instead of "store")
* GASPI: Remove unnecessary declearations in GASPI tests cases
* GASPI: Fix remote race in GASPI conflict test case
* GASPI: Fix wrong race lines for GASPI list access calls
* Update jinja2 dependency

## 1.0.2 - (2024-01-23)

* Update jinja2 dependency

## 1.0.1 - (2023-12-13)

* Fix wrong `MPI_Compare_and_swap` and `MPI_Fetch_and_op` test cases which had a wrong target displacement of 1 and change it to 0.
* Fix wrong race locations of `MPI_Compare_and_wrap` test cases.
* Fix wrong target PE in some SHMEM test cases

## 1.0.0 - (2023-10-19)

* Initial version
