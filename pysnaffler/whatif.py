
import asyncio
import logging
from aiosmb.commons.connection.factory import SMBConnectionFactory
from pysnaffler.snaffler import pySnaffler
from pysnaffler.ruleset import SnafflerRuleSet
from aiosmb import logger

from tqdm import tqdm
import datetime
import codecs
import traceback
import sys
			

async def whatif(targets, config = None, rulesdir = None, url = None, is_aiosmb = False):
	logger.setLevel(logging.CRITICAL)

	if len(targets) == 0:
		print('No targets defined!')
		return
	
	connectionfactory = None
	if url is not None:
		connectionfactory = SMBConnectionFactory.from_url(url)
	
	ruleset = SnafflerRuleSet.load_default_ruleset()
	if rulesdir is not None:
		ruleset = SnafflerRuleSet.from_directory(rulesdir)
	
	snaffler = pySnaffler(ruleset, dry_run=True)
	if config is not None:
		snaffler = pySnaffler.from_config_file(config)
	
	
	
	print('Running config:')
	print(snaffler.to_toml())
	
	for target in targets:
		total_dl_size = 0
		files_to_dl = []
		print('Processing %s' % target)
		total = 0
		estart = datetime.datetime.now()
		with codecs.open(target, 'r','latin-1') as f:
			if is_aiosmb is True:
				for line in f:
					line = line.strip()
					if line == '':
						continue
					_, _, otype, *rest = line.split('\t')
					if otype != 'file':
						continue
					total += 1
			else:
				for line in f:
					total += 1
		eend = datetime.datetime.now()
		print('Took %s to count lines' % (eend-estart))

		estart = datetime.datetime.now()
		with codecs.open(target, 'r','latin-1') as f:
			for line in tqdm(f, total=total):
				try:
					line = line.strip()
					if line == '':
						continue
					if is_aiosmb is True:
						_, _, otype, uncpath, *rest = line.split('\t')
						if otype != 'file':
							continue
						try:
							fsize = rest[1]
						except:
							print('Error on line %s' % line)
							fsize = 0
					else:
						_, otype, uncpath, *rest = line.split('\t')
						if otype != 'file':
							continue
						fsize = rest[1]
					
					todl, rules = ruleset.enum_unc(uncpath, fsize)
					if todl is False:
						continue
					
					total_dl_size += int(fsize)
					rulenames = ','.join([r.ruleName for r in rules])
					files_to_dl.append((uncpath, fsize, rulenames))
				except Exception as e:
					print('Error processing %s: %s' % (line, e))
					traceback.print_exc()
					continue
		
		eend = datetime.datetime.now()
		print('Took %s to process' % (eend-estart))
		print('Total files to download: %s' % len(files_to_dl))
		print('Total size to download: %s' % total_dl_size)
	
	
	#snaffler.print_stats()

async def amain():
	import argparse

	parser = argparse.ArgumentParser(description='Snaffler-whatif.')
	parser.add_argument('-c', '--config', help='Path to config file. Overrides all other options.')
	parser.add_argument('-r', '--rules', help='Path to rules directory. Overrides all other options.')
	parser.add_argument('--aiosmb', action='store_true', help='Targets are in aiosmb format')
	parser.add_argument('--url', help = 'Connection string in URL format')
	parser.add_argument('targets', nargs='*', help = 'File containing a list of UNC file paths in "\\\\server\\share\\path\\file" format. One per line. Optionally, a file size can be appended to the line, separated by a tab. Example: "\\\\server\\share\\path\\file\t123456"')
	args = parser.parse_args()

	await whatif(args.targets, args.config, args.rules, args.url, args.aiosmb)


def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()