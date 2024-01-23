# RMARaceBench 1.0.2 - [![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
RMARaceBench [[RRB23](#reference)] is a collection of race test cases for MPI RMA, SHMEM, and GASPI to evaluate the classification quality of race detection tools for RMA programs.

Authors: Simon Schwitanski, Sven Klotz, Joachim Jenke, Matthias S. Müller, RWTH Aachen University

## Structure
- `MPIRMA`, `SHMEM`, `GASPI`: Race test cases for the different programming models
- `util`: Utility programs to reproduce the results and generate the tables used the paper
- `Dockerfile`: Docker environment we used to gather the results
- `templates`: Code templates with the necessary boilerplate code

## Results
The results of the experiments presented in the paper are available in a separate repository: https://github.com/RWTH-HPC/RMARaceBench-Results

## Usage
We provide a Dockerfile that provides the required software environment
to reproduce our results. In the following, we assume that `$ROOT` is
the root folder of the supplemental repository / unpacked files. First,
build the Docker image with tag `rmaracebench` and start a shell within
the container:
```
cd $ROOT
docker build . -t rmaracebench
docker run -it rmaracebench bash
```

### Run Tests Without Tool
Within the Docker image, use `run_test.py` to run the plain tests on MPI
RMA, SHMEM, GASPI without any tool and specify an output folder to store
the results:
```
python run_test.py plain -o result_folder
```
The result folder contains the outputs of the different test cases runs for further investigations.

### Run Classification Quality Tests
The same script `run_test.py` can be used to execute the classification
quality tests on MUST-RMA and PARCOACH:

```
python run_test.py tools -o result_folder
```
The result folder contains the outputs of the different tool runs for further investigations. A summary CSV file is also generated that can be used in the
Python script `parse_results.py` to generate the result tables (TP/FP/TN/FN):

```
python parse_results.py result_folder/results.csv
```

## Software Environment
The following software packages are used for the evaluation in the Docker
environment:
-   LLVM / Clang compiler version 15.0.6
-   OpenMPI 4.1.4
-   CMake 3.25.1
-   Python 3
-   PARCOACH 2.3.1
-   MUST-RMA 1.9.0

## Generate Test Cases
The test cases are generated based on Jinja2 templates to avoid writing the same boilerplate code for every test case.
In the Docker environment, run in the `/rmaracebench` folder:

```
python generate.py
```

## Contribution
In case you find a mistake in the test cases or would like to contribute your own benchmarks, we are looking forward to pull requests.

In case you face any problems with the test cases, please use the issue tracker or contact us personally.


## <a name="reference"></a> Reference
[RRB23] Simon Schwitanski, Joachim Jenke, Sven Klotz, and Matthias S. Müller. 2023. [RMARaceBench: A Microbenchmark Suite to Evaluate Race Detection Tools for RMA Programs](https://doi.org/10.1145/3624062.3624087). In Workshops of The International Conference on High Performance Computing, Network, Storage, and Analysis (SC-W 2023), November 12–17, 2023, Denver, CO, USA. ACM, New York, NY, USA.
https://doi.org/10.1145/3624062.3624087