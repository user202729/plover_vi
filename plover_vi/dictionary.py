#!/bin/python
from typing import List, Dict, Optional, Union, Iterable
from pathlib import Path
import json

from plover import system, config  # type: ignore

import plover_vi.config
from plover_vi import library
from plover_vi.stroke import Stroke, decompose, remap, subsets

LONGEST_KEY=2

vowel_mask               =Stroke("AOEU")
left_mask                =Stroke("TKPWHR")
left_w_mask              =Stroke("S")
right_mask               =Stroke("-FRPBLG")
right_w_mask             =Stroke("-S")
star_mask                =Stroke("*")
right_coda_mask          =Stroke("-FRPB")
right_tone_mask          =Stroke("-LGTS")
right_disambiguation_mask=Stroke("-TS")
vowel_glide_mask         =vowel_mask|Stroke("S")

right_disambiguation_index: Dict[Stroke, int]={
        Stroke("")   : 0,
        Stroke("-S") : 1,
        Stroke("-T") : 2,
        Stroke("-TS"): 3,
        }

left_to_right_mirror: Dict[str, str]={
		'T-': '-L',
		'K-': '-G',
		'P-': '-P',
		'W-': '-B',
		'H-': '-F',
		'R-': '-R',
		}
right_to_left_mirror: Dict[str, str]={
		right: left for left, right in left_to_right_mirror.items()
		}

right_to_coda_builder: Dict[Stroke, Union[str, List[str]]]={
		# those that can also be used as coda
		# if list,[0] is onset and[1] is coda
		Stroke(""     ): '',
		Stroke("-P"   ): ['ng/ngh', 'ng'],
		Stroke("-PB"  ): ['c/k', 'c'],
		Stroke("-FRP" ): 'nh',
		Stroke("-FRPB"): 'ch',
		Stroke("-FP"  ): 'm',
		Stroke("-FPB" ): 'p',
		Stroke("-F"   ): 'p', # easier alternative
		Stroke("-RP"  ): 'n',
		Stroke("-RPB" ): 't',
		Stroke("-RB"  ): ['y', 'i/y'],
		}

right_to_coda: Dict[Stroke, str]={
		**{stroke: (item[1] if isinstance(item, list) else item) for stroke, item in right_to_coda_builder.items()},
		Stroke("-B"   ): 'o/u',
		}

right_to_onset_common_coda_part: Dict[Stroke, str]={
		stroke: (item[0] if isinstance(item, list) else item) for stroke, item in right_to_coda_builder.items()
		}

left_to_consonant_onset_only: Dict[Stroke, str]={
		Stroke("KPW"  ): 'b',
		Stroke("TKP"  ): 'd',
		Stroke("TK"   ): 'đ',
		Stroke("TKPW" ): 'g/gh',
		Stroke("TKPWR"): 'gi',
		Stroke("TW"   ): 'h',
		Stroke("KPH"  ): 'kh',
		Stroke("HR"   ): 'l',
		Stroke("TP"   ): 'ph',
		Stroke("KW"   ): 'q',
		Stroke("R"    ): 'r',
		Stroke("KPR"  ): 's',
		Stroke("TH"   ): 'th',
		Stroke("TR"   ): 'tr',
		Stroke("TPR"  ): 'v',
		Stroke("KP"   ): 'x',
		}

for stroke, consonant in right_to_onset_common_coda_part.items(): # partial conflict check. There's no runtime way to check dictionary literal doesn't have conflicts
	assert remap(stroke, right_to_left_mirror) not in left_to_consonant_onset_only, (stroke, remap(stroke, right_to_left_mirror), consonant)



left_to_consonant={
		**{remap(stroke, right_to_left_mirror): item for stroke, item in right_to_onset_common_coda_part.items()},
		**left_to_consonant_onset_only}

vowel_glide_to_stroke: Dict[Stroke, str]={
		Stroke("A"    ): 'a',
		Stroke("AE"   ): '/ă',
		Stroke("E"    ): 'e',
		Stroke("AOE"  ): 'ê',
		Stroke("EU"   ): 'i',
		Stroke("O"    ): 'o',
		Stroke("OEU"  ): 'ô',
		Stroke("OE"   ): 'ơ',
		Stroke("U"    ): 'u',
		Stroke("AOU"  ): 'ư',
		Stroke("AEU"  ): '/â',
		Stroke("AOEU" ): 'ia/iê',
		Stroke("OU"   ): 'ưa/ươ',
		Stroke("AU"   ): 'ua/uô',

		Stroke("SA"   ): 'oa',
		Stroke("SAE"  ): '/oă',
		Stroke("SE"   ): 'oe',
		Stroke("SAOE" ): 'uê',
		Stroke("SO"   ): '/oo',  # orthographic special case
		Stroke("SEU"  ): 'uy',
		Stroke("SOE"  ): 'uơ',
		Stroke("SAEU" ): '/uâ',
		Stroke("SAOEU"): 'uya/uyê',
		}

