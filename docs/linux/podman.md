# Podman for RISC-V

## Abstract

This guide will show you the steps of building the requirements for `podman`, the daemonless container engine for developing, managing, and running OCI Containers on `RISC-V`.

## Introduction

In the guide [Linux on RISC-V using QEMU and BUSYBOX from scratch](linux/simple.md), we have been able to create a minimal, bootable, `Linux`. However, it lacks a lot a feature because of it is inner simplicity. In order to run `Kubernetes` on `RISC-V`, we will use the `Fedora Core OS` Linux distribution, a minimal operating system for running containerized workloads securely and at scale.

The `Fedora Core OS` can be build using *COSA* (CoreOS Assembler). It is a collection of various tools used to build Fedora CoreOS style systems, including RHEL CoreOS. The goal is that everything needed to build and test the OS comes encapsulated in one (admittedly large) container.

*COSA* relies on other packages : `ostree` `git` `rclone` `podman`. Through this guide, we will build those dependencies for `RISC-V` on Fedora 33 over `Qemu`.

## Fedora 33 QEMU Setup

First, we will prepare a `Fedora 33` virtual machine that will run over QEMU on the RISCV64 architecture. This virtual machine will be our host for building `Fedora Core OS` and its dependencies.

### Cross-compile golang 1.16.x from source targeting RISC-V from X86

*From your X86 host*, install `golang` (revision > 1.14) and build the last revision for `RISC-V`

``` bash
dnf install golang

# Switch to root
sudo su
cd /root

# Override go path
export GOPATH=~/go
export PATH=$GOPATH/bin:$PATH

git clone https://go.googlesource.com/go

cd go
git checkout tags/go1.16.2
# Note: switching to 'tags/go1.16.2'.

cd src/
export GOOS=linux
export GOARCH=riscv64
bash -x ./make.bash -v
```

