from pysnaffler.rules.rule import SnaffleRule
from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from typing import List


class SnafflerShareRule(SnaffleRule):
	def __init__(self, enumerationScope:EnumerationScope, ruleName:str, matchAction:MatchAction, relayTargets:List[str], description:str, matchLocation:MatchLoc, wordListType:MatchListType, matchLength:int, wordList:List[str], triage:Triage):
		super().__init__(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation, wordListType, matchLength, wordList, triage)
	
	def match(self, data):
		for rex in self.wordList:
			if rex.search(data) is not None:
				return True
		return False

	def determine_action(self, data):
		if self.match(data) is False:
			return None, None
		return self.matchAction, self.triage