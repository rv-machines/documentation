# Standard Fedora image with python3 and dnf
#
# https://raw.githubusercontent.com/weldr/lorax/master/docs/fedora-docker.ks
# https://pagure.io/fedora-kickstarts/tree/f33
# http://fedora.riscv.rocks:3000/davidlt/fedora-riscv-kickstarts/
#
# Make a flat Kickstart :
# wget https://pagure.io/fedora-kickstarts/raw/f33/f/fedora-container-common.ks
# wget https://pagure.io/fedora-kickstarts/raw/f33/f/fedora-container-base.ks
# ksflatten -c fedora-container-base.ks -o fedora-container.ks

# Use network installation
url --url="http://fedora.riscv.rocks/repos-dist/rawhide/latest/riscv64/"

# System timezone
timezone Etc/UTC --utc --nontp

# Root password
rootpw --iscrypted --lock locked

# System keyboard
keyboard 'us'

# Network information
network --bootproto=dhcp --device=link --activate

# Shutdown after installation
shutdown

# System language
lang en_US.UTF-8

# SELinux configuration
selinux --enforcing

# Installation logging level
logging --level=info

# System bootloader configuration
bootloader --disabled
# boot partitions are irrelevant as the final docker image is a tarball
zerombr
clearpart --all
autopart --noboot --nohome --noswap --nolvm

%packages --excludedocs --nocore --inst-langs=en --exclude-weakdeps
bash
coreutils
dnf
dnf-yum
dnf-plugins-core
fedora-release-container
fedora-repos-modular
glibc-minimal-langpack
rootfiles
rpm
shadow-utils
sssd-client
sudo
tar
util-linux
vim-minimal
-cracklib-dicts
-dosfstools
-e2fsprogs
-fuse-libs
-glibc-langpack-en
-gnupg2-smime
-grubby
-kernel
-langpacks-en
-libss
-pinentry
-shared-mime-info
-trousers
-xkeyboard-config

%end

%post --erroronfail --log=/root/anaconda-post.log
set -eux

# Disable default repositories (not riscv64 in upstream)
dnf config-manager --set-disabled rawhide updates updates-testing fedora fedora-modular fedora-cisco-openh264 updates-modular updates-testing-modular rawhide-modular

dnf -y remove dracut-config-generic

# Create Fedora RISC-V repo
cat << EOF > /etc/yum.repos.d/fedora-riscv.repo
[fedora-riscv]
name=Fedora RISC-V
baseurl=http://fedora.riscv.rocks/repos-dist/rawhide/latest/riscv64/
enabled=1
gpgcheck=0

[fedora-riscv-debuginfo]
name=Fedora RISC-V - Debug
baseurl=http://fedora.riscv.rocks/repos-dist/rawhide/latest/riscv64/debug/
enabled=0
gpgcheck=0

[fedora-riscv-source]
name=Fedora RISC-V - Source
baseurl=http://fedora.riscv.rocks/repos-dist/rawhide/latest/src/
enabled=0
gpgcheck=0
EOF

# Create Fedora RISC-V Koji repo
cat << EOF > /etc/yum.repos.d/fedora-riscv-koji.repo
[fedora-riscv-koji]
name=Fedora RISC-V Koji
baseurl=http://fedora.riscv.rocks/repos/rawhide/latest/riscv64/
enabled=0
gpgcheck=0
EOF

%end

%post --erroronfail --log=/root/anaconda-post.log
set -eux

# Set install langs macro so that new rpms that get installed will
# only install langs that we limit it to.
LANG="en_US"
echo "%_install_langs $LANG" > /etc/rpm/macros.image-language-conf

# https://bugzilla.redhat.com/show_bug.cgi?id=1727489
echo 'LANG="C.UTF-8"' >  /etc/locale.conf

echo "# fstab intentionally empty for containers" > /etc/fstab

# Remove machine-id on pre generated images
rm -f /etc/machine-id
touch /etc/machine-id

# remove random seed, the newly installed instance should make it's own
rm -f /var/lib/systemd/random-seed

%end

%post --erroronfail --log=/root/anaconda-post.log
# remove some extraneous files
rm -rf /var/cache/dnf/*
rm -rf /tmp/*

# https://pagure.io/atomic-wg/issue/308
printf "tsflags=nodocs\n" >>/etc/dnf/dnf.conf


# https://bugzilla.redhat.com/show_bug.cgi?id=1343138
# Fix /run/lock breakage since it's not tmpfs in docker
# This unmounts /run (tmpfs) and then recreates the files
# in the /run directory on the root filesystem of the container
#
# We ignore the return code of the systemd-tmpfiles command because
# at this point we have already removed the /etc/machine-id and all
# tmpfiles lines with %m in them will fail and cause a bad return
# code. Example failure:
#   [/usr/lib/tmpfiles.d/systemd.conf:26] Failed to replace specifiers: /run/log/journal/%m
#
umount /run
rm /run/nologin # https://pagure.io/atomic-wg/issue/316

# Final pruning
rm -rfv /var/cache/* /var/log/* /tmp/*

%end

%post --nochroot --erroronfail --log=/mnt/sysimage/root/anaconda-post-nochroot.log
set -eux

# See: https://bugzilla.redhat.com/show_bug.cgi?id=1051816
# NOTE: run this in nochroot because "find" does not exist in chroot
KEEPLANG=en_US
for dir in locale i18n; do
    find /mnt/sysimage/usr/share/${dir} -mindepth  1 -maxdepth 1 -type d -not \( -name "${KEEPLANG}" -o -name POSIX \) -exec rm -rfv {} +
done

%end
