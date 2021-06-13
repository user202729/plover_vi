from typing import List, Dict, Iterable, Optional

from plover import system  # type: ignore

from plover_stroke import BaseStroke  # type: ignore
from plover_vi import initialize_independent_script

class Stroke(BaseStroke): pass
Stroke.setup(system.KEYS, system.IMPLICIT_HYPHEN_KEYS, system.NUMBER_KEY, system.NUMBERS)
# https://github.com/openstenoproject/plover/discussions/1224

def subsets(stroke: Stroke)->Iterable[Stroke]:
	import itertools
	for keys in itertools.product([[], [key]] for key in stroke.keys()):
		yield Stroke(itertools.chain(keys))

def remap(stroke: Stroke, keymap: Dict[str, str])->Stroke:
	return Stroke([keymap[key] for key in stroke.keys()])

def decompose(stroke: Stroke, *parts)->List[Stroke]:
	"""
	Given a list of mutually disjoint stroke parts, break stroke into parts in that list
	and the "remaining" component (returned as the last item of the list)

	Example:

	>>> decompose(Stroke("STK"), Stroke("S-S"), Stroke("T-T"))
	[Stroke("S"), Stroke("T"), Stroke("K")]
	"""
	combined_before=Stroke()
	result: List[Stroke]=[]
	for part in parts:
		result.append(stroke&part)
		stroke-=part
		assert not combined_before&part
		combined_before+=part
	result.append(stroke)
	return result
