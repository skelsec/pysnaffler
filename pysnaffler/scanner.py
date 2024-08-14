import datetime
import asyncio
import traceback
from pathlib import Path
from typing import List
from asysocks.unicomm.common.scanner.common import *
from pysnaffler.rules.rule import SnaffleRule

from aiosmb.commons.interfaces.machine import SMBMachine
from aiosmb.commons.interfaces.file import SMBFile
from aiosmb.commons.connection.factory import SMBConnectionFactory
from aiosmb.examples.scanners.smbfile import SMBFileRes
from pysnaffler.snaffler import pySnaffler
from pysnaffler.utils import sizeof_fmt


class SnafflerResult:
	def __init__(self, otype:str, smbobj, rule:SnaffleRule, data:str or bytes = None):
		self.otype = otype
		self.smbobj = smbobj
		self.rule = rule
		self.data = data

	def get_name(self):
		return 'Snaffler'

	def get_fname(self):
		return self.smbobj.name

	def get_fdata(self):
		return None

	def data_to_line(self):
		# data needs to be one single line, so we replace newlines with spaces
		if self.data is None:
			return ''
		return str(self.data).replace('\r', '\\r').replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')

	def to_line(self):
		try:
			# tab separater line containing filename, rule triage color, file size, file size in human readable format,  file last modified date, full unc path, data.
			if self.otype == 'file':
				return '%s\t[File]\t%s\t%s\tR\t%s\t%s\t%s\t%s\t%s' % (datetime.datetime.utcnow().isoformat(), self.rule.triage.name, self.rule.ruleName, self.smbobj.size, sizeof_fmt(self.smbobj.size), self.smbobj.last_write_time.isoformat(), self.smbobj.unc_path, self.data_to_line())
			elif self.otype == 'dir':
				return '%s\t[Dir]\t%s\t%s\tR\t%s\t%s\t%s\t%s\t%s' % (datetime.datetime.utcnow().isoformat(), self.rule.triage.name, self.rule.ruleName, '0', '', '', self.smbobj.unc_path, '')
			elif self.otype == 'share': 
				return '%s\t[Share]\t%s\t%s\tR\t%s\t%s\t%s\t%s\t%s' % (datetime.datetime.utcnow().isoformat(), self.rule.triage.name, self.rule.ruleName, '0', '', '', self.smbobj.unc_path, '')
		except Exception as e:
			traceback.print_exc()
			raise e

class SnafflerScanner:
	"""This is an interface object for aiosmb's scanner"""
	def __init__(self, factory:SMBConnectionFactory, snaffler:pySnaffler):
		self.factory = factory
		self.snaffler = snaffler
		self.download_semaphore = asyncio.Semaphore(snaffler.max_downloads)
		self.download_tasks = []

	async def __filter_share_and_dir(self, otype, obj):
		"""Filter function for SMBMachine.enum_files_with_filter, this is the callback"""
		# return True to continue enumeration, False to stop
		try:                
			if otype == 'dir':
				return self.snaffler.ruleset.enum_directory(obj.fullpath)[0]
			if otype == 'share':
				return self.snaffler.ruleset.enum_share(obj.name)[0]
			elif otype == 'sharename':
				return self.snaffler.ruleset.enum_share(obj)[0]
			else:
				print('%s is not a share or directory' % otype)
			return True
		except Exception as e:
			traceback.print_exc()
			print('Error processing %s: %s' % (obj, e))
			return False

	async def download_file(self, connection, smbfile:SMBFile):
		try:
			async with self.snaffler.total_dl_semaphore:
				async with self.download_semaphore:
					localpath = SMBFile.prepare_mirror_path(self.snaffler.download_base_dir, smbfile.unc_path)
					localpath.mkdir(parents=True, exist_ok=True)
					fpath, err = await smbfile.download(connection, str(localpath))
					if err is not None:
						return None, err
					return fpath, None
		except Exception as e:
			return None, e

	async def process_file(self, connection, smbfile:SMBFile, matchingrules:List[SnaffleRule], targetid:str, target:str, out_queue:asyncio.Queue):
		fpath = None
		keep_file = False
		try:
			await out_queue.put(ScannerInfo(target, 'Downloading %s' % smbfile.unc_path))
			fpath, err = await self.download_file(connection, smbfile)
			if err is not None:
				await out_queue.put(ScannerInfo(target, 'Error downloading %s: %s' % (smbfile.unc_path, err)))
				return
			if fpath is None:
				# file got skipped
				return
			await out_queue.put(ScannerInfo(target, 'Processing %s' % smbfile.unc_path))
			async for data, rule, err in self.snaffler.ruleset.parse_file(fpath, matchingrules, smbfile.size):
				if err is not None:
					# error handling ?
					continue
				if data is None:
					continue
				
				keep_file = True
				await out_queue.put(ScannerData(target, SnafflerResult('file', smbfile, rule, data)))
			
		except Exception as e:
			print(e)
		finally:
			if fpath is not None and (self.snaffler.keep_files is False or keep_file is False):
				Path(fpath).unlink()	
	
	async def snaffle_machine(self, machine:SMBMachine, targetid:str, target:str, out_queue:asyncio.Queue):
		async for obj, otype, err in machine.enum_files_with_filter(self.__filter_share_and_dir):
			if err is not None:
				#print(err)
				continue
			if self.snaffler.gen_filelist is True:
				await out_queue.put(ScannerData(target, SMBFileRes(obj, otype, None)))

			if otype == 'file':
				
				tograb, matchingrules = self.snaffler.ruleset.enum_file(obj)
				if tograb is False:
					continue
				
				if obj.size > self.snaffler.max_file_size:
					self.snaffler.stat_flarge += 1
					for rule in matchingrules:
						await out_queue.put(ScannerData(target, SnafflerResult('file', obj, rule, 'Skipped due to file size constraints')))
					
					continue
				if obj.size == 0:
					continue

				self.snaffler.stat_fcnt += 1
				self.snaffler.stat_fsize += obj.size

				if self.snaffler.dry_run is True:
					continue

				await self.process_file(machine.connection, obj, matchingrules, targetid, target, out_queue)
			elif otype == 'dir':
				# at this point it sure matches to at least one rule
				tograb, rules = self.snaffler.ruleset.enum_directory(obj.fullpath)
				if tograb is False:
					continue
				for rule in rules:
					await out_queue.put(ScannerData(target, SnafflerResult('dir', obj, rule)))
			if otype == 'share':
				tograb, rules = self.snaffler.ruleset.enum_share(obj.name)
				if tograb is False:
					continue
				for rule in rules:
					await out_queue.put(ScannerData(target, SnafflerResult('share', obj, rule)))
	
	async def run(self, targetid, target, out_queue:asyncio.Queue):
		try:
			connection = self.factory.create_connection_newtarget(target)
			async with connection:
				_, err = await connection.login()
				if err is not None:
					raise err

				machine = SMBMachine(connection)
				await self.snaffle_machine(machine, targetid, target, out_queue)

		except asyncio.CancelledError:
			return
		except Exception as e:
			await out_queue.put(ScannerError(target, e))
