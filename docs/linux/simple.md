# Linux on RISC-V using QEMU and BUSYBOX from scratch

## Abstract

This guide will show you the steps of building from scratch, using `QEMU` and `Busybox`, a minimal Linux targeting the `RISC-V` architecture.

This is an updated guide from [Running 64- and 32-bit RISC-V Linux on QEMU](https://risc-v-getting-started-guide.readthedocs.io/en/latest/linux-qemu.html).

## Introduction

The aim is to cross-compile the `Linux` image along with `Busybox` from the `X86_64` CPU architecture to the `RISC-V` arch and start a virtual machine with `QEMU` that will use them.

## Environment

This guide has been tested on `Fedora 33` in February 2021.

## Linux

### Install

We can easily compile `Linux` using a ready-to-go *toolchain* provided by your distro :

=== "RHEL"
    ``` bash
    sudo dnf install gcc-riscv64-linux-gnu
    ```

=== "Debian"
    ``` bash
    sudo apt-get install gcc-riscv64-linux-gnu
    ```

> Cross-build GNU C compiler.
Only building kernels is currently supported.  Support for cross-building
user space programs is not currently provided as that would massively multiply
the number of packages.

### Pull

Let's fetch `Linux` from *Linus Torvald's* repository [torvalds/linux](https://github.com/torvalds/linux) :

``` bash
git clone https://github.com/torvalds/linux.git
```

Now fetch the last stable revision :

``` bash
git checkout v5.11 # as of February 2021
```

### Configure

In order to find the **prefix** of your installed toolchain from the command above, you can use :

``` bash
PREFIX=$(rpm -ql gcc-riscv64-linux-gnu | grep "lib/gcc" | cut -d'/' -f5 | head -n1)
```

Let's use the default configuration by issuing :

``` bash
make ARCH=riscv CROSS_COMPILE=${PREFIX}- defconfig
```

### Compile

Now is the time to bench your CPU by actually compiling `Linux` !

``` bash
make ARCH=riscv CROSS_COMPILE=${PREFIX}- -j $(nproc)
```

At the end of the compilation process you should see a line similar to :

```
Kernel: arch/riscv/boot/Image.gz is ready
```

Congratulation, you have built `Linux` for `RISC-V` !

## Qemu 

We will use `Qemu` for launching `Linux` on our `X86_64` hardware. This is ideal for prototyping in a `RISC-V` without having specific hardware.

> QEMU is a generic and open source machine emulator and virtualizer.

Instead of building it from scratch, we can simply use the one provided by your distro.

=== "RHEL"

    ``` bash
    $ sudo dnf install qemu-system-riscv
    ```

=== "Debian"

    ``` bash
    $
    ```

## Toolchain

As you may have noticed, if you want to build your applications for `RISC-V`, you can't use the previously installed package because it will lack *C libraries* that your program may depend on.

We have to build our own *toolchain* in order to build `Busybox` later in this guide.

This part is heavily inspired by the [README from the RISC-V GNU Compiler Toolchain project](https://github.com/riscv/riscv-gnu-toolchain/blob/master/README.md). Feel free to follow their instructions or the ones below.

### Pull

``` bash
git clone --recursive https://github.com/riscv/riscv-gnu-toolchain
```

### Install requirements

=== "RHEL"

    ``` bash
    $ sudo dnf install ncurses-devel ncurses autoconf automake python3 libmpc-devel mpfr-devel gmp-devel gawk bison flex texinfo patchutils gcc gcc-c++ zlib-devel expat-devel
    ```

=== "Debian"

    ``` bash
    $ sudo dnf install ncurses-devel ncurses autoconf automake autotools-dev curl python3 libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev
    ```

### Configure and Install

The command below will compile the toolchain and install the artifacts in `/opt/riscv`.

``` bash
cd riscv-gnu-toolchain
./configure --prefix=/opt/riscv
make linux -j $(nproc)
```

If you list `/opt/riscv/bin`, you should see an executable file of the name `riscv64-unknown-linux-gnu-gcc`.

You can change the prefix by passing the `--prefix=$RISCV` option at the configuration stage :

``` bash
./configure --prefix=$RISCV
```

## Busybox

TBD