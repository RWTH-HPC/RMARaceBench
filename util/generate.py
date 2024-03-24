# Part of RMARaceBench, under BSD-3-Clause License
# See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
# SPDX-License-Identifier: BSD-3-Clause

from jinja2 import Environment, FileSystemLoader
import os
import pathlib
from enum import Enum

env = Environment(
    loader=FileSystemLoader(".")
)

class Model(str, Enum):
    MPIRMA = 'MPIRMA'
    SHMEM  = 'SHMEM'
    GASPI  = 'GASPI'

    def __str__(self) -> str:
        return self.value


class CaseCounter:
    def __init__(self):
        self.counter = {Model.MPIRMA : 0,
               Model.SHMEM  : 0,
               Model.GASPI  : 0}
        self.race_counter = {Model.MPIRMA : 0,
               Model.SHMEM  : 0,
               Model.GASPI  : 0}

    def get(self, model: Model) -> int:
        return self.counter[model]
    
    def inc_get(self, model: Model, has_race: bool) -> int:
         self.counter[model] += 1
         if has_race:
            self.race_counter[model] += 1
         return self.counter[model]
    
    def set(self, model, value):
        self.counter[model] = value

    def set_races(self, model, value):
        self.race_counter[model] = value
    
    def get_races(self, model: Model) -> int:
        return self.race_counter[model]
    
    def get_noraces(self, model: Model) -> int:
        return self.counter[model] - self.race_counter[model]


caseCounters = {
    'conflict': CaseCounter(),
    'sync': CaseCounter(),
    'atomic': CaseCounter(),
    'hybrid': CaseCounter(),
}

class Operation:
     def __init__(self, model: Model, opname: str, callname: str, local_opkind: str, remote_opkind: str, opcode: str, additional_declarations = ''):
          self.model = model
          self.name = opname
          self.callname = callname
          self.local_opkind = local_opkind
          self.remote_opkind = remote_opkind
          self.code = opcode
          self.additional_declarations = additional_declarations
    
     def __str__(self):
          return self.name

class Combination:
     def __init__(self, op1: Operation, op2: Operation, num_procs: int):
          self.op1 = op1
          self.op2 = op2
          self.num_procs = num_procs

class SourceTemplate:
     def __init__(self, filename, nprocs, has_race=None, operation_combinations=None, threaded=False):
          self.filename = filename
          self.has_race = has_race
          self.operation_combinations = operation_combinations
          self.nprocs = nprocs
          self.threaded = threaded


class OperationManager:
     operations = {}

     def __init__(self):
          for model in Model:
               self.operations[model] = {}

     def add(self, model: Model, name: str, short_name: str, callname: str, local_opkind: str, remote_opkind: str, code: str, additional_declarations = ''):
           self.operations[model][name] = Operation(model, short_name, callname, local_opkind, remote_opkind, code, additional_declarations)

     def get(self, model: Model, name: str) -> Operation:
          return self.operations[model][name]


om = OperationManager()
om.add(Model.MPIRMA, 'local_load', 'load', 'LOAD', 'load', 'load', 'printf("value is %d\\n", value);')
om.add(Model.MPIRMA, 'local_store', 'store', 'STORE', 'store', 'store', 'value = 42;')
om.add(Model.MPIRMA, 'put', 'put', 'MPI_Put', 'local buffer read', 'rma write', 'MPI_Put(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win);')
om.add(Model.MPIRMA, 'put2', 'put', 'MPI_Put', 'local buffer read', 'rma write', 'MPI_Put(&value, 1, MPI_INT, 1, 1, 1, MPI_INT, win);')
om.add(Model.MPIRMA, 'acc', 'acc', 'MPI_Accumulate', 'local buffer read', 'rma atomic write', 'MPI_Accumulate(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, MPI_SUM, win);')
om.add(Model.MPIRMA, 'acc2', 'acc', 'MPI_Accumulate', 'local buffer read', 'rma atomic write', 'MPI_Accumulate(&value, 1, MPI_INT, 1, 1, 1, MPI_INT, MPI_SUM, win);')
om.add(Model.MPIRMA, 'get', 'get', 'MPI_Get', 'local buffer write', 'rma read', 'MPI_Get(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win);')
om.add(Model.MPIRMA, 'remote_load', 'load', 'LOAD', 'load', 'load', 'printf("win_base[0] is %d\\n", win_base[0]);')
om.add(Model.MPIRMA, 'remote_store', 'store', 'STORE', 'store', 'store', 'win_base[0] = 42;')
om.add(Model.MPIRMA, 'rget', 'rget','MPI_Rget', 'local buffer write', 'rma read', 'MPI_Rget(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win, &req);')
om.add(Model.MPIRMA, 'rput', 'rput','MPI_Rput', 'local buffer read', 'rma write', 'MPI_Rput(&value, 1, MPI_INT, 1, 0, 1, MPI_INT, win, &req);')

