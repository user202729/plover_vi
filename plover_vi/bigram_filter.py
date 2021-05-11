#!/bin/python
import sys
import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

parser=argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		usage="Take a frequency list from stdin, output the filtered frequency list to stdout."
		)
parser.add_argument("wordlist",
		help="Path to the list of actual words. Should be a list of words separated by newlines")
args=parser.parse_args()

words: List[str]=Path(args.wordlist).read_text().splitlines()
frequency: Dict[str, int]=json.load(sys.stdin)

frequency_list: List[Tuple[str, int]]=sorted(frequency.items(), key=lambda x: x[1], reverse=True)
words_lower={word.casefold(): word for word in words}
frequency=Counter()
for word, count in frequency_list:
	try:
		word_lower=words_lower[word.casefold()]
	except KeyError:
		continue
	frequency[word_lower]+=count

json.dump(dict(frequency.most_common()), sys.stdout, ensure_ascii=False, indent=0)
