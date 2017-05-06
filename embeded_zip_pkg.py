#!/usr/bin/env python2

import base64
import io
import os
import re
import sys
import textwrap
import zipfile

def zip_package(zfh, pkg_dir):
    pkg_name = os.path.basename(pkg_dir)

    for root, dirs, files in os.walk(pkg_dir):
        fpath = [os.path.join(root, fn) for fn in files]
        for fp in fpath:
            zpath = re.sub('^' + pkg_dir, pkg_name, fp)
            zfh.write(fp, zpath)


def gen_embeded_zipped_data(pkg_dirs):
    zfio = io.BytesIO()
    with zipfile.ZipFile(zfio, 'w', zipfile.ZIP_DEFLATED) as zfh:
        for d in pkg_dirs:
            zip_package(zfh, d)

    data = zfio.getvalue()
    return base64.b64encode(data)


def gen_py_code(zipdata_b64, pkg_names):
    print '''\
#!/usr/bin/env python2

import base64
import imp
import io
import os
import sys
import zipfile

class EZImport(object): #{{{{{{

    # Embeded {} package(s), zipped then encoded with base64
    EZ_DATA = \'\'\'
{}
\'\'\'

    class ZipImporter(object): #{{{{{{
        def __init__(self, zip_file):
            self.z = zip_file
            self.zfile = zipfile.ZipFile(self.z)
            self._paths = [x.filename for x in self.zfile.filelist]

        def _mod_to_paths(self, fullname):
            py_filename = fullname.replace('.', os.sep) + '.py'
            py_package = fullname.replace('.', os.sep, fullname.count('.') - 1) + '/__init__.py'
            if py_filename in self._paths:
                return py_filename
            elif py_package in self._paths:
                return py_package
            else:
                return None

        def find_module(self, fullname, path):
            if self._mod_to_paths(fullname):
                return self
            else:
                return None

        def load_module(self, fullname):
            filename = self._mod_to_paths(fullname)
            if not filename in self._paths:
                raise ImportError(fullname)
            zfh = self.zfile.open(filename)
            code = zfh.read()
            ispkg = filename.endswith('__init__.py')
            mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
            mod.__file__ = filename
            mod.__loader__ = self
            if ispkg:
                mod.__path__ = []
                mod.__package__ = fullname
            else:
                mod.__package__ = fullname.rpartition('.')[0]
            exec(code, mod.__dict__)
            return mod
    #}}}}}}

    def __new__(cls, *args, **kwargs):
        if cls.EZ_DATA:
            data = base64.b64decode(cls.EZ_DATA)
            zipbytes = io.BytesIO(data)
            sys.meta_path.insert(0, cls.ZipImporter(zipbytes))
            cls.EZ_DATA = None
        return super(EZImport, cls).__new__(cls, *args, **kwargs)

    def __init__(self, pkgname):
        exec('global %s; import %s;' % (pkgname, pkgname))
#}}}}}}

if __name__ == '__main__':\
'''.format(','.join(pkg_names), zipdata_b64)

    for pkg in pkg_names:
        print '''\
    EZImport('{}')\
'''.format(pkg)

    print '''
# TODO: YOUR CODE HERE ...

# vim: set fdm=marker:
'''

#------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('USAGE: ./embeded_zip_pkg.py pkg_dir pkg_dir ...')

    for d in sys.argv[1:]:
        if not os.path.isdir(d):
            sys.exit('[FATAL] %s is an invalid package directory!' % d)

    pkg_dirs = [os.path.normpath(p) for p in sys.argv[1:]]

    zdata_b64 = gen_embeded_zipped_data(pkg_dirs)

    pkg_names = [os.path.basename(d) for d in pkg_dirs]

    gen_py_code(zdata_b64, pkg_names)

