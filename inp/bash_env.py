import re


LINE_RE=re.compile(r'^export (?P<variable>[^=]*)=(?P<value>[^=]*)$')


def to_lines(bash_lines):
    """
    >>> to_lines('')
    []
    """
    return [line for line in bash_lines.split('\n') if line]


def line_to_dict(line):
    """
    >>> line_to_dict('export SOMETHING=value')
    {'SOMETHING': 'value'}
    """
    match = re.match(LINE_RE, line)
    return {match.group('variable'): match.group('value')}


def bash_to_dict(bash_lines):
    """
    >>> bash_to_dict('export SOMETHING=value\\nexport OTHER=othervalue')['SOMETHING']
    'value'
    >>> bash_to_dict('export SOMETHING=value\\nexport OTHER=othervalue')['OTHER']
    'othervalue'
    """
    settings = {}
    for line in to_lines(bash_lines):
        settings.update(line_to_dict(line))
    return settings


def issues_with_line(line):
    """
    >>> issues_with_line('aa')
    ['The expected format for each line is: "export VARNAME=VALUE" found: "aa"']
    """
    match = LINE_RE.match(line)
    if not match:
        return ['The expected format for each line is: "export VARNAME=VALUE" found: "%s"' % line]


def bash_env_parsing_issues(bash_lines):
    """
    >>> bash_env_parsing_issues('\\n'.join(['stuff']))
    ['line 1: The expected format for each line is: "export VARNAME=VALUE"']
    """
    issues = []
    for idx, line in enumerate(to_lines(bash_lines)):
        line_issues = issues_with_line(line)
        if line_issues:
            issues.append('line %d: %s' % (idx + 1, ','.join(line_issues)))
    return issues
