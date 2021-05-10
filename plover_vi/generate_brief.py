#!/bin/python
"""Generate two-word brief mappings."""
import sys
import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import List, Dict, Tuple

from plover_vi import config
from plover_vi.stroke import Stroke
from plover_vi.decompose import decompose
from plover_vi.library import TwoWordBriefMapping


def generate(frequency: Dict[str, int], words: List[str])->str:
	#data: Tuple[Dict[..., str], ...]=({}, {}) # [new_tone_placement] = {...: word}
	data: TwoWordBriefMapping=defaultdict(list) # {(onset1, nucleus1, onset2): words}

	frequency_list: List[Tuple[str, int]]=sorted(frequency.items(), key=lambda x: x[1], reverse=True)
	words_lower={word.casefold(): word for word in words}
	frequency=Counter()
	for word, count in frequency_list:
		try:
			word_lower=words_lower[word.casefold()]
		except KeyError:
			continue
		frequency[word_lower]+=count

	for word, count in frequency.most_common():
		try:
			parts=[decompose[syllable.lower()] for syllable in word.split()]
		except KeyError:
			continue

		if len(parts)!=2: continue
		#currently briefs with !=2 words are not supported

		if any(not part.new_tone_placement for part in parts):
			continue

		data[
				" ".join((
					parts[0].onset,
					parts[0].nucleus,
					parts[1].onset,
					))].append(word)

	for key, l in data.items():
		for i, word in enumerate(l):
			if word!=word.lower() and word.lower() in l:
				l[i]=None
		l[:]=list(filter(None, l))

	return dict(sorted(data.items(), key=lambda x: len(x[1]), reverse=True))


if __name__=="__main__":
	import argparse

	parser=argparse.ArgumentParser(
			formatter_class=argparse.ArgumentDefaultsHelpFormatter
			)
	parser.add_argument("wordlist",
			help="Path to the list of actual words. Should be a list of words separated by newlines")
	args=parser.parse_args()

	json.dump(
			generate(json.load(sys.stdin), Path(args.wordlist).read_text().splitlines()),
			sys.stdout,
			ensure_ascii=False, indent=0)
