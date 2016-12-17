# Rockstor ISO creation process
A new Rockstor ISO can be created from an existing one by running the
`make_iso.py` script. 

## Rebase CentOS
A Rockstor ISO is a CentOS ISO remastered with our artwork, installer modifications and custom packages. As of this writing it's based on CentOS 7, the 1511 ISO file.

## make_iso script
make_iso script can be invoked to use an existing Rockstor ISO as a seed and create a new one with updated packages including upstream updates as well as custom packages from us and elrepo. The script itself should be run on a Rockstor or a CentOS machine. It's easier to run it on Rockstor as custom repos are already setup. Follow these steps on that machine to create a new/updated ISO.

* Exract the iso to a directory. eg: /mnt/riso:
```
 mkdir -p /mnt/riso; mount /path/to/Rockstor.iso /mnt/riso
```
* Run make_iso:
```
/path/to/make_iso.py /mnt/riso
```
The script will take a while to compute package dependencies and download all available updates. The newly created ISO is dropped in `/tmp/Rockstor-efi.iso`.

* `--repeat` flag:

make_iso also support a flag for repeat ISO creation where packages are not downloaded again. This is useful if you make changes to certain files like the kickstart file or grub etc.. and know that there won't be any package updates since the last run a few moments ago. Here's an example invocation: `/path/to/make_iso.py /mnt/riso --repeat`
