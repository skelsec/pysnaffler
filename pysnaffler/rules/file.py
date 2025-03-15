import copy
from pathlib import Path
from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from typing import List
from pysnaffler.rules.rule import SnaffleRule

class SnafflerFileRule(SnaffleRule):
	def __init__(self, enumerationScope:EnumerationScope, ruleName:str, matchAction:MatchAction, relayTargets:List[str], description:str, matchLocation:MatchLoc, wordListType:MatchListType, matchLength:int, wordList:List[str], triage:Triage):
		super().__init__(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation, wordListType, matchLength, wordList, triage)
	
	def match(self, smbfile, fullpath:str=None, name:str=None, size:int=None, **kwargs):
		if smbfile is not None:
			fullpath = smbfile.fullpath
			name = smbfile.name
			size = smbfile.size
		else:
			if fullpath is None or name is None or size is None:
				raise ValueError('If smbfile is not provided, fullpath, name, and size are required for file matching')

		if self.matchLocation == MatchLoc.FileName:
			for rex in self.wordList:
				if rex.search(name) is not None:
					return True
		elif self.matchLocation == MatchLoc.FileExtension:
			fullpath = copy.deepcopy(fullpath)
			if fullpath.endswith('.bak') is True:
				fullpath = fullpath[:-4]
			ext = Path(fullpath).suffix
			if ext == '':
				return False
			for rex in self.wordList:
				if rex.search(ext) is not None:
					return True
		elif self.matchLocation == MatchLoc.FilePath:
			for rex in self.wordList:
				if rex.search(fullpath) is not None:
					return True
		elif self.matchLocation == MatchLoc.FileLength:
			if size == self.matchLength:
				return True
		return False

	def determine_action(self, smbfile, fullpath:str=None, name:str=None, size:int=None, **kwargs):
		if self.match(smbfile, fullpath=fullpath, name=name, size=size, **kwargs) is False:
			return None, None
		return self.matchAction, self.triage