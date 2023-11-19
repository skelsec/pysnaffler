from typing import List

from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from pysnaffler.rules.rule import SnaffleRule


class SnafflerShareRule(SnaffleRule):
    def __init__(self, enumerationScope: EnumerationScope, ruleName: str, matchAction: MatchAction,
                 relayTargets: List[str], description: str, matchLocation: MatchLoc, wordListType: MatchListType,
                 matchLength: int, wordList: List[str], triage: Triage):
        super().__init__(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation,
                         wordListType, matchLength, wordList, triage)

    def match(self, data):
        return any(rex.search(data) is not None for rex in self.wordList)

    def determine_action(self, data):
        if self.match(data) is False:
            return None, None
        return self.matchAction, self.triage
