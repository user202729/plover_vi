from .library import construct, onsets, nucleuses, codas, tones
from typing import NamedTuple, Dict, List

class SyllableParts(NamedTuple):
	onset: str
	nucleus: str
	coda: str
	tone: str
	new_tone_placement: bool

decompose: Dict[str, SyllableParts]={}

for new_tone_placement in (False, True): # prefer (True) to (False)
	for onset in onsets:
		for nucleus in nucleuses:
			for coda in codas:
				for tone in tones:
					word=construct(onset, nucleus, coda, tone, new_tone_placement)
					if word is not None:
						decompose[word]=SyllableParts(onset, nucleus, coda, tone, new_tone_placement)
