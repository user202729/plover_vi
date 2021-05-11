#!/bin/python
# heuristic, repeatedly merge least common until fit.

import operator
import json
import itertools
import sys
from typing import Dict, Mapping, List, Optional, Tuple
from collections import Counter, defaultdict
import argparse
from tempfile import gettempdir
from pathlib import Path

from plover_vi.decompose import decompose

parser=argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		usage="Search through two-word brief systems."
		)
parser.add_argument("frequency_file", help="Path to JSON frequency file.")
parser.add_argument("output_log_directory", help="Path to temporary log file output directory",
		nargs="?", default=gettempdir())
parser.add_argument("--search-all", "-a", help="Search all possible partitions. "
		"If this argument is not set, the list of partitions to search in the source code "
		"should also be modified", action="store_true")
args=parser.parse_args()

Parts=Tuple[str, ...]

frequency: Dict[str, int]=json.load(open(args.frequency_file))
frequency=dict(list(frequency.items())[:10000])
part_frequency: List[Counter]=[Counter() for _ in range(8)]
frequency_parts_mapped: Dict[Parts, int]=Counter()
old_word={}
for word, count in frequency.items():
	a0, b0=word.split()
	try:
		a, b=decompose[a0.lower()], decompose[b0.lower()]
	except KeyError:
		continue
	parts: Parts=(a.onset, a.nucleus, a.coda, a.tone, b.onset, b.nucleus, b.coda, b.tone)
	# ignore tone placement... (so there might be overlaps)
	#assert parts not in old_word, ((word, a, b), old_word[parts])
	old_word[parts]=word
	frequency_parts_mapped[parts]+=count
	for i in range(8):
		part_frequency[i][parts[i]]+=count


MergedCounter=List[Tuple[Parts, int]]
MergeMapping=Mapping[str,
		#Parts
		int # some unique identifier
		]

def compression_sequence(frequency: Mapping[str, int])->List[MergeMapping]:
	result: List[MergedCounter]=[[] for _ in range(len(frequency)+1)]
	result[-1]=[
			((key,), value)
			for key, value in frequency.items()]
	for i in range(len(result)-1, 1, -1):
		cur=result[i]
		result[i]=sorted(cur, key=operator.itemgetter(1))
		key1, value1=cur[0]
		key2, value2=cur[1]
		result[i-1]=[(key1+key2, value1+value2), *cur[2:]]
	assert len(result[1])==1
	assert not result[0]
	return [
			{
				key: index
				for index, (keys, count) in enumerate(merged_counter)
				for key in keys}
			for merged_counter in result
			]

part_compression=[compression_sequence(frequency) for frequency in part_frequency]

#import readline
#import code
#code.interact(local=locals())

# assumption: 11 independent bits each hand => 22 in total
from math import ceil, log2
partitions=[
		partition
		for partition in itertools.product(*(
			range(0, ceil(log2(len(part_frequency[i]))-1e-10)+1)
			for i in range(8)
			))
		if sum(partition)==22]

import time
import datetime
start_time=time.time()
import random
random.shuffle(partitions)

if not args.search_all:
	partitions=[
	(5, 0, 4, 3, 5, 0, 4, 1),
	(5, 0, 4, 0, 5, 5, 0, 3),
	(5, 0, 4, 1, 5, 0, 4, 3),
	(5, 0, 4, 3, 5, 5, 0, 0),
	(5, 5, 0, 0, 5, 0, 4, 3),

	# current
	(5, 5, 0, 0, 5, 0, 0, 0),
	# alternative
	(5, 5, 0, 0, 5, 5, 0, 0),
	(5, 0, 5, 0, 5, 0, 5, 0),
	(5, 5, 0, 1, 5, 5, 0, 0),
	(5, 5, 0, 1, 5, 5, 0, 1),
	(5, 0, 5, 1, 5, 0, 5, 0),
	(5, 0, 5, 1, 5, 0, 5, 1),
	(5, 4, 0, 1, 5, 4, 0, 0),
	(5, 4, 0, 1, 5, 4, 0, 1),
	(5, 0, 5, 1, 5, 0, 5, 0),
	(5, 0, 5, 1, 5, 0, 5, 1),
			]

for partition_index, partition in enumerate(partitions):
	cur_part_compression=[part_compression[i][min(len(part_compression[i])-1, 2**partition[i])] for i in range(8)]
	def remap(parts): return tuple(
		cur_index_part_compression[part]
		for part, cur_index_part_compression in zip(parts, cur_part_compression)
		)
	distinct_values={remap(parts) for parts, count in frequency_parts_mapped.items()}
	# disregard frequency for now...
	conflict_count=len(frequency_parts_mapped)-len(distinct_values)
	print(
			partition,
			partition_index, "/", len(partitions),
			":",
			conflict_count,
			":",
			datetime.timedelta(
				seconds=
				(time.time()-start_time)/(partition_index+1)*len(partitions)
				)
			)

	if not args.search_all:
		frequency_list: List[Tuple[Parts, int]]=sorted(
				frequency_parts_mapped.items(), key=lambda x: x[1], reverse=True)
		data_: Dict[Parts, List[Tuple[str, int]]]=defaultdict(list)
		for parts_, count in frequency_list:
			data_[
					remap(parts_)
					].append((
						old_word[parts_],
						count))
		partition_string="".join(map(str, partition))
		with open(Path(args.output_log_directory)/f"log_{partition_string}_{conflict_count}.json", "w") as f:
			data_2=[
					#[word for word, count in words]
					words
					for words in 
					sorted(
						[words for words in data_.values() if len(words)!=1]
						, key=lambda words: words[1][1], reverse=True)
					]

			f.write("[\n")
			for index, item in enumerate(data_2):
				if index!=0:
					f.write(",\n")
				json.dump(
						item,
						f,
						ensure_ascii=False,
						#indent=0
						)
			f.write("\n]")
