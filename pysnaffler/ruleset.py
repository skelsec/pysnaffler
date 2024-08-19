from pysnaffler.rules.constants import EnumerationScope, MatchAction, MatchLoc, MatchListType, Triage
from typing import Dict, List, Tuple
from pysnaffler.rules.rule import SnaffleRule
from pathlib import PureWindowsPath
from glob import glob
from aiosmb.commons.interfaces.file import SMBFile
import hashlib

class SnafflerRuleSet:
	def __init__(self):
		self.shareEnumerationRules:Dict[str, SnaffleRule] = {}
		self.fileEnumerationRules:Dict[str, SnaffleRule] = {}
		self.directoryEnumerationRules:Dict[str, SnaffleRule] = {}
		self.contentsEnumerationRules:Dict[str, SnaffleRule] = {}
		self.allRules:Dict[str, SnaffleRule] = {}
		self.unrollCache:Dict[str, List[SnaffleRule]] = {}


	def enum_share(self, sharename) -> Tuple[bool, List[Triage]]:
		"""Returns True if the share should be enumerated, False if it should be discarded."""
		rules = []
		if sharename.startswith('\\\\') is False:
			sharename = '\\\\' + sharename
		for rule in self.shareEnumerationRules.values():
			action, triage = rule.determine_action(sharename)
			if action is MatchAction.Discard:
				return False, None
			if action is not None:
				rules.append(rule)
		return True, rules

	def enum_directory(self, directory) -> Tuple[bool, List[Triage]]:
		rules = []
		if directory.startswith('\\') is False:
			directory = '\\' + directory
		for rule in self.directoryEnumerationRules.values():
			action, triage = rule.determine_action(directory)
			if action is MatchAction.Discard:
				return False, None
			if action is not None:
				rules.append(rule)
		
		return True, rules
	
	def enum_file(self, filename) -> Tuple[bool, List[SnaffleRule]]:
		"""Returns True if the file should be enumerated, False if it should be discarded.
		Returns a list of rules that matched the file."""
		rules = []
		for rule in self.fileEnumerationRules.values():
			res, triage = rule.determine_action(filename)
			if res is None:
				continue
			if res == MatchAction.Discard:
				return False, [rule]
			else:
				rules.append(rule)

		# By default, we don't want to download files that don't match any rules
		if len(rules) == 0:
			return False, None
		
		return True, rules
			  
	def enum_unc(self, unc_path:str, fsize:int = None):
		unc = PureWindowsPath('\\\\\\\\' + unc_path.lstrip('\\'))
		share = unc.parts[2]
		shareres = self.enum_share(share)
		if shareres[0] is False:
			return False, []
		for x in unc.parts[2:-1]:
			dirres = self.enum_directory(x) 
			if dirres[0] is False:
				return False, []
		smbfile = SMBFile.from_uncpath(unc_path)
		smbfile.size = 1000 if fsize is None else int(fsize)
		to_dl, rules = self.enum_file(smbfile)
		if to_dl is False:
			return False, []
		rules = self.unroll_relays(rules)
		return True, rules

	def load_rule(self, rule):
		"""Adds a single rule to the ruleset"""
		self.allRules[rule.ruleName] = rule
		if rule.enumerationScope == EnumerationScope.ShareEnumeration:
			self.shareEnumerationRules[rule.ruleName] = rule
		elif rule.enumerationScope == EnumerationScope.DirectoryEnumeration:
			self.directoryEnumerationRules[rule.ruleName] = rule
		elif rule.enumerationScope == EnumerationScope.FileEnumeration:
			self.fileEnumerationRules[rule.ruleName] = rule
		elif rule.enumerationScope == EnumerationScope.ContentsEnumeration:
			self.contentsEnumerationRules[rule.ruleName] = rule

	def load_rules(self, rules:List[SnaffleRule]):
		"""Adds all rules from a list of rules"""
		for rule in rules:
			self.load_rule(rule)

	def load_rule_file(self, fpath):
		"""Adds all rules from a single file"""
		with open(fpath, 'r') as file:
			data = file.read()
			self.load_rules(SnaffleRule.from_toml(data))
	
	def load_directory(self, directory):
		"""Adds all rules from a directory recursively"""
		for rulefilepath in glob(directory + '/**/*.toml', recursive=True):
			self.load_rule_file(rulefilepath)
	
	def to_dict(self):
		return {
			'shareEnumerationRules' : self.shareEnumerationRules,
			'fileEnumerationRules' : self.fileEnumerationRules,
			'directoryEnumerationRules' : self.directoryEnumerationRules,
			'contentsEnumerationRules' : self.contentsEnumerationRules,
			'allRules' : self.allRules
		}
	
	@staticmethod
	def from_dict(d):
		ruleset = SnafflerRuleSet()
		ruleset.shareEnumerationRules = d['shareEnumerationRules']
		ruleset.fileEnumerationRules = d['fileEnumerationRules']
		ruleset.directoryEnumerationRules = d['directoryEnumerationRules']
		ruleset.contentsEnumerationRules = d['contentsEnumerationRules']
		ruleset.allRules = d['allRules']
		return ruleset

	def pickle(self):
		"""Pickle the ruleset"""
		import pickle
		import gzip
		import base64
		return base64.b64encode(gzip.compress(pickle.dumps(self.to_dict())))
	
	@staticmethod
	def unpickle(pickled):
		"""Unpickle a ruleset"""
		import pickle
		import gzip
		import base64
		return SnafflerRuleSet.from_dict(pickle.loads(gzip.decompress(base64.b64decode(pickled))))

	@staticmethod
	def load_default_ruleset():
		from pysnaffler.rulefiles import get_default_ruleset
		return get_default_ruleset()

	@staticmethod
	def from_directory(dirpath):
		"""Load all rules from a directory recirsively"""
		ruleset = SnafflerRuleSet()
		ruleset.load_directory(dirpath)
		return ruleset

	@staticmethod
	def from_file(filepath):
		"""Load all rules from a single file"""
		ruleset = SnafflerRuleSet()
		ruleset.load_rule_file(filepath)
		return ruleset
	
	def unroll_relays(self, rules:List[SnaffleRule]) -> List[SnaffleRule]:
		lookupkey = ''
		for rule in rules:
			lookupkey += rule.ruleName
		if lookupkey in self.unrollCache:
			return self.unrollCache[lookupkey]

		finalrules = {}
		for rule in rules:
			if rule.matchAction == MatchAction.Relay:
				# I can only hope there won't be nested relays
				# or worse: recursive relays...
				for relay in rule.relayTargets:
					if relay in self.allRules:
						if relay not in finalrules:
							finalrules[relay] = self.allRules[relay]
						# keep it like this so we know which rule is already in the set
						# and which one is missing
					else:
						print('Rule %s has relay target %s which is not a valid rule' % (rule.ruleName, relay))
			else:
				finalrules[rule.ruleName] = rule
		self.unrollCache[lookupkey] = finalrules.values()
		return finalrules.values()

	async def parse_file(self, filepath, rules:List[SnaffleRule], fsize:int = 0):
		finalrules = self.unroll_relays(rules)
		for rule in finalrules:
			if rule.enumerationScope == EnumerationScope.ContentsEnumeration:
				res, err = rule.open_and_match(filepath)
				if err is not None:
					yield None, rule, err
				if res:
					yield res, rule, None
			else:
				temp = SMBFile.from_uncpath(filepath)
				temp.size = fsize
				tograb = rule.match(temp)
				if tograb is False:
					continue
				# maybe we'd need to be recursive here?
				# TODO: check if we need to be recursive here
				err = None
				res = ''
				yield res, rule, None

if __name__ == '__main__':
	ruleset = SnafflerRuleSet.load_default_ruleset()
	print(ruleset.pickle())