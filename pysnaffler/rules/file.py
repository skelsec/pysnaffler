import copy
from pathlib import Path
from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from typing import List
from pysnaffler.rules.rule import SnaffleRule

class SnafflerFileRule(SnaffleRule):
	def __init__(self, enumerationScope:EnumerationScope, ruleName:str, matchAction:MatchAction, relayTargets:List[str], description:str, matchLocation:MatchLoc, wordListType:MatchListType, matchLength:int, wordList:List[str], triage:Triage):
		super().__init__(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation, wordListType, matchLength, wordList, triage)
	
	def match(self, smbfile):
		if self.matchLocation == MatchLoc.FileName:
			for rex in self.wordList:
				if rex.search(smbfile.name) is not None:
					return True
		elif self.matchLocation == MatchLoc.FileExtension:
			fullpath = copy.deepcopy(smbfile.fullpath)
			if fullpath.endswith('.bak') is True:
				fullpath = smbfile.fullpath[:-4]
			ext = Path(fullpath).suffix
			if ext == '':
				return False
			for rex in self.wordList:
				if rex.search(ext) is not None:
					return True
		elif self.matchLocation == MatchLoc.FilePath:
			for rex in self.wordList:
				if rex.search(smbfile.fullpath) is not None:
					return True
		elif self.matchLocation == MatchLoc.FileLength:
			if smbfile.size == self.matchLength:
				return True
		return False

	def determine_action(self, smbfile):
		if self.match(smbfile) is False:
			return None, None
		return self.matchAction, self.triage