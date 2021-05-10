LONGEST_KEY = 1


import unicodedata, codecs, sys, re, itertools, json, os
from typing import List, Optional, MutableMapping, Tuple


diacritics_pattern=re.compile(' (WITH|AND) (GRAVE|HOOK ABOVE|TILDE|ACUTE|DOT BELOW)')

def strip_tone(char: str)->str:
	return unicodedata.lookup(diacritics_pattern.sub('', unicodedata.name(char)))

def add_tone(char: str,tone: str)->str:
	if tone=='LEVEL':
		return char
	name=unicodedata.name(char)
	return unicodedata.lookup(name+(' AND ' if 'WITH' in name else ' WITH ')+tone)


onsets: List[str]=['', 'b', 'p', 'tr', 'ch', 's', 'x', 'd', 'gi', 'r', 'l', 'h', 'kh', 'm', 'n', 'đ', 't', 'th', 'ph', 'v', 'q', 'c/k', 'g/gh', 'nh', 'ng/ngh', 'y',]
nucleuses_without_w: List[str]=['a', '/ă', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư', '/â', '/oo', 'ia/iê', 'ưa/ươ', 'ua/uô',]
nucleuses_with_w: List[str]=['oa', '/oă', 'oe', 'uê', 'uy', 'uơ', '/uâ', 'uya/uyê',]
codas: List[str]=['', 'c', 'ch', 'm', 'n', 'ng', 'nh', 'p', 't', 'o/u', 'i/y',]
tones: List[str]=['LEVEL', 'ACUTE', 'GRAVE', 'HOOK ABOVE', 'TILDE', 'DOT BELOW',]


nucleuses: List[str]=nucleuses_without_w+nucleuses_with_w
for it in onsets, nucleuses, codas, tones:
	assert len(set(it))==len(it)

def construct(onset: str, nucleus: str, coda: str, tone: str, new_tone_placement: bool, tolerant: bool=False) -> Optional[str]:
	if None in (onset, nucleus, coda, tone): return None
	assert onset in onsets, onset
	assert nucleus in nucleuses, nucleus
	assert coda in codas, coda
	assert tone in tones, tone

	if onset=='gi':
		if nucleus=='i' and coda=='o/u': return None
		if nucleus=='ia/iê' and coda=='': return None
		if nucleus=='ê' and coda!='': return None

	if coda in ('c','ch','p','t'):
		if tone=='LEVEL':
			if tolerant: tone='ACUTE'
			else: return None
		elif tone not in ('ACUTE','DOT BELOW'):
			return None
	if onset=='q':
		if not (
				nucleus in nucleuses_with_w or
				(nucleus=='ua/uô' and coda)
				):
			return None

	if coda=='o/u' and nucleus in ('o','u'):
		return None
	if coda=='i/y' and nucleus in ('e','ê','ia/iê'):
		# orthographic rule: (nucleus == 'i') + (coda == 'i/y') ==> rime ('-y')
		return None

	if '/' in nucleus:
		nucleus=nucleus.split('/')[1 if coda else 0]
		if not nucleus:
			return None

	if tolerant and onset=='y' and nucleus in ('e','ê'):
		nucleus='iê'

	if '/' in coda:
		if nucleus[-1]=='ă':
			nucleus=nucleus[:-1]+'a'
			coda=coda[-1]  # u/y
		elif coda=='o/u':
			coda='o' if nucleus[-1] in ('a','e') else 'u'
		elif coda=='i/y':
			coda='y' if nucleus[-1]=='â' else 'i'
			if nucleus=='i':
				if onset=='': return None # when the onset is empty, use y- instead of -i
				nucleus, coda='y', ''
			elif nucleus=='uy' and onset=='q':
				nucleus, coda='ui', ''  # aw...

	# (*)
	if nucleus=='uy' and onset=='c/k' and coda!='': # i/y spelling variation
		onset, nucleus='q', 'ui'

	if '/' in onset:
		onset=onset.split('/')[1 if nucleus[0] in ('e','ê','i','y') else 0]

	if onset=='y':
		if nucleus[0]!='i': return None
		onset,nucleus='','y'+nucleus[1:]

	if len(nucleus)==1:
		tone_pos=0
	elif nucleus in nucleuses_with_w:
		tone_pos=1
		if not new_tone_placement and nucleus in ('oa','oe','uy') and coda=='' and onset!='q':
			tone_pos=0
	else:
		tone_pos=len(nucleus)-1 if coda else len(nucleus)-2

	if onset=='q':
		if nucleus=='ua':
			tone_pos=1
		nucleus='u'+nucleus[1:]

	return (
		(onset[:-1] if onset.endswith(nucleus[0]) else onset)+
		nucleus[:tone_pos]+add_tone(nucleus[tone_pos],tone)+nucleus[tone_pos+1:]+
		coda)


TwoWordBriefMapping=MutableMapping[str, List[str]]
