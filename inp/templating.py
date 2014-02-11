def bash_style_replace(env, contents):
    """
    >>> bash_style_replace({'a': 12}, "$a")
    '12'
    """
    for k, v in env.iteritems():
        contents = contents.replace("$" + k, "%s" % v)
    return contents