right_to_tone: Dict[Stroke, str]={
		Stroke(""     ): 'LEVEL',
		Stroke("-G"   ): 'ACUTE',
		Stroke("-L"   ): 'GRAVE',
		Stroke("-GS"  ): 'DOT BELOW',
		Stroke("-LS"  ): 'HOOK ABOVE',
		Stroke("-LG"  ): 'TILDE',
		}

right_to_consonant={
		remap(left, left_to_right_mirror): consonant
		for left, consonant in left_to_consonant.items()
		}



del right_to_coda_builder
del right_to_onset_common_coda_part
del left_to_consonant_onset_only


for left, consonant in left_to_consonant.items():
	assert left in left_mask, left
	assert consonant in library.onsets, consonant

for right, consonant in right_to_consonant.items():
	assert right in right_mask, right
	assert consonant in library.onsets, consonant

for right, tone in right_to_tone.items():
	assert right in right_tone_mask, right
	assert tone in library.tones, tone

for stroke, vowel_glide in vowel_glide_to_stroke.items():
	assert stroke in vowel_glide_mask
	assert vowel_glide in library.nucleuses, vowel_glide

two_word_brief: library.TwoWordBriefMapping
try:
	two_word_brief=json.loads(
		plover_vi.config.two_word_brief_default_path.read_text(encoding='u8'))
except FileNotFoundError:
	two_word_brief={}

def lookup(strokes: List[str])->Optional[str]:
	#might raise KeyError
	assert len(strokes) in (1, 2)
	disambiguation: Optional[Stroke]=None
	index1: int=0
	try:
		stroke: Stroke=Stroke(strokes[0])
		if len(strokes)==2:
			disambiguation=Stroke(strokes[1])
			if disambiguation not in right_disambiguation_index:
				return None
			index1=right_disambiguation_index[disambiguation]
			assert index1!=0
	except ValueError:
		return None


	if stroke&vowel_mask:
		if stroke&star_mask:
			# 2-word brief
			left_part, left_vowel_glide, right_part, star, right_disambiguation, rest=decompose(
					stroke, left_mask, vowel_glide_mask, right_mask, star_mask, right_disambiguation_mask)
			if rest: return None
			assert star==star_mask
			words: List[str]=two_word_brief[
					' '.join((
						left_to_consonant[left_part],
						vowel_glide_to_stroke[left_vowel_glide],
						right_to_consonant[right_part],
					))] #might raise KeyError
			assert words

			try:
				import plover_textarea
				try:
					instance=plover_textarea.extension.get_instance()
					window_name=":plover_vi_brief_suggestion"
					instance.clear(window_name)
					for index, word in enumerate(words[:4]):
						instance.write(window_name, f"{index+1}: {word}\n")
					instance.write(window_name, "~~~")
				except RuntimeError:
					pass
			except ImportError:
				pass

			index=right_disambiguation_index[right_disambiguation]
			if index1!=0 and index!=0: return None
			index+=index1
			if index>=len(words): return None
			return words[index]
		else:
			# simple word
			if index1: return None
			left_part, vowel_glide, right_coda, right_tone, rest=decompose(
					stroke, left_mask, vowel_glide_mask, right_coda_mask, right_tone_mask)
			if rest: return None

			return library.construct(
					left_to_consonant[left_part],
					vowel_glide_to_stroke[vowel_glide],
					right_to_coda[right_coda],
					right_to_tone[right_tone],
					new_tone_placement=True, tolerant=True)
	else:
		if index1: return None
		if stroke&star_mask:
			# 1 or >=3-word brief
			# TODO unimplemented
			return None
		else:
			# 2-character acronym (uppercase)
			# TODO unimplemented
			return None

#def reverse_lookup(text: str):
#	from plover_vi import decompose # this import may be time-consuming, make it lazy
#	if decompose(text)
