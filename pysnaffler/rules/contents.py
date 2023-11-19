import codecs
from typing import List

from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from pysnaffler.rules.rule import SnaffleRule


class SnafflerContentsEnumerationRule(SnaffleRule):
    def __init__(self, enumerationScope: EnumerationScope, ruleName: str, matchAction: MatchAction,
                 relayTargets: List[str], description: str, matchLocation: MatchLoc, wordListType: MatchListType,
                 matchLength: int, wordList: List[str], triage: Triage):
        super().__init__(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation,
                         wordListType, matchLength, wordList, triage)

    def match(self, data):
        for rex in self.wordList:
            res = rex.findall(data)
            if res is not None:
                for r in res:
                    if r != '':
                        break
                else:
                    return ''
                return '\r\n'.join(res)
        return None

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
                return False, Exception(f'ERROR: Unknown match location: {self.matchLocation}')
        except Exception as e:
            return False, e

    def determine_action(self, data):
        pass
