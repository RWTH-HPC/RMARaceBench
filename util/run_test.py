# Part of RMARaceBench, under BSD-3-Clause License
# See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
# SPDX-License-Identifier: BSD-3-Clause

from enum import Enum
import subprocess
from abc import ABC, abstractmethod
import json
import multiprocessing as mp
import os
import pandas
import pathlib
from datetime import datetime
from glob import glob
import argparse
import shutil

defaultdisciplines = ['conflict', 'sync', 'atomic', 'hybrid']
defaulttools = ['MUST', 'PARCOACH-dynamic', 'PARCOACH-static']
defaultrmamodels = ['MPIRMA', 'SHMEM', 'GASPI']


parser = argparse.ArgumentParser(prog="RMARaceBench Runner",
                                 description="Runs the tests of RMARaceBench and classifies the results")
parser.add_argument('mode', choices=['plain', 'tools'], help='Run plain tests (MPI RMA, OpenSHMEM, GASPI) (choice: plain) or the tools on the MPI RMA test cases (choice: tools)', type=str)
parser.add_argument('--tool', dest='tools', default=defaulttools, help='Select tools that should be tested (space-separated, default: all tools)', choices=['MUST', 'PARCOACH-dynamic', 'PARCOACH-static'], nargs='+', type=str)
parser.add_argument('--discipline', dest='disciplines', default=defaultdisciplines, help='Select tool(s) that should be tested (space-separated, default: all disciplines)', choices=['conflict', 'sync', 'atomic', 'hybrid', 'misc'], nargs='+', type=str)
parser.add_argument('--rma-model', dest='rma_models', default=defaultrmamodels, help='Select RMA model(s) that should be tested (space-separated, default: all models)', choices=['MPIRMA', 'SHMEM', 'GASPI'], nargs='+', type=str)
parser.add_argument('-o', '--output-folder', dest='output_folder', default='results-' + datetime.now().strftime("%Y%m%d-%H%M%S"), help='Set output folder, default is results-Ymd-HMS')

class Result(str, Enum):
    TP = 'TP',
    FP = 'FP',
    TN = 'TN',
    FN = 'FN',
    TO = 'TO',
    CR = 'CR',
    NOSUPPORT = '-'

    def __str__(self) -> str:
        return self.value
    
class RunResult(str, Enum):
    SUCCESS = 'SUCCESS'
    TIMEOUT = 'TIMEOUT',
    CRASH = 'CRASH'

    def __str__(self) -> str:
        return self.value


class Test:
    def __init__(self, filename):
        self.filename = filename
        self.basename = os.path.basename(filename)
        with open(self.filename, 'r') as f:
            # read out JSON from test case
            json_string = f.read().split('// RACE LABELS BEGIN\n/*')[1] \
                                  .split('*/\n// RACE LABELS END')[0].strip()
            
            metadata = json.loads(json_string, strict=False)
            self.race_kind = metadata["RACE_KIND"]
            self.has_race = False if self.race_kind == 'none' else True
            if self.has_race:
                self.access_set = metadata["ACCESS_SET"]
                self.race_pair = metadata["RACE_PAIR"]
                self.race_loc1 = int(metadata["RACE_PAIR"][0].split('@')[1])
                self.race_loc2 = int(metadata["RACE_PAIR"][1].split('@')[1])
            self.description = metadata["DESCRIPTION"]
            self.nprocs = metadata["NPROCS"]


