import pysvn

if __name__ == "__main__":
    # the py2exe wrapper for this test doesn't pick up the svn
    # lib installed with pysvn so it can report a different
    # version number, so just make sure we can get the version
    # number and that the major version is the same
    print pysvn.version[0]