om.add(Model.MPIRMA, 'gacc1', 'gacc', 'MPI_Get_accumulate', 'local buffer read', 'rma atomic write', 'MPI_Get_accumulate(&value, 1, MPI_INT, &value2, 1, MPI_INT, 1, 0, 1, MPI_INT, MPI_SUM, win);')
om.add(Model.MPIRMA, 'gacc2', 'gacc', 'MPI_Get_accumulate', 'local buffer write', 'rma atomic write', 'MPI_Get_accumulate(&value2, 1, MPI_INT, &value, 1, MPI_INT, 1, 0, 1, MPI_INT, MPI_SUM, win);')
om.add(Model.MPIRMA, 'gaccread', 'gaccread', 'MPI_Get_accumulate', 'local buffer write', 'rma atomic read', 'MPI_Get_accumulate(NULL, 0, MPI_DATATYPE_NULL, &value, 1, MPI_INT, 1, 0, 1, MPI_INT, MPI_NO_OP, win);')
om.add(Model.MPIRMA, 'fop1', 'fop', 'MPI_Fetch_and_op', 'local buffer read', 'rma atomic write', 'MPI_Fetch_and_op(&value, &value2, MPI_INT, 1, 0, MPI_SUM, win);')
om.add(Model.MPIRMA, 'fop2', 'fop', 'MPI_Fetch_and_op', 'local buffer write', 'rma atomic write', 'MPI_Fetch_and_op(&value2, &value, MPI_INT, 1, 0, MPI_SUM, win);')
om.add(Model.MPIRMA, 'cas1', 'cas', 'MPI_Compare_and_swap', 'local buffer read', 'rma atomic write', 'MPI_Compare_and_swap(&value, &win_base[0], &value2, MPI_INT, 1, 0, win);')
om.add(Model.MPIRMA, 'cas2', 'cas', 'MPI_Compare_and_swap', 'local buffer write', 'rma atomic write', 'MPI_Compare_and_swap(&value2, &win_base[0], &value, MPI_INT, 1, 0, win);')


om.add(Model.SHMEM, 'local_load', 'load', 'LOAD', 'load', 'load', 'printf("localbuf is %d\\n", localbuf);')
om.add(Model.SHMEM, 'local_store', 'store', 'STORE', 'store', 'store','localbuf = 42;')
om.add(Model.SHMEM, 'putnbi', 'putnbi', 'shmem_int_put_nbi', 'local buffer read', 'rma write', 'shmem_int_put_nbi(&remote, &localbuf, 1, 1);')
om.add(Model.SHMEM, 'putnbi2', 'putnbi', 'shmem_int_put_nbi', 'local buffer read', 'rma write', 'shmem_int_put_nbi(&remote, &localbuf, 1, 0);')
om.add(Model.SHMEM, 'put', 'put', 'shmem_int_put', 'local buffer read', 'rma write', 'shmem_int_put(&remote, &localbuf, 1, 1);')
om.add(Model.SHMEM, 'atomicset', 'atomicset', 'shmem_int_atomic_set', 'local buffer read', 'rma atomic write', 'shmem_int_atomic_set(&remote, 1, 1);')
om.add(Model.SHMEM, 'atomicfetch', 'atomicfetch', 'shmem_int_atomic_fetch', 'local buffer write', 'rma atomic read', 'localbuf = shmem_int_atomic_fetch(&remote, 1);')
om.add(Model.SHMEM, 'atomicfetchinc', 'atomicfetchinc', 'shmem_int_atomic_fetch', 'local buffer write', 'rma atomic write', 'localbuf = shmem_int_atomic_fetch_inc(&remote, 1);')
om.add(Model.SHMEM, 'atomicfetchincnbi', 'atomicfetchincnbi', 'shmem_int_atomic_fetch_inc_nbi', 'local buffer write', 'rma atomic write', 'shmem_int_atomic_fetch_inc_nbi(&localbuf, &remote, 1);')
om.add(Model.SHMEM, 'atomicfetchnbi', 'atomicfetchnbi', 'shmem_int_atomic_fetch', 'local buffer write', 'rma atomic read', 'shmem_int_atomic_fetch_nbi(&localbuf, &remote, 1);')
om.add(Model.SHMEM, 'atomiccompareswap', 'atomiccompareswap', 'shmem_int_compare_swap', 'local buffer write', 'rma atomic write', 'localbuf = shmem_int_atomic_compare_swap(&remote, 42, 1, 1);')
om.add(Model.SHMEM, 'atomiccompareswapnbi', 'atomiccompareswapnbi', 'shmem_int_compare_swap_nbi', 'local buffer write', 'rma atomic write', 'shmem_int_atomic_compare_swap_nbi(&localbuf, &remote, 42, 1, 1);')
om.add(Model.SHMEM, 'getnbi', 'getnbi', 'shmem_int_get_nbi', 'local buffer write', 'rma read', 'shmem_int_get_nbi(&localbuf, &remote, 1, 1);')
om.add(Model.SHMEM, 'get', 'get', 'shmem_int_get', 'local buffer write', 'rma read', 'shmem_int_get(&localbuf, &remote, 1, 1);')
om.add(Model.SHMEM, 'remote_load', 'load', 'LOAD', 'load', 'load', 'printf("remote is %d", remote);')
om.add(Model.SHMEM, 'remote_store', 'store', 'STORE', 'store', 'store', 'remote = 42;')
om.add(Model.SHMEM, 'put_remote', 'put', 'shmem_int_put', 'local buffer read', 'rma write',  'int myval = 42;\nshmem_int_put(&remote, &myval, 1, 1);')
om.add(Model.SHMEM, 'get_remote', 'get', 'shmem_int_get', 'local buffer write', 'rma read', 'shmem_int_get(&localbuf, &remote, 1, 1);')
om.add(Model.SHMEM, 'put_signal', 'put_signal', 'shmem_int_put_signal', 'local buffer read', 'rma write', 'shmem_int_put_signal(&remote, &localbuf, 1, &ps_sig_addr, 1, SHMEM_SIGNAL_SET, 1);', 'static uint64_t ps_sig_addr = 0;')
om.add(Model.SHMEM, 'put_signal2', 'put_signal', 'shmem_int_put_signal', 'local buffer read', 'rma write', 'shmem_int_put_signal(&remote, &localbuf, 1, &ps_sig_addr2, 1, SHMEM_SIGNAL_SET, 1);', 'static uint64_t ps_sig_addr2 = 0;')
om.add(Model.SHMEM, 'put_signal_nbi', 'put_signal_nbi', 'shmem_int_put_signal_nbi', 'local buffer read', 'rma write', 'shmem_int_put_signal_nbi(&remote, &localbuf, 1, &psn_sig_addr, 1, SHMEM_SIGNAL_SET, 1);', 'static uint64_t psn_sig_addr = 0;')
om.add(Model.SHMEM, 'p', 'p', 'shmem_int_p', '', 'rma write', 'shmem_int_p(&remote, 42, 1);')
om.add(Model.SHMEM, 'g', 'g', 'shmem_int_g', '', 'rma read', 'localbuf = shmem_int_g(&remote, 1);')
om.add(Model.SHMEM, 'iput', 'iput', 'shmem_int_iput', 'local buffer read', 'rma write', 'shmem_int_iput(&remote, &localbuf, 1, 1, 1, 1);')
om.add(Model.SHMEM, 'iget', 'iget', 'shmem_int_iget', 'local buffer write', 'rma read', 'shmem_int_iget(&localbuf, &remote, 1, 1, 1, 1);')

