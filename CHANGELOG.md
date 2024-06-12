# Changelog

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
