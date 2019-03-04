%define name nrpe
%define version 3.0.1
%define release 0.rgm
%define nsusr nagios
%define nsgrp rgm
%define nsport 5666
%define ns_src_tmpfile "tmpfile.conf"

%define rgmdir /srv/rgm
%define linkdir %{rgmdir}/%{name}
%define datadir %{linkdir}-%{version}
%define plugindir %{rgmdir}/nagios/plugins

%define isaix %(test "`uname -s`" = "AIX" && echo "1" || echo "0")
%define islinux %(test "`uname -s`" = "Linux" && echo "1" || echo "0")

%if %{isaix}
	%define _prefix	/opt/nagios
	%define _docdir %{_prefix}/doc/nrpe-3.0.1
	%define nshome /opt/nagios
	%define _make gmake
%endif
%if %{islinux}
	%define _init_dir /usr/lib/systemd/system
	%define _exec_prefix %{datadir}/bin
	%define _bindir %{datadir}/bin
	%define _sbindir %{datadir}/sbin
	%define _libexecdir %{plugindir} 
	%define _datadir %{datadir}/share
	%define _localstatedir /var/run/%{name}
	%define nshome /var/run/%{name}
	%define _make make
%endif
%define _sysconfdir %{datadir}/etc

# Reserve option to override port setting with:
# rpm -ba|--rebuild --define 'nsport 5666'
%{?port:%define nsport %{port}}

# Macro that print mesages to syslog at package (un)install time
%define nnmmsg logger -t %{name}/rpm

Summary: Host/service/network monitoring agent for Nagios
URL: http://www.nagios.org
Name: %{name}
Version: %{version}
Release: %{release}
License: GPL
Group: Application/System
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
Prefix: /usr/lib/systemd/system
Prefix: %{datadir}/etc
%if %{isaix}
Requires: nagios-plugins
%endif
%if %{islinux}
Requires: bash, grep, nagios-plugins, util-linux, chkconfig, shadow-utils, sed, initscripts, mktemp
%endif

%description
NPRE (Nagios Remote Plugin Executor) is a system daemon that 
will execute various Nagios plugins locally on behalf of a 
remote (monitoring) host that uses the check_nrpe plugin.  
Various plugins that can be executed by the daemon are available 
at: http://sourceforge.net/projects/nagiosplug

This package provides the client-side NRPE agent (daemon).

%package plugin
Group: Application/System
Summary: Provides nrpe plugin for Nagios.
Requires: nagios-plugins

%description plugin
NPRE (Nagios Remote Plugin Executor) is a system daemon that 
will execute various Nagios plugins locally on behalf of a 
remote (monitoring) host that uses the check_nrpe plugin.  
Various plugins that can be executed by the daemon are available 
at: http://sourceforge.net/projects/nagiosplug

This package provides the server-side NRPE plugin for 
Nagios-related applications.

%prep
%setup -q

%if %{isaix}
# Check to see if the nrpe service is running and, if so, stop it.
/usr/bin/lssrc -s nrpe > /dev/null 2> /dev/null
if [ $? -eq 0 ] ; then
	status=`/usr/bin/lssrc -s nrpe | /usr/bin/gawk '$1=="nrpe" {print $NF}'`
	if [ "$status" = "active" ] ; then
		/usr/bin/stopsrc -s nrpe
	fi
fi
%endif

%if %{isaix}
%post
/usr/bin/lssrc -s nrpe > /dev/null 2> /dev/null
if [ $? -eq 1 ] ; then
	/usr/bin/mkssys -p %{_bindir}/nrpe -s nrpe -u 0 -a "-c %{_sysconfdir}/nrpe.cfg -d -s" -Q -R -S -n 15 -f 9
fi
/usr/bin/startsrc -s nrpe
%endif

%preun
%if %{isaix}
status=`/usr/bin/lssrc -s nrpe | /usr/bin/gawk '$1=="nrpe" {print $NF}'`
if [ "$status" = "active" ] ; then
	/usr/bin/stopsrc -s nrpe
