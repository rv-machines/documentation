# Fedora 33 Container on RISC-V

## Abstract

This guide will show you the steps of building a docker compliant container image (from *scratch*) based on `Fedora 33` for `RISC-V`.

## Introduction

Through this guide, we will build our own `fedora image` for the `RISC-V`. It requires `podman` to be installed and configured in the `Fedora 33 RSICV Developer` virtual machine.
From a `mocked` environment, we will generate a `rootfs` that we will use for building the container image `from scratch`.

## Requirements

On the `RISC-V` virtual machine, install and download the following **packages** :

``` bash
# Install mock package
dnf install mock

# Add 'riscv' to mock group
usermod -a -G mock riscv
```

Fetch the following **resources** :

``` bash
# Mock configuration
wget https://raw.githubusercontent.com/rv-machines/documentation/main/res/mock/fedora-rawhide-riscv64.cfg
mv fedora-rawhide-riscv64.cfg /etc/mock/

# Lorax Kickstart file
wget https://raw.githubusercontent.com/rv-machines/documentation/main/res/lorax/fedora-docker.ks
mv fedora-docker.ks /home/riscv/

# Anaconda RPMs for Fedora 33
wget http://fedora.riscv.rocks/kojifiles/packages/anaconda/33.25.4/1.0.riscv64.fc33/riscv64/anaconda-core-33.25.4-1.0.riscv64.fc33.riscv64.rpm
wget http://fedora.riscv.rocks/kojifiles/packages/anaconda/33.25.4/1.0.riscv64.fc33/riscv64/anaconda-tui-33.25.4-1.0.riscv64.fc33.riscv64.rpm
mv anaconda-core-33.25.4-1.0.riscv64.fc33.riscv64.rpm /home/riscv/
mv anaconda-tui-33.25.4-1.0.riscv64.fc33.riscv64.rpm /home/riscv/

# RISC-V Patch for pyanaconda
# TODO: upstream this patch
# src: https://github.com/rhinstaller/anaconda/blob/f33-release/pyanaconda/modules/storage/platform.py#L265
# src: https://github.com/storaged-project/blivet/blob/3.4-devel/blivet/arch.py
wget https://raw.githubusercontent.com/rv-machines/documentation/main/res/pyanaconda/f33-release/platform.py
```

## Make a rootfs

> Mock is a simple program that will build source RPMs inside a chroot. It doesn't do anything terribly 
> fancy other than populate a chroot with the contents specified by a configuration file.

We will use `mock` for building a `chroot`in order to build a *clean* `rootfs` using `livemedia-creator`.

``` bash
# Disable SELinux
sudo setenforce 0

# Switch to the build user
sudo su - riscv

# Go to HOME directory
cd ~/

# Make a directory for results matching the bind mount above
mkdir ~/results/

# Init the mock
mock -r fedora-rawhide-riscv64 --init

# Push Kickstart file
mock -r fedora-rawhide-riscv64 --copyin ./fedora-docker.ks /root/

# Install some more packages and anaconda
mock -r fedora-rawhide-riscv64 --install dracut-network tar lorax libblockdev-plugins-all
mock -r fedora-rawhide-riscv64 --install ./anaconda-core-33.25.4-1.0.riscv64.fc33.riscv64.rpm ./anaconda-tui-33.25.4-1.0.riscv64.fc33.riscv64.rpm

# Patch pyanaconda
mock -r fedora-rawhide-riscv64 --chroot rm /usr/lib64/python3.9/site-packages/pyanaconda/modules/storage/platform.py
mock -r fedora-rawhide-riscv64 --copyin ./platform.py /usr/lib64/python3.9/site-packages/pyanaconda/modules/storage/

# Make the rootfs
mock -r fedora-rawhide-riscv64 --chroot --enable-network -- \
  livemedia-creator --resultdir=/results/try-1 --image-only --make-tar --no-virt --ks /root/fedora-docker.ks --image-name=rootfs_fedora.tar.xz --project "Fedora Docker" --releasever "33"
```

The new `rootfs` will be located at `~/results/try-1/rootfs_fedora.tar.xz`. We will use this artifact for building our scratch image.

You can use `mock -r fedora-rawhide-riscv64 --shell` for entering an interactive shell inside the chroot.
The chroot filesystem can be accessed via : `/var/lib/mock/fedora-rawhide-riscv64/` from the host system.

## Building a scratch image

Go to `results` :

```
cd /home/riscv/results/try-1/
```

Unpack the `rootfs` :

```
xz -d rootfs_fedora.tar.xz
```

Let's create the `Dockerfile` for our fedora container image :

``` Dockerfile
FROM scratch
ADD rootfs_fedora.tar /
CMD ["/bin/bash"]
```

Time to build the image !

``` bash
podman build -t f33-riscv64 .
```

Test that it works :

``` bash
podman run -it --rm f33-riscv64 cat /etc/os-release
podman run --privileged -it --rm --entrypoint="/bin/bash" f33-riscv64
```

This image has been published on `quay.io`, you can pull and test it :

``` bash
# Pull
podman pull quay.io/nirousseau/f33-riscv64:latest
```

### Publishing to Quay.IO

``` bash
# Tag
podman tag f33-riscv64:latest quay.io/nirousseau/f33-riscv64:latest

# Push
podman push quay.io/nirousseau/f33-riscv64:latest
```

## Further reading and related works

This guide has been created and inspired by the following articles and blog posts :
 
 * [How to build Fedora container images](https://fedoramagazine.org/how-to-build-fedora-container-images/)
 * [Example - x86_64 Official Docker image for Fedora 33](https://github.com/fedora-cloud/docker-brew-fedora/tree/7b9d4b28443845a3e4e4e520a857fa2e9e52fb8e/x86_64)
 * [weldr.io - livemedia-creator](https://weldr.io/lorax/livemedia-creator.html)
 * [Anaconda PKG on RISC-V KOJI](http://fedora.riscv.rocks/koji/buildinfo?buildID=195358)
 * [Livemedia-creator- How to create and use a Live CD](https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD#livemedia-creator)
 * [Getting Started with Quay.io](https://docs.quay.io/solution/getting-started.html)