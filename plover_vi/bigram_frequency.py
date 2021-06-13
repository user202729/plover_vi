#!/bin/python
# does not filter upper/lowercase
#
# might consume a lot of memory and take some time
# for the Wikipedia dump file viwiki-latest-pages-articles-multistream3.xml-p3452086p4565246
# (170 MiB, download from https://dumps.wikimedia.org/viwiki/latest/
#  read instructions from https://en.wikipedia.org/wiki/Wikipedia:Database_download#Where_do_I_get_it? )
# it consumes 4GiB of RAM and takes half a minute



import re
import sys
import json
from collections import Counter

data_=sys.stdin.read()
data=re.split(r"(\w+)", data_)
# 1, 3, ...: word
# 0, 2, ...: non-word
result=Counter(
		data[split_index-1]+' '+data[split_index+1]
		for split_index in range(2, len(data)-2, 2)
		if data[split_index].isspace())
json.dump(dict(result.most_common()), sys.stdout,
		indent=0, ensure_ascii=False)