class RunTest(ABC):
    def __init__(self, test: Test, out_folder: str):
        self.test = test
        self.out_folder = out_folder
        pathlib.Path(self.out_folder).mkdir(parents=True, exist_ok=True)
        # copy source file to output folder
        self.source_file = os.path.join(self.out_folder, self.test.basename)
        shutil.copy(self.test.filename, self.source_file)
        self.cmd_out = open(os.path.join(self.out_folder, self.test.basename+'.cmd'), 'w')
        self.stdout  = open(os.path.join(self.out_folder, self.test.basename+'.stdout'), 'w')

    def __del__(self):
        self.cmd_out.close()
        self.stdout.close()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def parse(self):
        pass


    def write_stdout(self, stdout: str):
        self.stdout.write(self.output)

    def run_command(self, command: str, timeout = 30):
        result = RunResult.SUCCESS
        self.cmd_out.write(command + '\n')
        p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=timeout)
        except:
            result = RunResult.TIMEOUT
            p.kill()
            return ('', result)

        out, _ = p.communicate()
        if p.returncode != 0:
            print("ERROR WHEN RUNNING COMMAND: ", end='')
            print(command)
            result = RunResult.CRASH

        try:
            return (out.decode(), result)
        except UnicodeDecodeError as e:
            return ('decoding error', result)
    
    def parse(self, race_string, race1_test='', race2_test=''):
        if self.runresult == RunResult.TIMEOUT:
            return Result.TO
        if self.test.has_race:
            if race_string in self.output:
                if race1_test not in self.output:
                    print("Could not find " + race1_test)
                    return Result.FN
                if race2_test not in self.output:
                    print("Could not find " + race2_test)
                    return Result.FN
                return Result.TP
            else:
                return Result.FN
        else:
            if not race_string in self.output:
                return Result.TN
            else:
                return Result.FP


class RunTestFactory:
    @classmethod
    def createTest(self, test: Test, prefix: str, tool: str, category: str):
        if tool == 'MPIRMA':
            return RunMPITest(test, os.path.join(prefix, tool, category))
        elif tool == 'SHMEM':
            return RunSHMEMTest(test, os.path.join(prefix, tool, category))
        elif tool == 'GASPI':
            return RunGASPITest(test, os.path.join(prefix, tool, category))
        elif tool == 'MUST':
            return RunMUSTTest(test, os.path.join(prefix, tool, category))
        elif tool == 'PARCOACH-static':
            return RunParcoachStaticTest(test, os.path.join(prefix, tool, category))
        elif tool == 'PARCOACH-dynamic':
            return RunParcoachDynamicTest(test, os.path.join(prefix, tool, category))
        else:
            raise Exception("Unknown test tool: ", tool)


class RunMPITest(RunTest):
    def run(self):
        binary_out = f'{self.source_file}.exe'
        command = f"mpicc -fopenmp {self.source_file} -o {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

        if self.runresult != RunResult.SUCCESS:
            print("Compilation failed")
            return

        command = f"mpirun -np {self.test.nprocs} {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

        if self.runresult != RunResult.SUCCESS:
            print("Run failed")
            return

    def parse(self):
        return self.runresult


class RunSHMEMTest(RunTest):
    def run(self):
        binary_out = f'{self.source_file}.exe'
        command = f"oshcc -fopenmp {self.source_file} -o {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

        if self.runresult != RunResult.SUCCESS:
            print("Compilation failed")
            return

        command = f"mpirun -np {self.test.nprocs} {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

        if self.runresult != RunResult.SUCCESS:
            print("Run failed")
            return

    def parse(self):
        return self.runresult

class RunGASPITest(RunTest):
    def run(self):
        binary_out = f'{self.source_file}.exe'
        command = f"mpicc -fopenmp -I/home/ss540294/software/gpi/include /usr/lib64/libGPI2.so -Wl,-rpath=/usr/lib64 {self.source_file} -o {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

        if self.runresult != RunResult.SUCCESS:
            print("Compilation failed")
            return


        command = f"mpirun -np {self.test.nprocs} {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

        if self.runresult != RunResult.SUCCESS:
            print("Run failed")
            return

    def parse(self):
        return self.runresult

class RunMUSTTest(RunTest):
    def run(self):
        binary_out = f'{self.source_file}.exe-must'
        command = f"mpicc -fopenmp -g -Wl,--whole-archive /opt/must/lib/libonReportLoader.a -Wl,--no-whole-archive -ldl -fsanitize=thread {self.source_file} -o {binary_out}"
        self.run_command(command)

        command = f"mustrun -np {self.test.nprocs} --must:distributed --must:nodl --must:output stdout --must:tsan --must:rma {binary_out}"
        self.output, self.runresult = self.run_command(command)
        self.write_stdout(self.output)

    def parse(self):
        if self.test.has_race:
            return super().parse('data race', f'{self.test.basename}:{self.test.race_loc1}', f'{self.test.basename}:{self.test.race_loc2}')
        else:
            return super().parse('data race')