om.add(Model.GASPI, 'local_load', 'load', 'LOAD', 'load', 'load', 'printf("localbuf[0] is %d\\n", localbuf[0]);')
om.add(Model.GASPI, 'local_store', 'store', 'STORE', 'store', 'store', 'localbuf[0] = 42;')
om.add(Model.GASPI, 'remote_load', 'load', 'LOAD', 'load', 'load', 'printf("remote_data[0] is %d\\n", remote_data[0]);')
om.add(Model.GASPI, 'remote_store', 'store', 'STORE', 'store', 'store', 'remote_data[0] = 42;')
om.add(Model.GASPI, 'write', 'write', 'gaspi_write', 'local buffer read', 'rma write', 'gaspi_write(loc_seg_id, 0, 1, remote_seg_id, 0, sizeof(int), queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'write2', 'write', 'gaspi_write', 'local buffer read', 'rma write', 'gaspi_write(loc_seg_id, 0, 0, remote_seg_id, 0, sizeof(int), queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'read', 'read', 'gaspi_read', 'local buffer write', 'rma read', 'gaspi_read(loc_seg_id, 0, 1, remote_seg_id, 0, sizeof(int), queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'fetchadd', 'fetchadd', 'gaspi_atomic_fetch_add', 'local buffer write', 'rma atomic write', 'gaspi_atomic_fetch_add(remote_seg_id, 0, 1, 1, &localbuf[0], GASPI_BLOCK);')
om.add(Model.GASPI, 'write_list', 'write_list', 'gaspi_write_list', 'local buffer read', 'rma write', 'gaspi_write_list(1, &loc_seg_id, (gaspi_offset_t[]) {0}, 1, &remote_seg_id, (gaspi_offset_t[]) {0}, (gaspi_size_t[]) {sizeof(int)}, queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'read_list', 'read_list', 'gaspi_read_list', 'local buffer write', 'rma read', 'gaspi_read_list(1, &loc_seg_id, (gaspi_offset_t[]) {0}, 1, &remote_seg_id, (gaspi_offset_t[]) {0}, (gaspi_size_t[]) {sizeof(int)}, queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'write_list_notify', 'write_list_notify', 'gaspi_write_list_notify', 'local buffer read', 'rma write', 'gaspi_write_list_notify(1, &loc_seg_id, (gaspi_offset_t[]) {0}, 1, &remote_seg_id, (gaspi_offset_t[]) {0}, (gaspi_size_t[]) {sizeof(int)}, remote_seg_id, 0, 1, queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'read_list_notify', 'read_list_notify', 'gaspi_read_list_notiy', 'local buffer write', 'rma read', 'gaspi_read_list_notify(1, &loc_seg_id, (gaspi_offset_t[]) {0}, 1, &remote_seg_id, (gaspi_offset_t[]) {0}, (gaspi_size_t[]) {sizeof(int)}, remote_seg_id, 0, queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'write_notify', 'write_notify', 'gaspi_write_notify', 'local buffer read', 'rma write', 'gaspi_write_notify(loc_seg_id, 0, 1, remote_seg_id, 0, sizeof(int), 0, 1, queue_id, GASPI_BLOCK);')
om.add(Model.GASPI, 'read_notify', 'read_notify', 'gaspi_read_notify', 'local buffer write', 'rma read', 'gaspi_read_notify(loc_seg_id, 0, 1, remote_seg_id, 0, sizeof(int), 0, queue_id, GASPI_BLOCK);')

def gen_conflict_races():
    op_local_load = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'local_load')],
        Model.SHMEM:  [om.get(Model.SHMEM, 'local_load')],
        Model.GASPI:  [om.get(Model.GASPI, 'local_load')]
    }

    op_local_store = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'local_store')],
        Model.SHMEM:  [om.get(Model.SHMEM, 'local_store')],
        Model.GASPI:  [om.get(Model.GASPI, 'local_store')]
    }

    op_local_buffer_read = {
        Model.MPIRMA: [
             om.get(Model.MPIRMA, 'put'),
             ],
        Model.SHMEM:  [
             om.get(Model.SHMEM, 'putnbi'),
             ],
        Model.GASPI:  [
             om.get(Model.GASPI, 'write'),
             ]
    }

    op_local_buffer_read2 = {
        Model.MPIRMA: [
             om.get(Model.MPIRMA, 'put2'),
             ],
        Model.SHMEM:  [
             om.get(Model.SHMEM, 'putnbi2'),
             ],
        Model.GASPI:  [
             om.get(Model.GASPI, 'write2'),
             ]
    }

    op_local_buffer_write = {
        Model.MPIRMA: [
             om.get(Model.MPIRMA, 'get'),
        ],
        Model.SHMEM:  [
             om.get(Model.SHMEM, 'getnbi'),
        ],
        Model.GASPI:  [
             om.get(Model.GASPI, 'read'),
             ]
    }

    op_remote_load  = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'remote_load')],
        Model.SHMEM: [om.get(Model.SHMEM, 'remote_load')],
        Model.GASPI:  [om.get(Model.GASPI, 'remote_load')]
    } 

    op_remote_store  = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'remote_store')],
        Model.SHMEM: [om.get(Model.SHMEM, 'remote_store')],
        Model.GASPI:  [om.get(Model.GASPI, 'remote_store')]
    } 

    op_rma_write = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'put')],
        Model.SHMEM:  [om.get(Model.SHMEM, 'put')],
        Model.GASPI:  [om.get(Model.GASPI, 'write')]
    }

    op_rma_read = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'get')],
        Model.SHMEM:  [om.get(Model.SHMEM, 'get')],
        Model.GASPI:  [om.get(Model.GASPI, 'read')]
    }

    op_rma_atomic_write = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'acc')],
        Model.SHMEM:  [om.get(Model.SHMEM, 'atomicset')],
        Model.GASPI:  [om.get(Model.GASPI, 'fetchadd')]
    }

    op_rma_atomic_read = {
        Model.MPIRMA: [om.get(Model.MPIRMA, 'gaccread')],
        Model.SHMEM:  [om.get(Model.SHMEM, 'atomicfetch')],
        Model.GASPI:  []
    }



    local_race_combinations = [
        (op_local_buffer_read, op_local_load, False),
        (op_local_buffer_read, op_local_store, True),
        (op_local_buffer_read, op_local_buffer_read2, False),
        (op_local_buffer_write, op_local_load, True),
        (op_local_buffer_write, op_local_store, True),
        (op_local_buffer_write, op_local_buffer_read, True),
        (op_local_buffer_write, op_local_buffer_write, True),
    ]

    additional_local_combinations = {
        Model.MPIRMA: [
            (om.get(Model.MPIRMA, 'acc'), om.get(Model.MPIRMA, 'local_store'), True, 2),
            (om.get(Model.MPIRMA, 'acc'), om.get(Model.MPIRMA, 'local_load'), False, 2),
            (om.get(Model.MPIRMA, 'gacc1'), om.get(Model.MPIRMA, 'local_store'), True, 2),
            (om.get(Model.MPIRMA, 'gacc2'), om.get(Model.MPIRMA, 'local_load'), True, 2),
            (om.get(Model.MPIRMA, 'fop1'), om.get(Model.MPIRMA, 'local_store'), True, 2),
            (om.get(Model.MPIRMA, 'fop2'), om.get(Model.MPIRMA, 'local_load'), True, 2),
            (om.get(Model.MPIRMA, 'cas1'), om.get(Model.MPIRMA, 'local_store'), True, 2),
            (om.get(Model.MPIRMA, 'cas2'), om.get(Model.MPIRMA, 'local_load'), True, 2),
        ],
        Model.SHMEM: [
            (om.get(Model.SHMEM, 'put_signal_nbi'), om.get(Model.SHMEM, 'local_store'), True, 2),
            (om.get(Model.SHMEM, 'put_signal_nbi'), om.get(Model.SHMEM, 'local_load'), False, 2),
            (om.get(Model.SHMEM, 'atomicfetchnbi'), om.get(Model.SHMEM, 'local_store'), True, 2),
            (om.get(Model.SHMEM, 'atomicfetchnbi'), om.get(Model.SHMEM, 'local_load'), True, 2),
            (om.get(Model.SHMEM, 'atomicfetchincnbi'), om.get(Model.SHMEM, 'local_store'), True, 2),
            (om.get(Model.SHMEM, 'atomicfetchincnbi'), om.get(Model.SHMEM, 'local_load'), True, 2),
            (om.get(Model.SHMEM, 'atomiccompareswapnbi'), om.get(Model.SHMEM, 'local_load'), True, 2),
            (om.get(Model.SHMEM, 'atomiccompareswapnbi'), om.get(Model.SHMEM, 'local_store'), True, 2),
        ],
        Model.GASPI: [
            (om.get(Model.GASPI, 'write_list'), om.get(Model.GASPI, 'local_load'), False, 2),
            (om.get(Model.GASPI, 'write_list'), om.get(Model.GASPI, 'local_store'), True, 2),
            (om.get(Model.GASPI, 'read_list'), om.get(Model.GASPI, 'local_load'), True, 2),
            (om.get(Model.GASPI, 'read_list'), om.get(Model.GASPI, 'local_store'), True, 2),
            (om.get(Model.GASPI, 'write_notify'), om.get(Model.GASPI, 'local_load'), False, 2),
            (om.get(Model.GASPI, 'write_notify'), om.get(Model.GASPI, 'local_store'), True, 2),
            (om.get(Model.GASPI, 'read_notify'), om.get(Model.GASPI, 'local_load'), True, 2),
            (om.get(Model.GASPI, 'read_notify'), om.get(Model.GASPI, 'local_store'), True, 2),
            (om.get(Model.GASPI, 'write_list_notify'), om.get(Model.GASPI, 'local_load'), False, 2),
            (om.get(Model.GASPI, 'write_list_notify'), om.get(Model.GASPI, 'local_store'), True, 2),
            (om.get(Model.GASPI, 'read_list_notify'), om.get(Model.GASPI, 'local_load'), True, 2),
            (om.get(Model.GASPI, 'read_list_notify'), om.get(Model.GASPI, 'local_store'), True, 2),
        ],
    }


    additional_remote_combinations = {
        Model.MPIRMA: [
            (om.get(Model.MPIRMA, 'gacc1'), om.get(Model.MPIRMA, 'remote_store'), True, 2),
            (om.get(Model.MPIRMA, 'gacc1'), om.get(Model.MPIRMA, 'gacc1'), False, 3),
            (om.get(Model.MPIRMA, 'fop1'), om.get(Model.MPIRMA, 'fop1'), False, 3),
            (om.get(Model.MPIRMA, 'fop1'), om.get(Model.MPIRMA, 'remote_store'), True, 2),
            (om.get(Model.MPIRMA, 'cas1'), om.get(Model.MPIRMA, 'remote_store'), True, 2),
            (om.get(Model.MPIRMA, 'cas1'), om.get(Model.MPIRMA, 'cas1'), False, 3),
        ],
        Model.SHMEM: [
            (om.get(Model.SHMEM, 'put_signal'), om.get(Model.SHMEM, 'remote_store'), True, 2),
            (om.get(Model.SHMEM, 'put_signal'), om.get(Model.SHMEM, 'put_signal2'), True, 3),
            (om.get(Model.SHMEM, 'g'), om.get(Model.SHMEM, 'remote_store'), True, 2),
            (om.get(Model.SHMEM, 'g'), om.get(Model.SHMEM, 'put'), True, 3),
            (om.get(Model.SHMEM, 'p'), om.get(Model.SHMEM, 'remote_load'), True, 2),
            (om.get(Model.SHMEM, 'p'), om.get(Model.SHMEM, 'get'), True, 3),
            (om.get(Model.SHMEM, 'iput'), om.get(Model.SHMEM, 'remote_store'), True, 2),
            (om.get(Model.SHMEM, 'iput'), om.get(Model.SHMEM, 'put'), True, 3),
            (om.get(Model.SHMEM, 'iget'), om.get(Model.SHMEM, 'remote_store'), True, 2),
            (om.get(Model.SHMEM, 'iget'), om.get(Model.SHMEM, 'put'), True, 3),
            (om.get(Model.SHMEM, 'atomicfetchnbi'), om.get(Model.SHMEM, 'atomicfetchnbi'), False, 3),
            (om.get(Model.SHMEM, 'atomicfetchnbi'), om.get(Model.SHMEM, 'remote_load'), False, 2),
            (om.get(Model.SHMEM, 'atomicfetchinc'), om.get(Model.SHMEM, 'atomicfetchinc'), False, 3),
            (om.get(Model.SHMEM, 'atomicfetchnbi'), om.get(Model.SHMEM, 'remote_store'), True, 2),
            (om.get(Model.SHMEM, 'atomiccompareswapnbi'), om.get(Model.SHMEM, 'remote_store'), True, 2),
            (om.get(Model.SHMEM, 'atomiccompareswapnbi'), om.get(Model.SHMEM, 'atomicfetchnbi'), False, 3),
        ],
        Model.GASPI: [
            (om.get(Model.GASPI, 'write_list'), om.get(Model.GASPI, 'remote_load'), True, 2),
            (om.get(Model.GASPI, 'write_list'), om.get(Model.GASPI, 'write'), True, 3),
            (om.get(Model.GASPI, 'read_list'), om.get(Model.GASPI, 'remote_load'), False, 2),
            (om.get(Model.GASPI, 'read_list'), om.get(Model.GASPI, 'write'), True, 3),
            (om.get(Model.GASPI, 'write_notify'), om.get(Model.GASPI, 'remote_load'), True, 2),
            (om.get(Model.GASPI, 'write_notify'), om.get(Model.GASPI, 'write'), True, 3),
            (om.get(Model.GASPI, 'read_notify'), om.get(Model.GASPI, 'remote_load'), False, 2),
            (om.get(Model.GASPI, 'read_notify'), om.get(Model.GASPI, 'write'), True, 3),
            (om.get(Model.GASPI, 'write_list_notify'), om.get(Model.GASPI, 'remote_load'), True, 2),
            (om.get(Model.GASPI, 'write_list_notify'), om.get(Model.GASPI, 'write'), True, 3),
            (om.get(Model.GASPI, 'read_list_notify'), om.get(Model.GASPI, 'remote_load'), False, 2),
            (om.get(Model.GASPI, 'read_list_notify'), om.get(Model.GASPI, 'write'), True, 3),
        ],
    }


    remote_race_combinations = [
        (op_rma_read, op_remote_load,  False, 2),
        (op_rma_read, op_rma_read,   False, 3),
        (op_rma_read, op_remote_store, True,  2),
        (op_rma_read, op_rma_write,   True,  3),
        (op_rma_read, op_rma_atomic_read,   False,  3),
        (op_rma_read, op_rma_atomic_write,   True,  3),
        (op_rma_write, op_remote_load,  True,  2),
        (op_rma_write, op_remote_store, True,  2),
        (op_rma_write, op_rma_write, True,  3),
        (op_rma_write, op_rma_atomic_read,   True,  3),
        (op_rma_write, op_rma_atomic_write,   True,  3),
        (op_rma_atomic_write, op_remote_load,  True,  2),
        (op_rma_atomic_write, op_remote_store, True,  2),
        (op_rma_atomic_write, op_rma_atomic_write, False, 3),
        (op_rma_atomic_write, op_rma_atomic_read, False, 3),
        (op_rma_atomic_read, op_rma_atomic_read, False, 3),
        (op_rma_atomic_read, op_remote_load,  False,  2),
        (op_rma_atomic_read, op_remote_store, True,  2),
    ]

    local_src_templates = {
         'MPIRMA': SourceTemplate("templates/MPIRMA/conflict/MPI-conflict-op1-op2-local-race.c.j2", 2,  [], local_race_combinations), 
         'SHMEM': SourceTemplate("templates/SHMEM/conflict/shmem-conflict-op1-op2-local-race.c.j2", 2, [], local_race_combinations ),
         'GASPI': SourceTemplate("templates/GASPI/conflict/GASPI-conflict-op1-op2-local-race.c.j2", 2, [], local_race_combinations ),
    }

    remote_src_templates = {
        'MPIRMA': SourceTemplate("templates/MPIRMA/conflict/MPI-conflict-op1-op2-remote-race.c.j2", 2, [], remote_race_combinations),
        'SHMEM': SourceTemplate("templates/SHMEM/conflict/shmem-conflict-op1-op2-remote-race.c.j2", 2, [], remote_race_combinations),
        'GASPI': SourceTemplate("templates/GASPI/conflict/GASPI-conflict-op1-op2-remote-race.c.j2", 2, [], remote_race_combinations),
    }

    for (ops1, ops2, has_race) in local_race_combinations:
        for model in Model:
            generated_combos = set()
            for op1 in ops1[model]:
                for op2 in ops2[model]:
                    if tuple(sorted([op1.name, op2.name])) in generated_combos:
                         continue
                    generated_combos.add(tuple(sorted([op1.name, op2.name])))
                    src_template = local_src_templates[model]
                    filename = src_template.filename
                    render_template(filename, caseCounters['conflict'].inc_get(model, has_race), model, op1, op2, has_race, src_template.nprocs)
    
    for model in Model:
        for (op1, op2, has_race, nprocs) in additional_local_combinations[model]:
            src_template = local_src_templates[model]
            filename = src_template.filename
            render_template(filename, caseCounters['conflict'].inc_get(model, has_race), model, op1, op2, has_race, nprocs)


    for (ops1, ops2, has_race, nprocs) in remote_race_combinations:
        for model in Model:
            generated_combos = set()
            for op1 in ops1[model]:
                for op2 in ops2[model]:
                    if tuple(sorted([op1.name, op2.name])) in generated_combos:
                         continue
                    generated_combos.add(tuple(sorted([op1.name, op2.name])))
                    src_template = remote_src_templates[model]
                    filename = src_template.filename
                    render_template(filename, caseCounters['conflict'].inc_get(model, has_race), model, op1, op2, has_race, nprocs)

    for model in Model:
        for (op1, op2, has_race, nprocs) in additional_remote_combinations[model]:
            src_template = remote_src_templates[model]
            filename = src_template.filename
            render_template(filename, caseCounters['conflict'].inc_get(model, has_race), model, op1, op2, has_race, nprocs)


