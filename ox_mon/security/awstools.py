"""Tools for working with AWS.
"""

import logging

from ox_mon.common import configs, interface
from ox_mon.security import awshelpers


class AWSShowRules(interface.OxMonTask):
    """Command to show existing AWS Network ACL rules.
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption('--vpc', type=str, help='AWS VPC ID'),
            configs.OxMonOption('--profile', help='AWS profile name'),
            ]
        return result

    def _do_task(self):
        kwargs = {n: getattr(self.config, n) for n in [
            'vpc', 'profile']}
        for name in ['vpc', 'profile']:
            if not kwargs[name]:
                raise ValueError('Must provide value for %s' % name)
        acl = awshelpers.get_nacl_data(**kwargs)
        entries = acl['Entries']
        return entries


class AWSBlockCmd(interface.OxMonTask):
    """Command to create deny rules to block access to AWS network.
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = AWSShowRules.options() + [
            configs.OxMonOption(
                '--block_file', help=(
                    'Path to file with IP address ranges to block')),
            configs.OxMonOption('--nacl_id', default=None, type=str, help=(
                'Network ACL ID to edit.')),
            configs.OxMonOption('--rule_start', default=1, type=int, help=(
                'Rule ID to start creating from')),
            configs.OxMonOption('--max_dup_num', default=0, type=int, help=(
                'Max rule number for duplicate rule.\n'
                'If a duplicate is found with a higher rule number than\n'
                'the --max_dup_num, then that is an error. This lets you\n'
                'skip duplicates if the duplicate is a low enough rule\n'
                'number but die if the rule number might be too high.')),
            configs.OxMonOption('--dry-run', default=False, type=bool, help=(
                'If True, do dry-run without with no actual effect.'))
            ]
        return result

    def _do_sub_cmd(self):
        kwargs = {n: getattr(self.config, n) for n in [
            'block_file', 'nacl_id', 'vpc', 'profile', 'rule_start',
            'dry_run', 'max_dup_num']}
        for name in ['vpc', 'profile', 'block_file', 'nacl_id']:
            if not kwargs[name]:
                raise ValueError('Must provide value for %s' % name)
        return awshelpers.deny(**kwargs)

    def _do_task(self):
        return self._do_sub_cmd()