class RunParcoachStaticTest(RunTest):
    def run(self):
        # Static analysis only can detect local buffer races
        if 'remote' in self.test.basename:
            return
        
        binary_out = f'{self.source_file}'
        self.run_command(f"mpicc -fopenmp -O0 -g -S -emit-llvm {self.source_file} -o {binary_out}.ll")
        self.output, self.runresult = self.run_command(f"parcoach -S --check=rma {binary_out}.ll -o {binary_out}-instrumented.ll")
        self.write_stdout(self.output)

    def parse(self):
        if 'remote' in self.test.basename:
            return Result.NOSUPPORT

        if self.test.has_race:
            return super().parse('LocalConcurrency detected', f'LINE {self.test.race_loc1}', f'LINE {self.test.race_loc2}')
        else:
            return super().parse('LocalConcurrency detected')
            


class RunParcoachDynamicTest(RunTest):
    def run(self):
        binary_out = f'{self.source_file}'
        self.run_command(f"mpicc -fopenmp -O0 -g -S -emit-llvm {self.source_file} -o {binary_out}.ll")
        self.run_command(f"parcoach -S --check=rma {binary_out}.ll -o {binary_out}-instrumented.ll")
        self.run_command(f"mpicc -fopenmp -O0 -g {binary_out}-instrumented.ll -o {binary_out}-instrumented.exe -Wl,-rpath=/opt/parcoach/lib /opt/parcoach/lib/libParcoachInstrumentation.so")

        command = f"mpirun -np {self.test.nprocs} {binary_out}-instrumented.exe"
        self.output = "timeout"
        for i in range(10): # need multiple retries since PARCOACH-dynamic sometimes just hangs
            ret, self.runresult = self.run_command(command, timeout=3)
            if self.runresult != RunResult.TIMEOUT:
                self.output = ret
                self.write_stdout(self.output)
                break
            else:
                print("PARCOACH TIMEOUT, retry")
        

    def parse(self):
        if self.test.has_race:
            return super().parse('Error when inserting memory access', f'{os.path.basename(self.test.basename)}:{self.test.race_loc1}', f'{os.path.basename(self.test.basename)}:{self.test.race_loc2}')
        else:
            return super().parse('Error when inserting memory access')


def run_tool_test(filename: str, prefix: str, tool: str, category: str):
    print(os.path.basename(filename))
    t = Test(filename)
    mt = RunTestFactory.createTest(t, prefix, tool, category)
    mt.run()
    print(os.path.basename(filename) + ': ' + mt.parse())
    return os.path.basename(filename), mt.parse()

def run_plain_test(filename: str, prefix: str, model: str, category: str):
    print(os.path.basename(filename))
    t = Test(filename)
    mt = RunTestFactory.createTest(t, prefix, model, category)
    mt.run()
    print(os.path.basename(filename) + ': ' + mt.parse())
    return os.path.basename(filename), mt.parse()


def results_append(results_dict, results, name, discipline):
    for testname, result in results:
        if testname not in results_dict.keys():
            results_dict[testname] = {}
        results_dict[testname]['discipline'] = discipline
        results_dict[testname][name] = result


if __name__ == '__main__':
    args = parser.parse_args()

    csvfile = open('results.csv', 'w', newline='')

    pool = mp.Pool(processes=1)
    results_dict = {}

    if args.mode == 'plain':
        # Plain runs without tool
        for model in args.rma_models:
            print(f"=== {model} ===")
            for discipline in args.disciplines:
                print(f"= {discipline} =")
                testfiles = glob(f"/rmaracebench/{model}/{discipline}/*.c")
                testfiles.sort()
                pool.starmap(run_plain_test, [(f, args.output_folder, model, discipline) for f in testfiles])
    elif args.mode == 'tools':
        # Tool runs
        out_prefix = os.path.join('results-' + datetime.now().strftime("%Y%m%d-%H%M%S"))
        for tool in args.tools:
            print(f"=== {tool} ===")
            for discipline in args.disciplines:
                print(f"= {discipline} =")
                testfiles = glob(f"/rmaracebench/MPIRMA/{discipline}/*.c")
                testfiles.sort()

                results = pool.starmap(run_tool_test, [(f, args.output_folder, tool, discipline) for f in testfiles])
                results_append(results_dict, results, tool, discipline)
        df = pandas.DataFrame.from_dict(results_dict, orient='index')
        df.to_csv(os.path.join(args.output_folder, 'results.csv'))
    else:
        parser.print_help()
        exit(1)