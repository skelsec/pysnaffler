import asyncio
import logging

from aiosmb import logger
from aiosmb.commons.connection.factory import SMBConnectionFactory
from asysocks.unicomm.common.scanner.scanner import UniScanner
from asysocks.unicomm.common.scanner.targetgen import UniTargetGen

from pysnaffler.ruleset import SnafflerRuleSet
from pysnaffler.scanner import SnafflerScanner
from pysnaffler.snaffler import pySnaffler


async def amain():
    import argparse

    parser = argparse.ArgumentParser(description='Snaffler')
    parser.add_argument('-w', '--worker-count', type=int, default=100, help='Parallell count')
    parser.add_argument('--dl-per-machine', type=int, default=5, help='Max paralell downloads per machine')
    parser.add_argument('--dl-total', type=int, default=20, help='Max paralell downloads in total. Global limit')
    parser.add_argument('--maxfile', type=int, default=1024 * 1024 * 10, help='Max file size to download')
    parser.add_argument('-r', '--rules', help='Path to ruleset directory. If not set, default rules will be used.')
    parser.add_argument('-t', '--timeout', type=int, default=36000, help='Timeout for each connection. dangerous!')
    parser.add_argument('--no-progress', action='store_false', help='Disable progress bar')
    parser.add_argument('-o', '--out-file', help='Output file path.')
    parser.add_argument('-e', '--errors', action='store_true', help='Includes errors in output.')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='Dry run. Enumeration only, gives stats on what would be downloaded/checked etc.')
    parser.add_argument('-l', '--filelist', action='store_true',
                        help='Generates filelist file containing a list of files and folders enumerated')
    parser.add_argument('-k', '--keep-files', action='store_true', help='Keeps downloaded files on disk after parsing')
    parser.add_argument('-b', '--base-path', default='snaffler_downloads',
                        help='Base directory path for downloaded files')
    parser.add_argument('-c', '--config', help='Path to config file. Overrides all other options.')
    parser.add_argument('url', help='Connection string in URL format')
    parser.add_argument('targets', nargs='*', help='Hostname or IP address or file with a list of targets')
    args = parser.parse_args()

    if len(args.targets) == 0:
        print('No targets defined!')
        return

    logger.setLevel(logging.CRITICAL)

    connectionfactory = SMBConnectionFactory.from_url(args.url)
    timeout = args.timeout
    if args.config is not None:
        snaffler = pySnaffler.from_config_file(args.config)
    else:
        ruleset = SnafflerRuleSet.load_default_ruleset()
        if args.rules is not None:
            ruleset = SnafflerRuleSet.from_directory(args.rules)

        snaffler = pySnaffler(
            ruleset,
            args.maxfile,
            args.worker_count,
            args.dl_per_machine,
            args.dl_total,
            args.keep_files,
            args.base_path,
            args.dry_run,
            args.filelist
        )

    # print('Running config:')
    # print(snaffler.to_toml())
    executors = [SnafflerScanner(connectionfactory, snaffler)]
    tgen = UniTargetGen.from_list(args.targets)
    scanner = UniScanner('Snaffler', executors, [tgen], worker_count=args.worker_count, host_timeout=timeout)
    await scanner.scan_and_process(progress=args.no_progress, out_file=args.out_file, include_errors=args.errors)
    snaffler.print_stats()


def main():
    asyncio.run(amain())


if __name__ == '__main__':
    main()
