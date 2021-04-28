# Minimal Disk Image
# base : https://raw.githubusercontent.com/weldr/lorax/master/docs/fedora-docker.ks

# Use network installation
url --url="http://fedora.riscv.rocks/repos-dist/rawhide/latest/riscv64/"

# Root password
rootpw --plaintext replace-this-pw
# Network information
network  --bootproto=dhcp --activate
# System keyboard
keyboard --xlayouts=us --vckeymap=us
# System language
lang en_US.UTF-8
# SELinux configuration
selinux --enforcing
# Installation logging level
logging --level=info
# Shutdown after installation
shutdown
# System timezone
timezone  US/Eastern
# System bootloader configuration
bootloader --disabled
# Partition clearing information
clearpart --all --initlabel
# Disk partitioning information
part / --fstype="ext4" --size=3000

%post
# Remove random-seed
rm /var/lib/systemd/random-seed
%end

%packages --nocore --instLangs en
httpd
-kernel
%end
