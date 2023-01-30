
from typing import List, Dict, Tuple
import toml
import re
from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage

class SnaffleRule:
	def __init__(self, enumerationScope, RuleName, matchAction, relayTargets, description, matchLocation, wordListType, matchLength, wordList, triage) -> None:
		self.enumerationScope:EnumerationScope = enumerationScope
		self.ruleName:str = RuleName
		self.matchAction:MatchAction = matchAction
		self.relayTargets:List[str] = relayTargets
		self.description:str = description
		self.matchLocation:MatchLoc = matchLocation
		self.wordListType:MatchListType = wordListType
		self.matchLength:int = matchLength
		self.wordList:List[re.Pattern] = wordList
		self.triage:Triage = triage
		self.__convert_wordlist()

	def __convert_wordlist(self):
		#convert wordlist to regex
		res = []
		for word in self.wordList:
			if self.wordListType == MatchListType.Regex:
				a=1
			elif self.wordListType == MatchListType.EndsWith:
				word = word + '$'
			elif self.wordListType == MatchListType.StartsWith:
				word = '^' + word
			elif self.wordListType == MatchListType.Contains:
				word = '.*' + word + '.*'
			elif self.wordListType == MatchListType.Exact:
				word = '^' + word + '$'
			res.append(re.compile(word, flags=re.IGNORECASE))
		self.wordList = res

	
	def match(self, data):
		for rex in self.wordList:
			if rex.search(data) is not None:
				return True
		return False

	def determine_action(self, data):
		if self.match(data) is False:
			return None, None
		return self.matchAction, self.triage
	
	def __repr__(self):
		return str(self.to_toml())
	
	def to_toml(self):
		return toml.dumps(self.to_dict())

	def to_dict(self):
		return {
			'EnumerationScope' : self.enumerationScope.value,
			'RuleName' : self.ruleName,
			'MatchAction' : self.matchAction.value,
			'RelayTargets' : self.relayTargets,
			'Description' : self.description,
			'MatchLocation' : self.matchLocation.value,
			'WordListType' : self.wordListType.value,
			'MatchLength' : self.matchLength,
			'WordList' : self.wordList,
			'Triage' : self.triage.value
		}

	@staticmethod
	def from_dict(datadict:Dict):
		from pysnaffler.rules.file import SnafflerFileRule
		from pysnaffler.rules.directory import SnafflerDirectoryRule
		from pysnaffler.rules.share import SnafflerShareRule
		from pysnaffler.rules.contents import SnafflerContentsEnumerationRule
		
		results = []
		if 'ClassifierRules' not in datadict:
			return []
		for d in datadict['ClassifierRules']:
			enumerationScope = EnumerationScope(d['EnumerationScope'])
			ruleName = d.get('RuleName', 'Unnamed Rule')
			matchAction = MatchAction(d['MatchAction'])
			relayTargets = d.get('RelayTargets', []) 
			description = d.get('Description', 'No description')
			matchLocation = MatchLoc(d['MatchLocation'])
			wordListType = MatchListType(d['WordListType'])
			matchLength = d.get('MatchLength', 0)
			wordList = d.get('WordList', [])
			triage = Triage(d.get('Triage', 'Gray'))
			if enumerationScope == EnumerationScope.FileEnumeration:
				obj = SnafflerFileRule
			elif enumerationScope == EnumerationScope.DirectoryEnumeration:
				obj = SnafflerDirectoryRule
			elif enumerationScope == EnumerationScope.ShareEnumeration:
				obj = SnafflerShareRule
			elif enumerationScope == EnumerationScope.ContentsEnumeration:
				obj = SnafflerContentsEnumerationRule
			else:
				raise NotImplementedError(f'EnumerationScope {enumerationScope} not implemented.')

			results.append(obj(enumerationScope, ruleName, matchAction, relayTargets, description, matchLocation, wordListType, matchLength, wordList, triage))
		return results

	@staticmethod
	def from_toml(data:str):
		# there is a problem how C# toml is being parsed, so we need to split the data to multiple parts
		def findentries(data:str):
			entry = ''
			for line in data.split('\n'):
				if line.strip().startswith('[[ClassifierRules]]'):
					if entry != '':
						yield entry
					entry = line+'\n'
					continue
				entry += line + '\n'
			yield entry
		results = []
		for entry in findentries(data):
			results.extend(SnaffleRule.from_dict(toml.loads(entry)))
		
		return results

