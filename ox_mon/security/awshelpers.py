"""Helpers for working with AWS.
"""

import re
import subprocess
import json
import logging
import typing
import ipaddress


CIDR_RE = re.compile(
    r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$')


def make_deny_rule(profile: str, nacl_id: str,
                   rule_num: typing.Union[str, int], cidr: str,
                   cidr_dict: dict) -> typing.List[str]:
    """Make an AWS command line to create a deny rule.

    :param profile:    String profile to use for AWS CLI

    :param nacl_id:    The Network ACL ID for the rule.

    :param rule_num:   String or integeer indicating an integer rule
                       number that is not in use.

    :param cidr:       The CIDR for the address to block.

    :param cidr_dict:  A dictionary where keys are strings indicating
                       CIDR for rules we already have and values are the
                       current rules. Used to make sure we do not create
                       a duplicate/conflicting rule for an existing CIDR.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  List of strings representing command line.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Help create command line for making a deny rule.

The following illustrates example usage:

>>> cmd_line = make_deny_rule(
...    'example_profile', 'example_nacl', 5, '12.34.56.78/32', {})
>>> print((r'%c  '%10).join(cmd_line))
aws
  --profile
  example_profile
  ec2
  create-network-acl-entry
  --protocol
  -1
  --ingress
  --network-acl-id
  example_nacl
  --rule-number
  5
  --cidr-block
  12.34.56.78/32
  --rule-action
  deny

    """
    if not CIDR_RE.match(cidr.strip()):
        raise ValueError('Invalid CIDR: %s' % str(cidr))
    existing = cidr_dict.get(cidr, None)
    assert nacl_id is not None, 'Must provide nacl_id'
    if existing:
        msg = 'Refusing to replace existing rule for cidr %s: %s' % (
            cidr, existing)
        raise ValueError(msg)

    skeleton = make_skeleton(cidr, rule_num)
    cmd = ['aws', '--profile', profile, 'ec2',
           'create-network-acl-entry', '--protocol', skeleton['Protocol'],
           '--network-acl-id', nacl_id,
           '--rule-number', str(skeleton['RuleNumber']),
           '--cidr-block', skeleton['CidrBlock'],
           '--rule-action', skeleton['RuleAction']]
    if skeleton['Egress'] is False:
        cmd.append('--ingress')
    elif skeleton['Egress'] is True:
        cmd.append('--egress')
    else:
        raise ValueError('Invalid value for Egress in %s' % str(skeleton))
    return cmd


def make_skeleton(cidr, rule_num, egress=False, protocol=-1, action='deny'):
    """Helper to make a dictionary skeleton for a deny rule.
    """
    return {
        'CidrBlock': cidr, 'Egress': egress, 'Protocol': str(protocol),
        'RuleAction': action, 'RuleNumber': int(rule_num)}


def deny(block_file: str, nacl_id: str, vpc: str, profile: str,
         rule_start: str, dry_run: bool = False,
         max_dup_num: int = 0) -> typing.List[str]:
    """Issue AWS CLI commands to create deny rules for CIDRs in block_file.

    :param block_file:   Path to file with one CIDR per line representing
                         addresses to block.

    :param nacl_id:      Network ACL ID.

    :param vpc:          VPC name.

    :param profile:    String profile to use for AWS CLI

    :param rule_start:   String or integer representing rule number to
                         start with.

    :param dry_run=False:    If True, do not actually block anything.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  List of strings indicating results from attempting blocks.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  This method takes a `block_file` indicating CIDRs to block,
              calls make_deny_rule to create a deny rule for each CIDR
              in that file, and and uses the AWS CLI to execute the rules.
              The end result is you will end up with a set of deny rules
              for all CIDRs in block_file.
    """
    result = []
    cidr_dict = {}
    rule_nums = {}
    for entry in get_nacl_data(profile, vpc, nacl_id)['Entries']:
        logging.debug('Processing entry: %s', str(entry))
        cidr_dict[entry['CidrBlock']] = entry
        rule_nums[entry['RuleNumber']] = entry
    valid, problems = validate_proposed_rules(
        open(block_file).readlines(), cidr_dict, max_dup_num=max_dup_num)
    if problems:
        raise ValueError('No action taken due to %i problems:\n%s' % (
            len(problems), '\n----------------\n'.join(problems)))
    logging.info('Preparing to create new rules')
    for entry in valid:
        rule_start = get_empty_rule_num(rule_start, rule_nums)
        rule = make_deny_rule(profile, nacl_id, rule_start, entry,
                              cidr_dict)
        if dry_run:
            msg = 'Dry run: skip command:\n  %s' % str(rule)
            logging.debug(msg)
            result.append(msg)
        else:
            msg = 'Creating rule %s' % str(rule)
            logging.debug(msg)
            outcome = subprocess.check_output(rule)
            if hasattr(outcome, 'decode'):
                outcome = outcome.decode('utf8')
            msg = 'Rule %s has outcome "%s"' % (rule, outcome)
            result.append(msg)
        rule_nums[rule_start] = rule

    return result


def get_empty_rule_num(rule_start: int, rule_nums: dict) -> int:
    """Helper to start from `rule_start` and find empty spot not in rule_nums.
    """
    while rule_start in rule_nums:
        rule_start += 1
    return rule_start


def validate_proposed_rules(new_rules: typing.List[str], cidr_dict: dict,
                            max_dup_num):
    """Validate

    :param new_rules:     List of strings indicating CIDRs to block.

    :param cidr_dict:  A dictionary where keys are strings indicating
                       CIDR for rules we already have and values are the
                       current rules. Used to make sure we do not create
                       a duplicate/conflicting rule for an existing CIDR.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  Pair of lists (valid, problems) indicating valid and problematic
              CIDRs.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Validate list of CIDRs to make into deny rules.

    """
    valid = []
    problems = []
    for i, line in enumerate(new_rules):
        line = line.strip()
        if not line or (line[0] and line[0] in ('#', ';')):
            logging.debug('Skip line %i: %s', i, line)
            continue
        else:
            cidr = line
        try:
            ipaddress.ip_network(cidr, strict=True)
        except Exception as problem:
            msg = '\n'.join([
                'Problem converting cidr %s to ip network: %s' % (
                    cidr, str(problem)),
                'Note that if you do not provide a valid IP CIDR (e.g.,',
                'if you have host bits set in the CIDR), then ',
                'duplicate checking may not work. Only provide valid',
                'CIDRs or use a tool to clean your CIDRs.'])
            logging.error(msg)
            raise
        existing = cidr_dict.get(cidr)
        if existing:
            if existing['RuleNumber'] <= max_dup_num:
                skeleton = make_skeleton(cidr, existing['RuleNumber'])
                if skeleton == existing:
                    logging.info('Skip duplicate %s', str(skeleton))
                    continue
            msg = '\n'.join([
                'Cidr from rule %i in matches existing:' % i,
                'Rule from line %i: %s' % (i, cidr),
                'Existing rule: %s' % str(existing),
                'Remove existing rule first to prevent confusion or',
                'increase max_dup_num argument'])
            problems.append(msg)
        else:
            valid.append(cidr)
    return valid, problems


def run_cmd(cmd, preamble=''):
    """Run a simple command using subprocess.check_output

    :param cmd:  List of str as command input for subprocess.check_output

    :param preamble='':   Optional string message to use in logging.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  Result of subprocess.check_output(cmd)

    """
    logging.info('%sRunning command:\n%s\n', preamble, ' '.join(cmd))
    result = subprocess.check_output(cmd)
    return result


def get_nacl_data(profile, vpc, nacl_id=None):
    """Get data for Network ACL.

    :param profile:    String profile to use for AWS CLI

    :param vpc:        AWS Virtual Private Cloud.

    :param nacl_id=None:     AWS Network ACL ID. If None, then there must
                             only be once Network ACL in the vpc.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  Data about the desired Network ACL.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  Get data about the network ACL.

    """
    cmd = ['aws', '--profile', profile, 'ec2', 'describe-network-acls',
           '--filters', 'Name=vpc-id,Values=%s' % vpc]
    result = run_cmd(cmd, 'Need info. ')
    data = json.loads(result.decode('utf8'))
    if nacl_id is None:
        if len(data['NetworkAcls']) != 1:
            raise ValueError('Could not find unique network ACL')
        return data['NetworkAcls'][0]

    filtered = [d for d in data['NetworkAcls']
                if d['NetworkAclId'] == nacl_id]
    if filtered:
        assert len(filtered) == 1
        return filtered[0]
    raise ValueError('No match to network ACL %s' % str(nacl_id))
