# https://src.fedoraproject.org/rpms/rust-coreos-installer/blob/rawhide/f/rust-coreos-installer.spec
%define dracutlibdir %{_prefix}/lib/dracut
%bcond_without check
%global __cargo_skip_build 0
# The library is for internal code reuse and is not a public API
%global __cargo_is_lib 0

%global crate coreos-installer

Name:           rust-%{crate}
Version:        0.9.0
Release:        2%{?dist}
Summary:        Installer for Fedora CoreOS and RHEL CoreOS

# Upstream license specification: Apache-2.0
License:        ASL 2.0
URL:            https://crates.io/crates/coreos-installer
Source:         %{crates_source}

ExclusiveArch:  %{rust_arches}

BuildRequires:  rust-packaging
BuildRequires:  systemd-rpm-macros

%global _description %{expand:
coreos-installer installs Fedora CoreOS or RHEL CoreOS to bare-metal
machines (or, occasionally, to virtual machines).
}

%description %{_description}

%package     -n %{crate}
Summary:        %{summary}
# ASL 2.0
# ASL 2.0 or Boost
# MIT
# MIT or ASL 2.0
# Unlicense or MIT
# zlib
License:        ASL 2.0 and MIT and zlib

Requires:       gnupg
Requires:       kpartx
Requires:       systemd-udev
Requires:       util-linux
%ifarch s390x
# This should be spelled "s390utils-core" but some of the binaries are
# still moving over from s390utils-base
Requires:       /usr/sbin/chreipl
Requires:       /usr/sbin/dasdfmt
Requires:       /usr/sbin/fdasd
Requires:       /usr/sbin/lszdev
Requires:       /usr/sbin/zipl
%endif

# Since `rust-coreos-installer` creates a `coreos-installer`
# subpackage with a newer version number, which supersedes the
# deprecated `coreos-installer` package (https://src.fedoraproject.org/rpms/coreos-installer),
# an explicit `Obsoletes:` for `coreos-installer` is not necessary.

# Obsolete dracut modules as they are not provided in this package.
Obsoletes:      coreos-installer-dracut < 0.0.1

%description -n %{crate} %{_description}

%files       -n %{crate}
%license LICENSE
%doc README.md
%{_bindir}/coreos-installer

%prep
%autosetup -n %{crate}-%{version_no_tilde} -p1
%cargo_prep
# Fix SIGSEGV in tests on s390x
# https://bugzilla.redhat.com/show_bug.cgi?id=1883457
sed -i 's/"-Ccodegen-units=1",//' .cargo/config
sed -i 's|directory = "/usr/share/cargo/registry"|local-registry = "/usr/share/cargo/registry"|g' .cargo/config

# Dependencies must be present in local-registry otherwise it fails

%build
%cargo_build -f rdcore

%install
%cargo_install -f rdcore
# Install binaries, dracut modules, units, targets, generators for running via systemd
install -D -m 0755 -t %{buildroot}%{dracutlibdir}/modules.d/50rdcore dracut/50rdcore/module-setup.sh
install -D -m 0755 -t %{buildroot}%{_libexecdir} scripts/coreos-installer-service
install -D -m 0755 -t %{buildroot}%{_libexecdir} scripts/coreos-installer-disable-device-auto-activation
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer-disable-device-auto-activation.service
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer.service
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer-reboot.service
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer-noreboot.service
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer-pre.target
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer.target
install -D -m 0644 -t %{buildroot}%{_unitdir} systemd/coreos-installer-post.target
install -D -m 0755 -t %{buildroot}%{_systemdgeneratordir} systemd/coreos-installer-generator
mv %{buildroot}%{_bindir}/rdcore %{buildroot}%{dracutlibdir}/modules.d/50rdcore/

%package     -n %{crate}-bootinfra
Summary:     %{crate} boot-time infrastructure for use on Fedora/RHEL CoreOS
Requires:    %{crate}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
# ASL 2.0
# ASL 2.0 or Boost
# MIT
# MIT or ASL 2.0
# Unlicense or MIT
# zlib
License:     ASL 2.0 and MIT and zlib

