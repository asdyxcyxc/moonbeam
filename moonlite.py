#!/usr/bin/env python
#
# Copyright 2017 anonymous
#
# This software is the result of a joint project between the anonymous
# aand anonymous. 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#


from argparse import ArgumentParser
import glob
import logging
import os
import re
import sys
import time


logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s: [%(name)s] %(message)s')
logger = logging.getLogger('moonlite')


class ProgramStatus(object):
    """
    A simple class to show the progress.
    """
    def __init__(self, N, interval=1.0):
        self._N = N
        self._interval = interval
        self._last_show = time.time()
        self._start_timer = 0.0
        self._time = [0.0, 0.0, 0.0]
        self._item_N = [0, 0, 0]
        self._total_N = [N, N, N, N]
        self._label = ['Read files\t', 'Trace\t\t', 'Output\t\t']
        self._modules = 3
        self._last_modules = 3
        self._item_id = 0

    def start_timing(self, item_id):
        self._start_timer = time.time()
        self._item_id = item_id

    def update_item(self, n):
        idx = self._item_id
        self._item_N[idx] = n
        cur_time = time.time()
        self._time[idx] += cur_time - self._start_timer
        if cur_time - self._last_show >= self._interval:
            self._last_show = cur_time
            self.update_stat(True)

    def update_stat(self, revert_pos):
        if revert_pos:
            for i in xrange(self._last_modules):
                sys.stdout.write('\033[1A\033[K')
        self._last_modules = self._modules
        for i in xrange(self._modules):
            percent = self._item_N[i] * 100.0 / self._total_N[i]
            sys.stdout.write('%s: %.6fs\t%d/%d\t%.2f%%\n' % (self._label[i],
                                                             self._time[i],
                                                             self._item_N[i],
                                                             self._total_N[i],
                                                             percent))


class BitVector(object):
    def __init__(self):
        self._count = 0
        self._current_char = 0
        self._vector = ''

    def get_vector(self):
        if self._count is not 0:
            self._add_char()

        return self._vector

    def add_bit(self, bit):
        if bit % 2 is 1:
            self._current_char += 1 << (7 - self._count)

        self._count += 1

        if self._count == 8:
            self._add_char()

    def _add_char(self):
        self._vector += chr(self._current_char)
        self._current_char = 0
        self._count = 0

    def save(self, output_path):
        logger.info('Saving bit vector trace to %s', output_path)

        with open(output_path, 'w') as f:
            f.write(self.get_vector())


def generate_bit_vector(current_tuples, global_tuples):
    """
    Generate the bit vector.

    Args:
        current_tuples: the tuples read from a particular file.
        global_tuples: global view of existing tuple. Required to identify the
            position of a tuple in the bitvector.

    Returns:
        Bitvector representation of the given tuples.
    """
    bit_vector = BitVector()
    idx = 0
    idx_max = len(current_tuples)
    last = -1

    for global_tuple in global_tuples:
        if idx >= idx_max:
            bit_vector.add_bit(0)
            continue

        if global_tuple < current_tuples[idx]:
            bit_vector.add_bit(0)
            continue

        while idx < idx_max and global_tuple > current_tuples[idx]:
            if last == global_tuple:
                logger.info('%d', global_tuple)
            idx += 1
            last = global_tuple

        if idx < idx_max and global_tuple == current_tuples[idx]:
            bit_vector.add_bit(1)
        else:
            bit_vector.add_bit(0)

    return bit_vector


def read_afltuples(file_name):
    """
    Gets the afl tuples result of calling afl-showmap.

    Args:
        file_name: file name of the result of afl-showmap.

    Returns:
        A list of afl tuples contained in the file
    """
    with open(file_name, 'r') as f:
        lines = f.readlines()

    return [int(line.split(':')[0]) for line in lines if line]


def main():
    """The main function."""
    parser = ArgumentParser(description='Convert AFL tuples to Moonshine '
                                        'bitvectors')
    parser.add_argument('-i', '--in-dir', default='.',
                        help='Input directory')
    parser.add_argument('-o', '--out-dir', default='.',
                        help='Output directory')
    parser.add_argument('-p', '--input-prefix', default='afltuples-',
                        help='Prefix prepended to the input file. Default is '
                             '`afltuples-`')
    parser.add_argument('-r', '--output-prefix', default='exemplar-',
                        help='Prefix prepended to output files. Default is '
                             '`exemplar-`')
    parser.add_argument('-s', '--show-progress', action='store_true',
                        default=False, help='show progress')
    args = parser.parse_args()

    in_dir = args.in_dir
    if not os.path.isdir(in_dir):
        logger.error('The input directory %s is invalid', in_dir)
        sys.exit(1)
    in_dir = os.path.abspath(in_dir)

    out_dir = args.out_dir
    if not os.path.isdir(out_dir):
        logger.error('The output directory %s is invalid', out_dir)
        sys.exit(1)
    out_dir = os.path.abspath(out_dir)

    in_prefix = args.input_prefix
    input_regex = re.compile(r'%s(?P<input>.*)' % in_prefix)
    out_prefix = args.output_prefix

    show_progress = args.show_progress

    tuple_files = glob.glob(os.path.join(in_dir, '%s*' % in_prefix))
    if not tuple_files:
        logger.error('No files with prefix `%s` found in %s', in_prefix,
                     in_dir)
        sys.exit(1)

    if show_progress:
        stat = ProgramStatus(len(tuple_files), 1.0)
        f_counter = 0
        stat.update_stat(False)

    tuples_seen = set()
    for tuple_file in tuple_files:
        if show_progress:
            f_counter += 1
            stat.start_timing(0)

        afl_tuples = read_afltuples(tuple_file)

        if show_progress:
            stat.update_item(f_counter)
            stat.start_timing(1)

        tuples_seen |= set(afl_tuples)

        if show_progress:
            stat.update_item(f_counter)

    if show_progress:
        f_counter = 0

    for tuple_file in tuple_files:
        if show_progress:
            f_counter += 1
            stat.start_timing(2)

        afl_tuples = read_afltuples(tuple_file)
        input_file = input_regex.search(tuple_file).group('input')
        out_path = os.path.join(out_dir, '%s%s.bv' % (out_prefix, input_file))

        bv = generate_bit_vector(sorted(afl_tuples), sorted(list(tuples_seen)))
        bv.save(out_path)

        if show_progress:
            stat.update_item(f_counter)

    if show_progress:
        stat.update_stat(True)


if __name__ == '__main__':
    main()
