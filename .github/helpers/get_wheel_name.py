import argparse
import warnings

from setuptools import Extension
from setuptools.dist import Distribution

def wheel_name(**kwargs):
    # create a fake distribution from arguments
    dist = Distribution(attrs=kwargs)
    # finalize bdist_wheel command
    bdist_wheel_cmd = dist.get_command_obj('bdist_wheel')
    bdist_wheel_cmd.ensure_finalized()
    # assemble wheel file name
    distname = bdist_wheel_cmd.wheel_dist_name
    tag = '-'.join(bdist_wheel_cmd.get_tag())
    return f'{distname}-{tag}.whl'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Return wheel name.')
    parser.add_argument('version', action='store', type=str, help='Version number.')
    args = parser.parse_args()

    warnings.simplefilter("ignore")
    print(wheel_name(name="py2exe", version=args.version, ext_modules=[Extension("py2exe.run", ["run.c"])]))
