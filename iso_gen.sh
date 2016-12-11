#!/bin/bash

createrepo -g repodata/c7-x86_64-comps.xml /tmp/vanilla/

mkisofs -U -A "Rockstor-3.8-0" -V "Rockstor 3 x86_64" \
    -volset "Rockstor-3.8-0" -J -joliet-long -r -v -T -x ./lost+found \
    -o /tmp/Rockstor-3.8-0.iso \
    -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 \
    -boot-info-table -eltorito-alt-boot -e images/efiboot.img -no-emul-boot /tmp/vanilla/

isohybrid /tmp/Rockstor-3.8-0.iso
implantisomd5 /tmp/Rockstor-3.8-0.iso


#artwork modification

rm -rf /tmp/sfs; mkdir /tmp/sfs
cp /tmp/vanilla/LiveOS/squashfs.img /tmp/sfs/
cd /tmp/sfs/; unsquashfs squashfs.img
rm -rf /mnt/rootfs; mkdir /mnt/rootfs; mount /tmp/sfs/squashfs-root/LiveOS/rootfs.img /mnt/rootfs/
#make changes

#sig images are in rnotes directory of pixmaps

#change eula location
usr/lib64/python2.7/site-packages/pyanaconda/constants.py:eulaLocation = "/usr/share/rockstor-release/EULA"

#remove user creation spokes, so there won't be an option to create a user during install.
rm /mnt/rootfs/usr/lib64/python2.7/site-packages/pyanaconda/ui/gui/spokes/user.py
rm /mnt/rootfs/usr/lib64/python2.7/site-packages/pyanaconda/ui/tui/spokes/user.py

#set buildstamp variables in this file
/mnt/rootfs/.buildstamp

umount /mnt/rootfs

cd /tmp/sfs; mksquashfs squashfs.img filesystem.squashfs -b 1024k -comp xz -Xbcj x86 -e boot
rm squashfs.img; mksquashfs squashfs-root squashfs.img -b 1024k -comp xz -Xbcj x86 -e boot
mv /tmp/sfs/squashfs.img /tmp/vanilla/LiveOS/squashfs.img
