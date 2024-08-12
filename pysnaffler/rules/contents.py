import codecs
from pysnaffler.rules.rule import SnaffleRule
from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from typing import List

class SnafflerContentsEnumerationRule(SnaffleRule):
	def __init__(self, enumerationScope:EnumerationScope, ruleName:str, matchAction:MatchAction, relayTargets:List[str], description:str, matchLocation:MatchLoc, wordListType:MatchListType, matchLength:int, wordList:List[str], triage:Triage):
		super().__init__(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation, wordListType, matchLength, wordList, triage)
	
	def match(self, data):
		matches = []
		for rex in self.wordList:
			res = rex.findall(data)
			if res != None and res != []:
				matches += res
		return '\r\n'.join(matches)

	def open_and_match(self, filename):
		try:
			if self.matchLocation == MatchLoc.FileContentAsString:
				with codecs.open(filename, 'r', 'latin-1') as f:
					data = f.read()
					return self.match(data), None
			elif self.matchLocation == MatchLoc.FileContentAsBytes:
				with open(filename, 'rb') as f:
					data = f.read()
					return self.match(data), None
			else:
				return False, Exception('ERROR: Unknown match location: %s' % self.matchLocation)
		except Exception as e:
			return False, e

	def determine_action(self, data):
		pass