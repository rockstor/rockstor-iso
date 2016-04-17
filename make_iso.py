#!/usr/bin/env python

import os
import sys
import re
from os.path import isfile
import subprocess
import shutil

YD='/usr/bin/yumdownloader'
RPM='/usr/bin/rpm'
YUM='/usr/bin/yum'


def download_new_pkgs(pkg_dir, new_pkg_dir):
    #first let's update the cache and system.
    os.system('yum -y update')
    print ('yum update finished')
    for f in os.listdir(pkg_dir):
        fp = ('%s/%s' % (pkg_dir, f))
        if (isfile(fp) and f[-4:] == '.rpm'):
            p = subprocess.Popen([RPM, '-q', '-p', '--qf', '%{NAME}:%{VERSION}:%{RELEASE}', fp],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 shell=False)
            orpm_long_name, e = p.communicate()
            rpm_name = orpm_long_name.split(':')[0]
            p2 = subprocess.Popen([YUM, 'info', rpm_name], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=False)
            o, e = p2.communicate()
            nver = None
            nrel = None
            for l in o.split('\n'):
                if (re.match('Version', l) is not None):
                    nver = l.split(': ')[1].strip()
                elif (re.match('Release', l) is not None):
                    nrel = l.split(': ')[1].strip()
            nrpm_long_name = '%s:%s:%s' % (rpm_name, nver, nrel)

            if (orpm_long_name == nrpm_long_name):
                print ('No update available for rpm {}. Copying it over from {}'.format(rpm_name, pkg_dir))
                shutil.copy(fp, new_pkg_dir)
                continue

            print ('Current version {}. Downloading new version {}'.format(orpm_long_name, nrpm_long_name))
            p = subprocess.Popen([YD, '-x', '\*i686', '--destdir', new_pkg_dir,
                                  '--archlist=x86_64,noarch', rpm_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 shell=False)
            o, e = p.communicate()
            print ('Done. stdout: {} stderr: {}'.format(o, e))


def rm_686_pkgs(pkg_dir):
    for f in os.listdir(pkg_dir):
        if (re.search('i686.rpm$', f) is not None):
            fp = ('%s/%s' % (pkg_dir, f))
            print ('Removing %s' % fp)
            os.remove(fp)

def mkiso(build_dir):
    iso_fp = '/tmp/Rockstor-efi.iso'
    #non efi
    #os.system('/usr/bin/mkisofs -o %s -b isolinux/isolinux.bin -c isolinux/boot.cat --no-emul-boot --boot-load-size 4 --boot-info-table -r -R -J -v -T -V "Rockstor 3 x86_64" %s' % (iso_fp, build_dir))
    os.system('/usr/bin/mkisofs -U -A "Rockstor 3 x86_64" -V "Rockstor 3 x86_64" -volset "Rockstor 3 x86_64" -J -joliet-long -r -v -T -x ./lost+found -o %s -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e images/efiboot.img -no-emul-boot %s' % (iso_fp, build_dir))
    os.system('/usr/bin/isohybrid %s' % iso_fp)
    print ('isohybrid finished')
    os.system('/usr/bin/implantisomd5 %s' % iso_fp)
    print ('md5sum implanted')


def install_deps():
    os.system('%s install -y anaconda anaconda-runtime createrepo isomd5sum '
              'genisoimage rpmdevtools squashfs-tools syslinux' % YUM)


def create_repo(build_dir):
    repodata_dir = '%s/repodata' % build_dir
    oldcompfile = None
    for l in os.listdir(repodata_dir):
        if (re.search('-c7-x86_64-comps.xml$', l) is not None):
            oldcompfile = '%s/%s' % (repodata_dir, l)
        elif (re.search('-c7-x86_64-comps.xml.gz$', l) is not None):
            lfp = '%s/%s' % (repodata_dir, l)
            os.remove(lfp)
    if (oldcompfile is None):
        sys.exit('Couldnt find old comp file. This is critical error')

    compfile = '%s/repodata/c7-x86_64-comps.xml' % build_dir
    shutil.move(oldcompfile, compfile)
    print ('Moved %s to %s' % (oldcompfile, compfile))
    p = subprocess.Popen(['/usr/bin/createrepo', '-g', compfile, build_dir],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=False)
    o, e = p.communicate()
    print ("repodata created")


def main():
    if (len(sys.argv) == 1):
        sys.exit("Usage: %s <iso_build_directory>" % sys.argv[0])
    build_dir = sys.argv[1]
    print("Using %s as the iso build directory" % build_dir)

    pkg_dir = '%s/Packages' % build_dir
    if (not os.path.isdir(pkg_dir)):
        sys.exit("Packages directory %s does not exist." % rpm_dir)
    new_pkg_dir = '%s/newrpms' % build_dir
    os.system("/usr/bin/mkdir -p %s" % new_pkg_dir)

    install_deps()
    download_new_pkgs(pkg_dir, new_pkg_dir)
    rm_686_pkgs(new_pkg_dir)
    print ("All i686 packages removed")
    ttbl = '%s/TRANS.TBL' % pkg_dir
    shutil.copy(ttbl, new_pkg_dir)
    print ("copied %s to %s" % (ttbl, new_pkg_dir))
    bkp_dest = '/tmp/Packages'
    if (os.path.isdir(bkp_dest)):
        os.system('/usr/bin/rm -rf %s' % bkp_dest)
        print ('Removed %s' % bkp_dest)
    shutil.move(pkg_dir, bkp_dest)
    print ("%s moved to %s" % (pkg_dir, bkp_dest))
    shutil.move(new_pkg_dir, pkg_dir)
    print ("%s moved to %s" % (new_pkg_dir, pkg_dir))
    create_repo(build_dir)
    mkiso(build_dir)

if __name__ == '__main__':
    main()
