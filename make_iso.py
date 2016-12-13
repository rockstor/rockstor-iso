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
RQ='/usr/bin/repoquery'
WORKING_DIR='/root/vanilla'


rockstor_deps = {
    'NetworkManager-team': False,
    'at': False,
    'avahi': False,
    'btrfs-progs': False,
    'chrony': False,
    'cyrus-sasl-plain': False,
    'docker-engine': False,
    'epel-release': False,
    'firewalld': False,
    'hdparm': False,
    'kernel-ml': False,
    'kernel-ml': False,
    'krb5-workstation': False,
    'nano': False,
    'net-snmp': False,
    'net-tools': False,
    'netatalk': False,
    'nfs-utils': False,
    'nginx': False,
    'ntp': False,
    'nut': False,
    'nut-xml': False,
    'pciutils': False,
    'postfix': False,
    'postgresql': False,
    'postgresql-server': False,
    'python': False,
    'realmd': False,
    'rockstor-release': False,
    'rpcbind': False,
    'rsync': False,
    'samba': False,
    'samba-client': False,
    'samba-common': False,
    'samba-winbind': False,
    'samba-winbind-clients': False,
    'samba-winbind-krb5-locator': False,
    'shellinabox': False,
    'smartmontools': False,
    'sos': False,
    'systemtap-runtime': False,
    'usbutils': False,
    'ypbind': False,
    'yum-cron': False,
    'yum-plugin-changelog': False,
}

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
            #Mark the dependency satisfied.
            if rpm_name in rockstor_deps:
                rockstor_deps[rpm_name] = True
            #print ('rpm name: {}. errors: {}'.format(rpm_name, e))

            #p2 = subprocess.Popen([RPM, '-q', '--qf', '%{NAME}:%{VERSION}:%{RELEASE}', rpm_name],
            #                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            #nrpm_long_name, e = p2.communicate()
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

            #print ("new rpm long name = %s" % nrpm_long_name)
            if (orpm_long_name == nrpm_long_name):
                print ('No update available for rpm {}. Copying it over from {}'.format(rpm_name, pkg_dir))
                shutil.copy(fp, new_pkg_dir)
                continue

            print ('Current version {}. Downloading new version {}'.format(orpm_long_name, nrpm_long_name))
            download_rpm(rpm_name, new_pkg_dir)

    for p,s in rockstor_deps.items():
        print ("{} {}".format(p, s))
        if (not s):
            download_rpm(p, new_pkg_dir)


def download_rpm(name, destdir):
    print ('Downloading {}'.format(name))
    p = subprocess.Popen([YD, '-x', '\*i686', '--destdir', destdir,
                          '--archlist=x86_64,noarch', name],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=False)
    o, e = p.communicate()
    print ('Done. stdout: {} stderr: {}'.format(o, e))


def resolve_rockstor_deps():
    """Add transitive dependencies to rockstor_deps"""
    deps = {}
    for pkg in rockstor_deps:
        deps = transitive_dependencies(pkg, deps)
    rockstor_deps.update(deps)
    print rockstor_deps


def transitive_dependencies(pkg, deps={}):
    print ('computing transitive dependencies for {}'.format(pkg))
    p = subprocess.Popen([RQ, '--requires', '--resolve', '--qf', '%{NAME}',
                          pkg], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=False)
    o, e = p.communicate()
    for l in o.split('\n'):
        if len(l.strip()) == 0:
            continue
        if l not in deps:
            deps[l] = False
            transitive_dependencies(l, deps=deps)
    return deps


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


def update_squashfs():
    sfsdir = '/tmp/sfs'
    rfsdir = '/mnt/rootfs'
    os.system('rm -rf %s' % sfsdir)
    os.system('mkdir %s' % sfsdir)
    os.system('cp %s/LiveOS/squashfs.img %s' % (WORKING_DIR, sfsdir))
    os.system('cd %s && unsquashfs squashfs.img')
    os.system('rm -rf %s' % rfsdir)
    os.system('mkdir %s' % rfsdir)
    os.system('mount %s/squashfs-root/LiveOS/rootfs.img %s' % (sfsdir, rfsdir))

    #remove user creation spoke
    os.system('rm -f %s/usr/lib64/python2.7/site-packages/pyanaconda/ui/gui/spokes/user.py' % rfsdir)
    os.system('rm -f %s/usr/lib64/python2.7/site-packages/pyanaconda/ui/tui/spokes/user.py' % rfsdir)

    #set buildstamp variable in /mnt/rootfs/.buildstamp
    #code here...

    os.system('umount %s' % rfsdir)
    os.system('cd %s && mksquashfs squashfs.img filesystem.squashfs -b 1024k -comp xz -Xbcj x86 -e boot' % sfsdir)
    os.system('cd %s && rm -f squashfs.img && mksquashfs squashfs-root squashfs.img -b 1024k -comp xz -Xbcj x86 -e boot' % sfsdir)
    os.system('mv %s/squashfs.img %s/LiveOS/squashfs.img' % (sfsdir, rfsdir))


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
    os.system("/usr/bin/createrepo -g %s %s" % (compfile, build_dir))

def main():
    if (len(sys.argv) == 1):
        sys.exit("Usage: %s <iso_build_directory>" % sys.argv[0])
    build_dir = sys.argv[1]
    print("Using %s as the iso build directory" % build_dir)

    #resolve_rockstor_deps()
    #return

    if (len(sys.argv) < 3 or sys.argv[2] != '--repeat'):
        pkg_dir = '%s/Packages' % build_dir
        if (not os.path.isdir(pkg_dir)):
            sys.exit("Packages directory %s does not exist." % pkg_dir)
        new_pkg_dir = '%s/newrpms' % build_dir
        os.system("/usr/bin/mkdir -p %s" % new_pkg_dir)

        resolve_rockstor_deps()
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