> [Install GO from source](https://golang.org/doc/install/source)
> [GO 1.16 RISC-V](https://golang.org/doc/go1.16#riscv)

#### Make a simple package

From the `go` directory, make an archive of the compilation artifacts :

``` bash
tar -czvf golang-16_2-bin-riscv64.tar.gz ./bin/linux_riscv64 ./pkg/tool/linux_riscv64 ./pkg/linux_riscv64 ./pkg/include ./src
```

### Install Requirements

**WARNING** : the QEMU VM requires 100GB of free space on your filesystem.

Install `virt-builder` by issuing :

``` bash
dnf install libguestfs-tools-c
```

Append to `virt-builder` known repositories this new entry for RISC-V images :

``` bash
mkdir -p ~/.config/virt-builder/repos.d/
cat <<EOF >~/.config/virt-builder/repos.d/fedora-riscv.conf
[fedora-riscv]
uri=https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/index
EOF
```

You can list available templates with :

``` bash
virt-builder --list | grep riscv64
```

> fedora-rawhide-developer-20190703n0 riscv64    Fedora® Rawhide Developer 20190703.n.0
> fedora-rawhide-developer-20191030n0 riscv64    Fedora® Rawhide Developer 20191030.n.0
> fedora-rawhide-developer-20191123.n.0 riscv64    Fedora® Rawhide Developer 20191123.n.0
> fedora-rawhide-minimal-20191123.n.1 riscv64    Fedora® Rawhide Minimal 20191123.n.1
> fedora-rawhide-developer-20200108.n.0 riscv64    Fedora® Rawhide Developer 20200108.n.0
> fedora-rawhide-minimal-20200108.n.0 riscv64    Fedora® Rawhide Minimal 20200108.n.0

``` bash
virt-builder --arch riscv64 --notes fedora-rawhide-developer-20200108.n.0 | grep fw_payload
```

> https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Developer-Rawhide-20200108.n.0-fw_payload-uboot-qemu-virt-smode.elf
> https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Developer-Rawhide-20200108.n.0-fw_payload-uboot-qemu-virt-smode.elf.CHECKSUM

We will now fetch the last available pre-built image, with the boot payload :

``` bash
wget http://fedora.riscv.rocks/kojifiles/work/tasks/959/910959/Fedora-Developer-Rawhide-20210113.n.0-sda.raw.zst
wget https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Developer-Rawhide-20200108.n.0-fw_payload-uboot-qemu-virt-smode.elf
```

> This image comes from an appliance image build produced by `KOJI`, the Fedora build system. You can see other artifacts here : [f33, Fedora-Developer-Rawhide-20210113.n.0, fedora-riscv64-developer-rawhide.ks, riscv64](http://fedora.riscv.rocks/koji/taskinfo?taskID=910959)

Install ZSTD archive manager :

``` bash
dnf install zstd
```

Unpack the appliance disk image and rename it :

``` bash
unzstd Fedora-Developer-Rawhide-20210113.n.0-sda.raw.zst
mv Fedora-Developer-Rawhide-20210113.n.0-sda.raw Fedora.raw
```

Extend the storage available on the *raw* disk :

``` bash
qemu-img resize -f raw Fedora.raw +40G
```

#### Boot

Boot the virtual machine with :

``` bash
qemu-system-riscv64 \
   -nographic \
   -machine virt \
   -smp 4 \
   -m 8G \
   -bios none \
   -kernel Fedora-Developer-Rawhide-20200108.n.0-fw_payload-uboot-qemu-virt-smode.elf \
   -object rng-random,filename=/dev/urandom,id=rng0 \
   -device virtio-rng-device,rng=rng0 \
   -device virtio-blk-device,drive=hd0 \
   -drive file=Fedora.raw,format=raw,id=hd0 \
   -device virtio-net-device,netdev=usernet \
   -netdev user,id=usernet,hostfwd=tcp::10000-:22
```

#### Increase partition size

``` bash
sudo fdisk /dev/vda
```

```
Command (m for help): p
Disk /dev/vda: 88.98 GiB, 95537856512 bytes, 186597376 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x5e96b6d1

Device     Boot   Start      End  Sectors  Size Id Type
/dev/vda1  *       8192  1007615   999424  488M 83 Linux
/dev/vda2       1007616 17960959 16953344  8.1G 83 Linux
```

`d`elete partition...

```
Command (m for help): d
```

... number `2`

```
Partition number (1,2, default 2): 2

Partition 2 has been deleted.
```

`n`ew partition...

```
Command (m for help): n
Partition type
   p   primary (1 primary, 0 extended, 3 free)
   e   extended (container for logical partitions)
```

... of type `p`rimary ...

```
Select (default p): p
```

... number `2`...

```
Partition number (2-4, default 2): 2
```

... First sector at `1007616`...

```
First sector (2048-186597375, default 2048): 1007616
```

... Last sector at `186597375` ...

```
Last sector, +/-sectors or +/-size{K,M,G,T,P} (1007616-186597375, default 186597375): 186597375

Created a new partition 2 of type 'Linux' and of size 88.5 GiB.
Partition #2 contains a ext4 signature.
```

Keep signature with `N`

```
Do you want to remove the signature? [Y]es/[N]o: N
```

Verify that the `/dev/vda2` has been extended

```
Command (m for help): p

Disk /dev/vda: 88.98 GiB, 95537856512 bytes, 186597376 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x5e96b6d1

Device     Boot   Start       End   Sectors  Size Id Type
/dev/vda1  *       8192   1007615    999424  488M 83 Linux
/dev/vda2       1007616 186597375 185589760 88.5G 83 Linux
```

Write the changes to the partition table and reboot

```
Command (m for help): w
The partition table has been altered.
Syncing disks.

reboot
```

Verify that the partition is now larger

``` bash
[root@fedora-riscv ~]# lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
vda    252:0    0   89G  0 disk 
├─vda1 252:1    0  488M  0 part /boot
└─vda2 252:2    0 88.5G  0 part /
```

Resize the filesystem :

```
resize2fs /dev/vda2
```

> resize2fs 1.45.6 (20-Mar-2020)
> Filesystem at /dev/vda2 is mounted on /; on-line resizing required
> old_desc_blocks = 2, new_desc_blocks = 12
> The filesystem on /dev/vda2 is now 23198720 (4k) blocks long.

You should now be able to enjoy the extra space :

``` bash
[root@fedora-riscv ~]# df -h
Filesystem      Size  Used Avail Use% Mounted on
devtmpfs        3.9G     0  3.9G   0% /dev
tmpfs           3.9G     0  3.9G   0% /dev/shm
tmpfs           1.6G  8.5M  1.6G   1% /run
/dev/vda2        88G  5.9G   82G   7% /
```

### Install dependencies (ostree rclone podman)

Update the system

```
dnf update && dnf upgrade --best
```

#### golang 1.16.x

From the X86 host, from the folder containing the archive `golang-16_2-bin-riscv64.tar.gz` previously created :

``` bash
python3 -m http.server
```

Download to your QEMU `riscv64` powered host the file with `wget`, and unpack it to `out` directory :

``` bash
sudo su
cd /root

wget http://X86_HOST:8000/golang-16_2-bin-riscv64.tar.gz -O golang-16_2-bin-riscv64.tar.gz
mkdir out
tar -zxvf golang-16_2-bin-riscv64.tar.gz -C out

cd out
mv ./go/bin/linux_riscv64/* ./go/bin/
```

Add go sources next to the compiled binaries

```
git clone https://go.googlesource.com/go
git checkout tags/go1.16.2
export PATH=~/go/bin:$PATH # Custom binary location
```

Prepare `golang` workspace

``` bash
mkdir golang
export GOPATH=~/golang # WORKSPACE
```

Verify that it works !

``` bash
[root@fedora-riscv ~]# go version
go version go1.16.2 linux/riscv64
```

#### ostree

> https://ostree.readthedocs.io/en/stable/contributing-tutorial/

Install Build Dependencies :

``` bash
dnf install @buildsys-build dnf-plugins-core && dnf builddep ostree
```

Fetch `ostree` with the last stable version :

``` bash
git clone https://github.com/ostreedev/ostree.git
cd ostree/
git checkout tags/v2020.8
git submodule update --init
```

Configure, make and install `ostree` :

``` bash
env NOCONFIGURE=1 ./autogen.sh
./configure
make -j $(nproc)
make install
```

#### rclone

Fetch `rclone` with the last stable version :

``` bash
git clone https://github.com/rclone/rclone.git
cd rclone
git checkout tags/v1.54.0
```

Patch dependency error [RISC-V support](https://github.com/ipfs/go-ipfs/issues/7781)

``` bash
go mod edit -replace=github.com/prometheus/procfs=github.com/prometheus/procfs@910e685
```

Build, check version and copy artifact to `/usr/bin`

``` bash
go build
./rclone version
cp rclone /usr/bin/
```

#### podman

##### runc

``` bash
git clone https://github.com/opencontainers/runc.git
cd runc
git checkout tags/v1.0.0-rc93
make vendor
make BUILDTAGS="seccomp"
```

Verify that it works

``` bash
[root@fedora-riscv runc]# ./runc --version
runc version 1.0.0-rc93
commit: 12644e614e25b05da6fd08a38ffa0cfe1903fdec
spec: 1.0.2-dev
go: go1.16.2
libseccomp: 2.4.1
```

Install the binary

``` bash
make install
```

##### container networking

> https://github.com/containernetworking/plugins/

``` bash
git clone https://github.com/containernetworking/plugins.git
cd plugins
GOOS=linux GOARCH=riscv64 ./build_linux.sh

export CNI_PATH=$PWD/bin
```

> https://github.com/containernetworking/cni#running-the-plugins

``` bash
mkdir -p /etc/cni/net.d

cat >/etc/cni/net.d/10-mynet.conf <<EOF
{
	"cniVersion": "0.2.0",
	"name": "mynet",
	"type": "bridge",
	"bridge": "cni0",
	"isGateway": true,
	"ipMasq": true,
	"ipam": {
		"type": "host-local",
		"subnet": "10.22.0.0/16",
		"routes": [
			{ "dst": "0.0.0.0/0" }
		]
	}
}
EOF

cat >/etc/cni/net.d/99-loopback.conf <<EOF
{
	"cniVersion": "0.2.0",
	"name": "lo",
	"type": "loopback"
}
EOF
```

> https://github.com/containernetworking/cni

``` bash
git clone https://github.com/containernetworking/cni.git
cd cni
cd scripts
./priv-net-run.sh ifconfig
```

Verify :

``` bash
root@fedora-riscv scripts]# ./priv-net-run.sh ifconfig
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.22.0.2  netmask 255.255.0.0  broadcast 10.22.255.255
        inet6 fe80::d02e:f7ff:fec2:3ce9  prefixlen 64  scopeid 0x20<link>
        ether d2:2e:f7:c2:3c:e9  txqueuelen 0  (Ethernet)
        RX packets 11  bytes 1026 (1.0 KiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 7  bytes 558 (558.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

Configure CNI networking for podman

``` bash
mkdir -p /etc/containers
curl -L -o /etc/containers/registries.conf https://raw.githubusercontent.com/projectatomic/registries/master/registries.fedora
curl -L -o /etc/containers/policy.json https://raw.githubusercontent.com/containers/skopeo/master/default-policy.json

mkdir -p /opt/cni/bin
mv plugins/bin* /opt/cni/bin/
```

##### containers-common

``` bash
git clone https://github.com/containers/common.git
cd common
make vendor
GOOS=linux GOARCH=riscv64 go build -tags "seccomp" ./...  # make BUILDTAGS="seccomp"
make install
```

##### Podman

``` bash
git clone https://github.com/containers/podman.git
cd podman
git checkout tags/v3.0.1
make BUILDTAGS="selinux seccomp systemd"
make install
```

Verify that podman is correctly set-up

```
podman --version
```

> podman version 3.0.1

## Build and run a simple image

> https://mschirbel.medium.com/introduction-to-podman-from-scratch-to-hello-world-b26b126d18d4

``` bash
mkdir helloworld
```

Create a simple C application :

nano hello.c
``` c
#include <stdio.h>

int main()
{
     printf("\nHello from Docker!\nThis message shows that your installation appears to be working correctly.\n\n");
     return 0;
}
```

Compile :

``` bash
gcc -static hello.c -o hello
```

Make a Dockerfile : 

```
FROM scratch
COPY hello /
ENTRYPOINT ["/hello"]
```

Build and run the docker image with podman :

```
podman build . -t helloworld
podman run helloworld
```

## Build and run a simple webapp

``` bash
podman run -d -p 8080:8080 carlosedp/echo_on_riscv
```

> ✔ docker.io/carlosedp/echo_on_riscv:latest
> Trying to pull docker.io/carlosedp/echo_on_riscv:latest...
> Getting image source signatures
> …  
> …  
> Writing manifest to image destination
> Storing signatures
> 3091688cc4a5dbf3e7a5ce07d93ce519bb306a7136eaedd5978b5445a12c6dd4

``` bash
podman ps
CONTAINER ID  IMAGE                                     COMMAND  CREATED         STATUS             PORTS                   NAMES
3091688cc4a5  docker.io/carlosedp/echo_on_riscv:latest           32 seconds ago  Up 17 seconds ago  0.0.0.0:8080->8080/tcp  intelligent_fermat
```

Query the HTTP server :

``` bash
[root@fedora-riscv helloworld]# curl http://localhost:8080
Hello, World! I'm running on linux/riscv64 inside a container!
```

## Further reading and related works

 * https://github.com/coreos/coreos-assembler
 * https://fedoraproject.org/wiki/Architectures/RISC-V/Installing#Download_using_virt-builder
 * [Linux & Python on RISC-V using QEMU from scratch by Vysakh P Pillai](https://embeddedinn.xyz/articles/tutorial/Linux-Python-on-RISCV-using-QEMU-from-scratch/#running-an-actual-os)