fi
/usr/bin/rmssys -s nrpe
%endif
%if %{islinux}
if [ "$1" = 0 ]; then
	/bin/systemctl stop nrpe > /dev/null 2>&1
	/bin/systemctl disable nrpe	
fi
%endif

%if %{islinux}
%postun
if [ "$1" -ge "1" ]; then
	/bin/systemctl condrestart nrpe >/dev/null 2>&1 || :
fi
unlink %{linkdir} >/dev/null 2>&1
%endif

%build
export PATH=$PATH:/usr/sbin
CFLAGS="$RPM_OPT_FLAGS" CXXFLAGS="$RPM_OPT_FLAGS" \
MAKE=%{_make} ./configure \
	--with-init-dir=/etc/init.d \
	--with-nrpe-port=%{nsport} \
	--with-nrpe-user=%{nsusr} \
	--with-nrpe-group=%{nsgrp} \
	--prefix=%{_prefix} \
	--exec-prefix=%{_exec_prefix} \
	--bindir=%{_bindir} \
	--sbindir=%{_sbindir} \
	--libexecdir=%{_libexecdir} \
	--datadir=%{_datadir} \
	--sysconfdir=%{_sysconfdir} \
	--localstatedir=%{_localstatedir} \
	--enable-command-args
%{_make} all

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
%if %{islinux}
install -d -m 0755 ${RPM_BUILD_ROOT}%{_init_dir}
%endif
DESTDIR=${RPM_BUILD_ROOT} %{_make} install-groups-users install install-config install-init
sed -i 's/%{name}-%{version}/%{name}/g' ${RPM_BUILD_ROOT}/usr/lib/systemd/system/nrpe.service

%post
ln -sf %{datadir} %{linkdir}
chown -Rh %{nsusr}:%{nsgrp} %{linkdir}*

%clean
rm -rf $RPM_BUILD_ROOT

%files
%if %{islinux}
%defattr(755,root,root)
/usr/lib/systemd/system/nrpe.service
%endif
%{_bindir}
%{datadir}
%dir %{_sysconfdir}
%defattr(600,%{nsusr},%{nsgrp})
%config(noreplace) %{_sysconfdir}/*.cfg
%defattr(755,%{nsusr},%{nsgrp})
%if %{ns_src_tmpfile} != ""
/usr/lib/tmpfiles.d/nrpe.conf
%endif
%doc Changelog LEGAL README.md README.SSL.md SECURITY.md

%files plugin
%defattr(755,%{nsusr},%{nsgrp})
%{_libexecdir}
%defattr(644,%{nsusr},%{nsgrp})
%doc Changelog LEGAL README.md

%changelog
* Mon Mar 04 2019 Michael Aubertin <maubertin@fr.scc.com> - 3.0.1-1.rgm
- Initial fork 

* Mon Feb 06 2017 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.0.1-0.eon
- packaged for EyesOfNetwork appliance 5.1

* Thu Aug 18 2016 John Frickson jfrickson<@>nagios.com
- Changed 'make install-daemon-config' to 'make install-config'
- Added make targets 'install-groups-users' and 'install-init'
- Misc. changes

* Mon Mar 12 2012 Eric Stanley estanley<@>nagios.com
- Created autoconf input file 
- Updated to support building on AIX
- Updated install to use make install*

* Mon Jan 23 2006 Andreas Kasenides ank<@>cs.ucy.ac.cy
- fixed nrpe.cfg relocation to sample-config
- replaced Copyright label with License
- added --enable-command-args to enable remote arg passing (if desired can be disabled by commenting out)

* Wed Nov 12 2003 Ingimar Robertsson <iar@skyrr.is>
- Added adding of nagios group if it does not exist.

* Tue Jan 07 2003 James 'Showkilr' Peterson <showkilr@showkilr.com>
- Removed the lines which removed the nagios user and group from the system
- changed the patch release version from 3 to 1

* Mon Jan 06 2003 James 'Showkilr' Peterson <showkilr@showkilr.com>
- Removed patch files required for nrpe 1.5
- Update spec file for version 1.6 (1.6-1)

* Sat Dec 28 2002 James 'Showkilr' Peterson <showkilr@showkilr.com>
- First RPM build (1.5-1)