def render_template(template_file: str, number: int, model: Model, op1: Operation, op2: Operation, has_race: bool, nprocs: int, threaded:bool=False):
    out_path, out_basename = os.path.split(template_file)
    out_path = out_path.replace('templates/', '')
    out_file = f"{number:03d}-" + \
               out_basename.replace('race', 'yes' if has_race else 'no') \
                           .replace("op1", op1.name if not op1 is None else '') \
                           .replace("op2", op2.name if not op2 is None else '') \
                           .replace('.j2', '')
    pathlib.Path(out_path).mkdir(parents=True, exist_ok=True)
    filename = os.path.join(out_path,out_file)

    with open(filename, 'w') as f:
        template = env.get_template(template_file)
        if "local" in out_file:
             access_kind = 'local'
        elif "remote" in out_file:
             access_kind = 'remote'
        else:
             print("No kind: ", out_file)
        code = template.render(op1=op1, op2=op2, race=has_race, nprocs=nprocs, access_kind=access_kind, threaded=threaded)
        f.write(code)
        f.close()
        os.system(f"clang-format -i {filename}")

    code = open(filename, 'r').read()

    race_loc1, race_loc2 = (-1,-1)
    if has_race:
        for line_no, line in enumerate(code.splitlines()):
            if "// CONFLICT" in line:
                if race_loc1 == -1:
                    race_loc1 = line_no + 2 # enumeration starts at 0, "// CONFLICT" is found in previous line
                elif race_loc2 == -1:
                    race_loc2 = line_no + 2
                else:
                    print("ERROR: Found more race conflicts than expected")
        code = code.replace('{race_loc1}', str(race_loc1)).replace('{race_loc2}', str(race_loc2))

    with open(filename, 'w') as f:
        f.write(code)
        f.close()
    
    print(f"Generated test case {filename}.")


