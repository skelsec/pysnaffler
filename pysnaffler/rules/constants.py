import enum


class EnumerationScope(enum.Enum):
    ShareEnumeration = 'ShareEnumeration'
    DirectoryEnumeration = 'DirectoryEnumeration'
    FileEnumeration = 'FileEnumeration'
    ContentsEnumeration = 'ContentsEnumeration'


class MatchLoc(enum.Enum):
    ShareName = 'ShareName'
    FilePath = 'FilePath'
    FileName = 'FileName'
    FileExtension = 'FileExtension'
    FileContentAsString = 'FileContentAsString'
    FileContentAsBytes = 'FileContentAsBytes'
    FileLength = 'FileLength'
    FileMD5 = 'FileMD5'


class MatchListType(enum.Enum):
    Exact = 'Exact'
    Contains = 'Contains'
    Regex = 'Regex'
    EndsWith = 'EndsWith'
    StartsWith = 'StartsWith'


class MatchAction(enum.Enum):
    Discard = 'Discard'
    SendToNextScope = 'SendToNextScope'
    Snaffle = 'Snaffle'
    Relay = 'Relay'
    CheckForKeys = 'CheckForKeys'
    EnterArchive = 'EnterArchive'


class Triage(enum.Enum):
    Black = 'Black'
    Green = 'Green'
    Yellow = 'Yellow'
    Red = 'Red'
    Gray = 'Gray'
