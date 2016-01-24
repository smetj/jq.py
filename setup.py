#!/usr/bin/env python

import os
import platform
import subprocess
import tarfile
import shutil
from Cython.Build import cythonize

try:
    import sysconfig
except ImportError:
    # Python 2.6
    from distutils import sysconfig

from setuptools import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve


def path_in_dir(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


tarball_path = path_in_dir("_jq-lib-1.5.tar.gz")
jq_lib_dir = path_in_dir("jq-jq-1.5")

onig_tarball_path = path_in_dir("_onig.tar.gz")
onig_lib_dir = path_in_dir("onig-5.9.6")


def build_onig():

        if os.path.exists(onig_tarball_path):
            os.unlink(onig_tarball_path)
        urlretrieve("https://github.com/kkos/oniguruma/releases/download/v5.9.6/onig-5.9.6.tar.gz", onig_tarball_path)

        if os.path.exists(onig_lib_dir):
            shutil.rmtree(onig_lib_dir)
        tarfile.open(onig_tarball_path, "r:gz").extractall(path_in_dir("."))

        def command(args, cwd):
            print("")
            print("#" * 15)
            print("# Executing: %s" % ' '.join(args))
            print("#" * 15)
            print("")
            subprocess.check_call(args, cwd=cwd)

        command(['./configure', 'CFLAGS=-fPIC', '--prefix=%s/%s' % (os.getcwd(), onig_lib_dir)], cwd=onig_lib_dir)
        command(['/usr/bin/make'], cwd=onig_lib_dir)
        command(['/usr/bin/make', 'install'], cwd=onig_lib_dir)


class jq_build_ext(build_ext):
    def run(self):

        build_onig()
        if os.path.exists(tarball_path):
            os.unlink(tarball_path)
        urlretrieve("https://github.com/stedolan/jq/archive/jq-1.5.tar.gz", tarball_path)

        if os.path.exists(jq_lib_dir):
            shutil.rmtree(jq_lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(path_in_dir("."))

        def command(args):
            print("")
            print("#" * 15)
            print("# Executing: %s" % ' '.join(args))
            print("#" * 15)
            print("")
            subprocess.check_call(args, cwd=jq_lib_dir)

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = macosx_deployment_target

        #Nasty hack, ... no idea why this needs to be done manually, ...
        command(["cython", "../jq.pyx"])
        command(["autoreconf", "-i"])
        command(["./configure", "CFLAGS=-fPIC", "--disable-maintainer-mode", "--with-oniguruma=%s/%s" % (os.getcwd(), onig_lib_dir)])
        command(["make"])

        build_ext.run(self)


jq_extension = Extension(
    "jq",
    sources=["jq.c"],
    include_dirs=[jq_lib_dir, "%s/lib" % (onig_lib_dir)],
    extra_objects=[os.path.join(jq_lib_dir, ".libs/libjq.a"), os.path.join(onig_lib_dir, ".libs/libonig.a")],
    )

setup(
    name='jq',
    version='0.1.6',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=read("README.rst"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/jq.py',
    zip_safe=False,
    license='BSD 2-Clause',
    ext_modules = [jq_extension],
    cmdclass={"build_ext": jq_build_ext},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)

