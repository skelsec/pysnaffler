from abc import ABC, abstractmethod

from aiosmb.commons.interfaces.machine import SMBMachine
from aiosmb.commons.interfaces.file import SMBFile

from anfs.protocol.nfs3.client import NFSAccessError, NFSFileEntry

class ProtocolClient(ABC):
	@abstractmethod
	def __init__(self, factory, target):
		pass

	@abstractmethod
	async def connect_to_target(self, target):
		pass

	@abstractmethod
	async def donwload_file(self, file, localpath, max_size):
		pass

	@abstractmethod
	async def enum_files_with_filter(self, filter):
		pass

class SMBProtocolClient(ProtocolClient):
	
	def __init__(self, factory, target):
		self.factory = factory
		self.target = target
		self.connection = None
		self.machine = None

	
	async def connect_to_target(self, target):
		self.connection = self.factory.create_connection_newtarget(target)
		_, err = await self.connection.login()
		if err is not None:
			raise err

		self.machine = SMBMachine(self.connection)

	
	async def donwload_file(self, file: SMBFile, localpath, max_size):
		return await file.download(self.connection, localpath)

	
	async def enum_files_with_filter(self, filter):
		async for obj, otype, err in self.machine.enum_files_with_filter(filter):
			yield obj, otype, err

class NFSProtocolClient(ProtocolClient):
	
	def __init__(self, factory, target):
		self.factory = factory
		self.target = target
		self.connection = None
		self.client = None
		self.newfactory = None

	
	async def connect_to_target(self, target):
		self.newfactory = self.factory.create_factory_newtarget(target)

	
	async def donwload_file(self, file, localpath, max_size):
		return await self.client.download_file(file.nfs_file.handle, localpath, max_size = max_size, uid = file.nfs_file.uid, gid = file.nfs_file.gid)

	@staticmethod
	def filter_wrapper(filter, target, mount_path):
		def filter_cb(entry_path, entry):
			smb_obj = entry.to_smbfile(target, mount_path, entry_path)
			return filter('dir', smb_obj)

		return filter_cb

	
	async def enum_files_with_filter(self, filter):
		async with self.newfactory.get_mount() as mount:
			mountpoints, err = await mount.export()
			if err is not None:
				yield None, None, err
				return

			mounts = {}
			for mountpoint in mountpoints:
				mounts[mountpoint.filesys] = mountpoint

			for mountpoint in mounts:
				yield mounts[mountpoint].to_smbshare(self.target), 'share', None

				mhandle, err = await mount.mount(mountpoint)
				if err is not None:
					continue

				filter_cb = NFSProtocolClient.filter_wrapper(filter, self.target, mountpoint)

				async with self.newfactory.get_client(mhandle) as nfs:
					self.client = nfs
					async for epath, etype, entry, err in nfs.enumall(0, depth=30, filter_cb = filter_cb):
						if err is not None and not isinstance(err, NFSAccessError):
							yield None, None, None, err
						elif isinstance(entry, NFSFileEntry):
							yield entry.to_smbfile(self.target, mountpoint, epath), etype, err

	async def __aenter__(self):
		return self
	
	async def __aexit__(self, exc_type, exc, tb):
		await self.client.disconnect()