def gen_sync_races():
    caseCounter = CaseCounter()
    mpi_get_load = [(om.get(Model.MPIRMA, 'get'), om.get(Model.MPIRMA, 'local_load'))]
    mpi_put_load = [(om.get(Model.MPIRMA, 'put'), om.get(Model.MPIRMA, 'remote_load'))]
    mpi_put_get = [(om.get(Model.MPIRMA, 'put'), om.get(Model.MPIRMA, 'get'))]
    mpi_rget_load = [(om.get(Model.MPIRMA, 'rget'), om.get(Model.MPIRMA, 'local_load'))]
    mpi_acc_acc = [(om.get(Model.MPIRMA, 'acc'), om.get(Model.MPIRMA, 'acc'))]

    shmem_get_load = [(om.get(Model.SHMEM, 'get'), om.get(Model.SHMEM, 'local_load'))]
    shmem_remote_conflict = [(om.get(Model.SHMEM, 'put_remote'), om.get(Model.SHMEM, 'get_remote'))]
    shmem_put_remoteload = [(om.get(Model.SHMEM, 'put_remote'), om.get(Model.SHMEM, 'remote_load'))]

    dummy = [(None, None)]

    src_sync_templates = {Model.MPIRMA: [
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-fence-local-race.c.j2", 2, [True, False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-local-race.c.j2", 2, [True, False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-flush-local-race.c.j2", 2, [True, False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lockall-flushlocalall-local-race.c.j2", 2, [True, False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-request-local-race.c.j2", 2, [True, False], mpi_rget_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-pscw-local-race.c.j2", 2, [True, False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lockall-flushall-remote-no.c.j2", 2, [False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lockall-flushall-remote-yes.c.j2", 2, [True], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lockall-barrier-remote-no.c.j2", 2, [False], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lockall-barrier-remote-yes.c.j2", 2, [True], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lockall-remote-yes.c.j2", 2, [True], mpi_get_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-fence-3procs-remote-race.c.j2", 3, [True], mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-fence-3procs-remote-race.c.j2", 3, [False], mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-barrier-nonconsistent-remote-yes.c.j2", 2, [True],  mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-barrier-remote-yes.c.j2", 2, [True],   mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-barrier-remote-no.c.j2", 2, [False],   mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-barrier-sameorigin-remote-no.c.j2", 2, [False],  mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-barrier-sameorigin-remote-yes.c.j2", 2, [True], mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-flushlocal-sameorigin-remote-yes.c.j2", 2, [True], mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-flushlocal-sameorigin-remote-no.c.j2", 2, [False], mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-exclusive-remote-no.c.j2", 2, [False], mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-exclusive-3procs-remote-no.c.j2", 3, [False], mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-exclusive-remote-yes.c.j2", 2, [True], mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-sendrecv-remote-race.c.j2", 2, [True, False], mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-sendrecv-3procs-remote-no.c.j2", 3, [False], mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-lock-sendrecv-3procs-remote-yes.c.j2", 3, [True], mpi_put_load),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-pscw-remote-no.c.j2", 3, [False],  mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-pscw-remote-yes.c.j2", 3, [True],  mpi_put_get),
        SourceTemplate("templates/MPIRMA/sync/MPI-sync-polling-remote-yes.c.j2", 2, [True], mpi_put_load),
    ],
    Model.SHMEM: 
    [
        SourceTemplate("templates/SHMEM/sync/shmem-sync-barrierall-local-race.c.j2", 2, [True, False], shmem_get_load),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-barrierall-remote-race.c.j2", 2, [True, False], shmem_remote_conflict),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-quiet-local-race.c.j2", 2, [True, False], shmem_get_load),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-quiet-sync-remote-no.c.j2", 2, [False], shmem_remote_conflict),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-quiet-sync-remote-yes.c.j2", 2, [True], shmem_remote_conflict),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-fence-put-put-remote-no.c.j2", 2, [False], [(om.get(Model.SHMEM, 'put'), om.get(Model.SHMEM, 'put_remote'))]),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-fence-getnbi-put-remote-yes.c.j2", 2, [True], [(om.get(Model.SHMEM, 'get'), om.get(Model.SHMEM, 'put_remote'))]),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-lock-remote-no.c.j2", 2, [False], [(om.get(Model.SHMEM, 'put_remote'), om.get(Model.SHMEM, 'put_remote'))]),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-lock-remote-yes.c.j2", 2, [True], [(om.get(Model.SHMEM, 'put_remote'), om.get(Model.SHMEM, 'put_remote'))]),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-waituntil-remote-yes.c.j2", 2, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-waituntil-remote-no.c.j2", 2, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-putsignal-remote-no.c.j2", 2, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-putsignal-remote-yes.c.j2", 2, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-ctx-remote-no.c.j2", 2, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-ctx-remote-yes.c.j2", 2, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-collective-reduce-remote-no.c.j2", 4, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-collective-reduce-remote-yes.c.j2", 4, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-team-sync-remote-yes.c.j2", 4, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/sync/shmem-sync-team-sync-remote-no.c.j2", 4, [False], shmem_put_remoteload),
    ],
    Model.GASPI: 
    [
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-local-yes.c.j2", 2, [True], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-local-no.c.j2", 2, [False], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-barrier-remote-no.c.j2", 2, [False], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-barrier-remote-nonconsistent-yes.c.j2", 2, [True], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-barrier-remote-yes.c.j2", 2, [True], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-write-barrier-remote-yes.c.j2", 2, [True], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-notify-waitsome-remote-no.c.j2", 2, [False], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-notify-waitsome-remote-yes.c.j2", 2, [True], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-allreduce-remote-no.c.j2", 3, [False], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-allreduce-remote-yes.c.j2", 3, [True], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-sendrecv-remote-no.c.j2", 2, [False], dummy),
        SourceTemplate("templates/GASPI/sync/GASPI-sync-wait-sendrecv-remote-yes.c.j2", 2, [True], dummy),
    ]
    }

    src_atomic_templates = {Model.MPIRMA: [
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-customdatatype-remote-no.c.j2", 3, [False], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-customdatatype-remote-yes.c.j2", 3, [True], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-disp-remote-yes.c.j2", 3, [True], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-disp-remote-no.c.j2", 3, [False], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-short-int-remote-yes.c.j2", 3, [True], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-float-int-remote-yes.c.j2", 3, [True], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-float-int-sameorigin-remote-yes.c.j2", 2, [True], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-double-float-remote-yes.c.j2", 3, [True], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-int-int-remote-no.c.j2", 3, [False], mpi_acc_acc),
        SourceTemplate("templates/MPIRMA/atomic/MPI-atomic-int-int-sameorigin-remote-no.c.j2", 2, [False], mpi_acc_acc),
    ],
    Model.SHMEM: 
    [
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-different-ctx-remote-yes.c.j2", 3, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-same-ctx-remote-no.c.j2", 3, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-same-domain-remote-no.c.j2", 3, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-int-int-remote-no.c.j2", 3, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-int-int-sameorigin-remote-no.c.j2", 3, [False], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-double-long-remote-yes.c.j2", 3, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-int-long-remote-yes.c.j2", 3, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-int-float-remote-yes.c.j2", 3, [True], shmem_put_remoteload),
        SourceTemplate("templates/SHMEM/atomic/shmem-atomic-int-float-sameorigin-remote-yes.c.j2", 3, [True], shmem_put_remoteload),
    ],

    Model.GASPI: 
    [
        SourceTemplate("templates/GASPI/atomic/GASPI-atomic-fetchadd-fetchadd-remote-no.c.j2", 3, [False], dummy),
        SourceTemplate("templates/GASPI/atomic/GASPI-atomic-fetchadd-fetchadd-remote-offset-yes.c.j2", 3, [True], dummy),
        SourceTemplate("templates/GASPI/atomic/GASPI-atomic-fetchadd-fetchadd-remote-offset-no.c.j2", 3, [False], dummy),
    ]
    }

    src_hybrid_templates = {Model.MPIRMA: [
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-master-local-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-master-local-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-single-local-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-single-local-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-ordered-local-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-for-local-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-section-local-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-section-local-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-task-local-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-task-local-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-master-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-master-remote-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-single-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-single-remote-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-task-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-task-remote-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-section-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-section-remote-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-ordered-remote-no.c.j2", 2, [False], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-for-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-section-barrier-origin-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
        SourceTemplate("templates/MPIRMA/hybrid/MPI-hybrid-section-sendrecv-origin-remote-yes.c.j2", 2, [True], mpi_acc_acc, True),
    ],
    Model.SHMEM: 
    [
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-for-local-yes.c.j2", 2, [True], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-for-ordered-local-no.c.j2", 2, [False], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-master-local-no.c.j2", 2, [False], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-master-local-yes.c.j2", 2, [True], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-single-local-no.c.j2", 2, [False], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-single-local-yes.c.j2", 2, [True], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-section-local-no.c.j2", 2, [False], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-section-local-yes.c.j2", 2, [True], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-task-local-no.c.j2", 2, [False], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-task-local-yes.c.j2", 2, [True], shmem_get_load, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-for-ordered-remote-no.c.j2", 2, [False], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-for-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-master-remote-no.c.j2", 2, [False], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-master-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-single-remote-no.c.j2", 2, [False], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-single-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-section-remote-no.c.j2", 2, [False], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-section-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-task-remote-no.c.j2", 2, [False], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-task-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-lock-section-barrier-origin-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
        SourceTemplate("templates/SHMEM/hybrid/shmem-hybrid-lock-section-barrier-origin-signal-remote-yes.c.j2", 2, [True], shmem_put_remoteload, True),
    ],
    Model.GASPI: 
    [
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-for-local-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-for-ordered-local-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-master-local-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-master-local-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-single-local-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-single-local-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-section-local-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-section-local-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-task-local-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-task-local-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-for-ordered-remote-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-for-remote-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-master-remote-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-master-remote-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-single-remote-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-single-remote-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-section-remote-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-section-remote-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-task-remote-no.c.j2", 2, [False], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-task-remote-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-lock-section-barrier-origin-remote-yes.c.j2", 2, [True], dummy, True),
        SourceTemplate("templates/GASPI/hybrid/GASPI-hybrid-lock-section-barrier-origin-p2p-remote-yes.c.j2", 2, [True], dummy, True),
    ]
    }

    for model in Model:
        for (discipline, src_templates) in [('sync', src_sync_templates), ('atomic', src_atomic_templates), ('hybrid', src_hybrid_templates)]:
            caseCounter = CaseCounter()
            for src_template in src_templates[model]:
                for (op1, op2) in src_template.operation_combinations:
                    for has_race in src_template.has_race:
                        filename = src_template.filename
                        render_template(filename, caseCounters[discipline].inc_get(model, has_race), model, op1, op2, has_race, src_template.nprocs, src_template.threaded)
    

gen_conflict_races()
gen_sync_races()


def printCases(name: str, counter: CaseCounter):
    print(f"{name}\t", end='')
    for model in Model:
        print(f"& {counter.get_races(model):>2} / {counter.get_noraces(model)} / {counter.get(model):>2} \t", end='')
    print("\\\\")

def printStaticstics():
    print("Statistics")
    print("\t\t\t& MPI RMA \t& SHMEM \t& GASPI \t\\\\\\midrule")
    printCases(f'{"Conflict": <16}', caseCounters['conflict'])
    printCases(f'{"Synchronization": <16}', caseCounters['sync'])
    printCases(f'{"Atomic": <16}', caseCounters['atomic'])
    printCases(f'{"Hybrid": <16}', caseCounters['hybrid'])
    total = CaseCounter()
    for model in Model:
        for discipline in ['conflict', 'sync', 'atomic', 'hybrid']:
            total.set(model, total.get(model) + caseCounters[discipline].get(model))
            total.set_races(model, total.get_races(model) + caseCounters[discipline].get_races(model))
    print('\midrule')
    printCases(f'{"Total": <16}', total)

printStaticstics()