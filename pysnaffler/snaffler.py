import asyncio
from pysnaffler.ruleset import SnafflerRuleSet
from pysnaffler.utils import sizeof_fmt
from typing import List
import toml
import os

class pySnaffler:
	def __init__(self, ruleset:SnafflerRuleSet = None, max_file_size:int = 10485760, max_connections:int = 200, 
					max_downloads:int = 4, max_downloads_total:int = 20, keep_files:bool = False, 
					download_base_dir:str = './snaffler_downloads', dry_run:bool = False, gen_filelist:bool = False,
					chars_before_match:int = 0, chars_after_match:int = 0, nfs:bool = False):
		self.ruleset = ruleset
		self.download_base_dir = download_base_dir
		self.max_file_size = max_file_size
		self.max_connections = max_connections
		self.max_downloads = max_downloads
		self.max_downloads_total = max_downloads_total
		self.keep_files = keep_files
		self.dry_run = dry_run
		self.gen_filelist = gen_filelist
		self.chars_before_match = chars_before_match
		self.chars_after_match = chars_after_match
		self.nfs = nfs
		self.stat_fcnt = 0
		self.stat_fsize = 0
		self.stat_flarge = 0
		self.total_dl_semaphore = asyncio.Semaphore(self.max_downloads_total)

	def print_stats(self):
		if self.dry_run:
			print('Total files would\'ve been downloaded: %s Totaling %s Skipped %s files because of size constraints' % (self.stat_fcnt, sizeof_fmt(self.stat_fsize), self.stat_flarge))
			return
		
		print('Total files downloaded: %s Totaling %s Skipped %s files because of size constraints' % (self.stat_fcnt, sizeof_fmt(self.stat_fsize), self.stat_flarge))

	def to_dict(self):
		return {
			#'ruleset' : self.ruleset.to_dict(),
			'download_base_dir' : self.download_base_dir,
			'max_file_size' : self.max_file_size,
			'max_connections' : self.max_connections,
			'max_downloads' : self.max_downloads,
			'max_downloads_total' : self.max_downloads_total,
			'keep_files' : self.keep_files,
			'dry_run' : self.dry_run,
			'gen_filelist' : self.gen_filelist,
			'chars_before_match': self.chars_before_match,
			'chars_after_match': self.chars_after_match,
			'nfs': self.nfs
		}

	def to_toml(self):
		# serialize all the settings to a toml file
		return toml.dumps(self.to_dict())

	def clean_working_directory(self):
		for directory, subdirs, _ in os.walk(self.download_base_dir, topdown=False):
			for subdir in subdirs:
				path = os.path.join(directory, subdir)
				if len(os.listdir(path)) == 0:
					os.rmdir(path)

	@staticmethod
	def from_dict(d:dict):
		# deserialize from a dict
		if 'ruleset' not in d:
			d['ruleset'] = SnafflerRuleSet.load_default_ruleset()
		else:
			d['ruleset'] = SnafflerRuleSet.from_dict(d['ruleset'])
		return pySnaffler(
			d['ruleset'],
			d['download_base_dir'],
			d['max_file_size'],
			d['max_connections'],
			d['max_downloads'],
			d['max_downloads_total'],
			d['keep_files'],
			d['dry_run'],
			d['gen_filelist'],
			d['chars_before_match'],
			d['chars_after_match'],
			d['nfs']
		)

	@staticmethod
	def from_toml(toml_str:str):
		# deserialize from a toml string
		d = toml.loads(toml_str)
		return pySnaffler.from_dict(d)

	@staticmethod
	def from_config_file(config_file:str):
		# deserialize from a toml file
		with open(config_file, 'r') as f:
			return pySnaffler.from_toml(f.read())