# Package was renamed from coreos-installer-systemd when rdcore was added
Provides:    %{crate}-systemd = %{version}-%{release}
Obsoletes:   %{crate}-systemd <= 0.3.0-3

%description -n %{crate}-bootinfra
This subpackage contains boot-time infrastructure for Fedora CoreOS and
RHEL CoreOS.  It is not needed on other platforms.

%files       -n %{crate}-bootinfra
%{dracutlibdir}/modules.d/*
%{_libexecdir}/*
%{_unitdir}/*
%{_systemdgeneratordir}/*

%if %{with check}
%check
%cargo_test -f rdcore
%endif

%changelog
* Thu Apr 08 2021 Sohan Kunkerkar <skunkerk@redhat.com> - 0.9.0-2
- Fix dracut library path

* Thu Apr 08 2021 Sohan Kunkerkar <skunkerk@redhat.com> - 0.9.0-1
- New release
- Fix hardcoded library path

* Tue Mar 16 2021 Sohan Kunkerkar <skunkerk@redhat.com> - 0.8.0-1
- New release 

* Mon Mar 01 2021 Fabio Valentini <decathorpe@gmail.com> - 0.7.2-5
- Backport trivial commit d94715c to allow building with nix 0.20.

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 04 2021 Benjamin Gilbert <bgilbert@redhat.com> - 0.7.2-3
- Add Requires for programs invoked by coreos-installer

* Mon Dec 28 13:28:50 CET 2020 Igor Raits <ignatenkobrain@fedoraproject.org> - 0.7.2-2
- Rebuild

* Thu Oct 22 2020 Sohan Kunkerkar <skunkerk@redhat.com> - 0.7.2-1
- New release

* Tue Oct 06 2020 Dusty Mabe <dusty@dustymabe.com> - 0.7.0-4
- Backport commit to start coreos-installer service after systemd-resolved
    - https://github.com/coreos/coreos-installer/pull/389

* Thu Oct 01 2020 Dusty Mabe <dusty@dustymabe.com> - 0.7.0-3
- Backport commit to add F33 and F34 keys. Drop F31 keys.
    - https://github.com/coreos/coreos-installer/pull/387

* Wed Sep 30 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.7.0-2
- Fix SIGSEGV in tests on s390x

* Mon Sep 21 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.7.0-1
- New release

* Tue Aug 25 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.6.0-1
- New release

* Sun Aug 16 15:01:11 GMT 2020 Igor Raits <ignatenkobrain@fedoraproject.org> - 0.5.0-2
- Rebuild

* Fri Jul 31 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.5.0-1
- New release

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 24 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.4.0-1
- New release
- Rename -systemd subpackage to -bootinfra
- Add rdcore Dracut module to -bootinfra

* Fri Jul 24 2020 Igor Raits <ignatenkobrain@fedoraproject.org> - 0.3.0-2
- Rebuild

* Mon Jul 13 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.3.0-1
- New release

* Sat May 30 2020 Igor Raits <ignatenkobrain@fedoraproject.org> - 0.2.1-2
- Fixup license

* Fri May 29 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.2.1-1
- New release
- Make coreos-installer-{service,generator} world-readable

* Tue May 05 2020 Robert Fairley <rfairley@redhat.com> - 0.2.0-1
- Update to 0.2.0

* Sat Mar 21 2020 Benjamin Gilbert <bgilbert@redhat.com> - 0.1.3-1
- New release

* Fri Feb 21 2020 Josh Stone <jistone@redhat.com> - 0.1.2-4
- Bump to nix 0.17 and reqwest 0.10

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Jan 09 2020 Josh Stone <jistone@redhat.com> - 0.1.2-2
- Remove the nix downgrade.

* Wed Jan 08 2020 Dusty Mabe <dusty@dustymabe.com> - 0.1.2-1
- Bump to new upstream release 0.1.2
    - Release notes: https://github.com/coreos/coreos-installer/releases/tag/v0.1.2
- Update spec file to include systemd units from upstream
    - These were added upstream in https://github.com/coreos/coreos-installer/pull/119

* Fri Dec 20 17:57:28 UTC 2019 Robert Fairley <rfairley@redhat.com> - 0.1.1-1
- Initial package
