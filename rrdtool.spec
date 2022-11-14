Name:             rrdtool
Version:          1.7.0
Release:          20
Summary:          RA tool for data logging and analysis
License:          GPLv2+ with exceptions
URL:              http://oss.oetiker.ch/rrdtool/
Source0:          https://github.com/oetiker/%{name}-1.x/releases/download/v%{version}/%{name}-%{version}.tar.gz
Source1:          php4-r1190.tar.gz
Patch0001:        rrdtool-1.6.0-ruby-2-fix.patch
Patch0002:        rrdtool-1.4.8-php-ppc-fix.patch
Patch0003:        rrdtool-1.7.0-fix-configure-parameters.patch

Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
BuildRequires:    gcc-c++ openssl-devel freetype-devel libpng-devel zlib-devel
BuildRequires:    intltool >= 0.35.0 cairo-devel >= 1.4.6, pango-devel >= 1.17
BuildRequires:    libtool groff gettext libxml2-devel systemd automake autoconf
BuildRequires:    perl-ExtUtils-MakeMaker perl-generators perl-Pod-Html perl-devel
BuildRequires:    libdbi-devel chrpath
Requires:         dejavu-sans-mono-fonts

%description
A tool to log and analyze data gathered from all kinds of data sources.
The data analysis part of RRDtool is based on the ability to quickly
generate graphical representations of the data values collected over a
definable time period.

%package devel
Summary:    RRDtool header files
Requires:  %{name} = %{version}-%{release} pkgconfig

%description devel
RRD stands for Round Robin Database. RRD is a system to store and
display time-series data (i.e. network bandwidth, machine-room temperature,
server load average). This package allow you to build programs making
use of the library.

%package help
Summary:   Help document files for %{name}
Provides:  %{name}-doc = %{version}-%{release}
Obsoletes: %{name}-doc < %{version}-%{release}

%description help
Help document files for %{name}.

%package perl
Summary:   Perl RRDtool bindings module
Requires:  %{name} = %{version}-%{release}
Requires:  perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Provides:  perl-%{name} = %{version}-%{release}
Obsoletes: perl-%{name} < %{version}-%{release}

%description perl
The Perl RRDtool bindings module.

%{!?rrd_python3_version: %global rrd_python3_version %(%{__python3} -c 'import sys; print(sys.version.split(" ")[0])' || echo "3.14")}

%package -n python3-rrdtool
Summary:       Python RRDtool bindings module
BuildRequires: python3-devel python3-setuptools
Requires:      python3 >= %{rrd_python3_version} %{name} = %{version}-%{release}
%{?python_provide:%python_provide python3-rrdtool}

%description -n python3-rrdtool
Python RRDtool bindings module.

%package tcl
Summary:       Tcl RRDtool bindings module
BuildRequires: tcl-devel >= 8.0
Requires:      tcl >= 8.0 %{name} = %{version}-%{release}
Provides:      tcl-%{name} = %{version}-%{release}
Obsoletes:     tcl-%{name} < %{version}-%{release}

%description tcl
The %{name}-tcl package includes RRDtool bindings for Tcl.

%{!?ruby_vendorarchdir: %global ruby_vendorarchdir %(ruby -rrbconfig -e 'puts Config::CONFIG["vendorarchdir"]')}

%package ruby
Summary:       Ruby RRDtool bindings module
BuildRequires: ruby ruby-devel
Requires:      %{name} = %{version}-%{release}

%description ruby
The %{name}-ruby package includes RRDtool bindings for Ruby.

%{!?luaver: %global luaver %(lua -e "print(string.sub(_VERSION, 5))")}
%global luapkgdir %{_datadir}/lua/%{luaver}

%package lua
Summary:       Lua RRDtool bindings module
BuildRequires: lua lua-devel
Requires:      lua(abi) = %{luaver}
Requires:      %{name} = %{version}-%{release}

%description lua
The %{name}-lua package includes RRDtool bindings for Lua.

%prep
%autosetup -n %{name}-%{version} -a 1 -p1

perl -pi -e 's|get_python_lib\(0,0,prefix|get_python_lib\(1,0,prefix|g' configure
perl -pi.orig -e 's|/lib\b|/%{_lib}|g' configure Makefile.in php4/configure php4/ltconfig*
perl -pi.orig -e 's|1.299907080300|1.29990708|' bindings/perl-shared/RRDs.pm bindings/perl-piped/RRDp.pm
cp -p /usr/lib/rpm/config.{guess,sub} php4/

%build
./bootstrap
%configure --with-perl-options='INSTALLDIRS="vendor"' --disable-rpath \
           --enable-tcl-site --with-tcllib=%{_libdir} --enable-python \
           --enable-ruby --enable-libdbi --disable-static --with-pic

perl -pi.orig -e 's|-Wl,--rpath -Wl,\$rp||g' bindings/perl-shared/Makefile.PL
perl -pi.orig -e 's|-Wl,--rpath -Wl,\$\(EPREFIX\)/lib||g' bindings/ruby/extconf.rb
sed -i 's|extconf.rb \\|extconf.rb --vendor \\|' bindings/Makefile

cd bindings/perl-piped/
perl Makefile.PL INSTALLDIRS=vendor
perl -pi.orig -e 's|/lib/perl|/%{_lib}/perl|g' Makefile
cd -

make

find examples/ -type f -exec perl -pi -e 's|^#! \@perl\@|#!%{__perl}|gi' {} \;
find examples/ -name "*.pl" -exec perl -pi -e 's|\015||gi' {} \;

cd bindings/python
%py3_build
cd -

%install
export PYTHON=%{__python3}
%make_install PYTHON="%{__python3}"

mv $RPM_BUILD_ROOT%{perl_vendorlib}/RRDp.pm $RPM_BUILD_ROOT%{perl_vendorarch}/
install -d doc2/html doc2/txt
cp -a doc/*.txt doc2/txt/
cp -a doc/*.html doc2/html/

install -d doc3/html
mv doc2/html/RRD*.html doc3/html/
rm -f examples/Makefile* examples/*.in
find examples/ -type f -exec chmod 0644 {} \;

cd bindings/python
%py3_install
cd -

%find_lang %{name}

chrpath -d %{buildroot}/%{python3_sitearch}/*.so

%check

%post
/sbin/ldconfig
%systemd_post rrdcached.service rrdcached.socket

%preun
%systemd_post rrdcached.service rrdcached.socket

%postun
/sbin/ldconfig
%systemd_post rrdcached.service rrdcached.socket

%files -f %{name}.lang
%license LICENSE
%doc CONTRIBUTORS COPYRIGHT TODO NEWS CHANGES THREADS
%{_bindir}/*
%{_libdir}/*.so.*
%{_unitdir}/rrdcached.service
%{_unitdir}/rrdcached.socket
%{_datadir}/%{name}

%files tcl
%doc bindings/tcl/README
%{_libdir}/tclrrd*.so
%{_libdir}/rrdtool/*.tcl

%files devel
%{_includedir}/*.h
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc
%exclude %{_libdir}/*.la
%exclude %{perl_vendorlib}/leaktest.pl
%exclude %{_docdir}/%{name}-*
%exclude %{perl_vendorarch}/ntmake.pl
%exclude %{perl_archlib}/perllocal.pod
%exclude %{_datadir}/%{name}/examples
%exclude %{perl_vendorarch}/auto/*/{.packlist,*.bs}

%files ruby
%doc bindings/ruby/README
%{ruby_vendorarchdir}/RRD.so

%files perl
%doc doc3/html
%{perl_vendorarch}/*.pm
%attr(0755,root,root) %{perl_vendorarch}/auto/RRDs/

%files lua
%doc bindings/lua/README
%exclude %{_libdir}/lua/%{luaver}/*.la
%{_libdir}/lua/%{luaver}/*

%files -n python3-rrdtool
%doc bindings/python/COPYING bindings/python/README.md
%{python3_sitearch}/rrdtool*.so
%{python3_sitearch}/rrdtool-*.egg-info

%files help
%doc examples doc2/html doc2/txt
%{_mandir}/man1/*
%{_mandir}/man3/*

%changelog
* Mon Nov 14 2022 yaoxin <yaoxin30@h-partners.com> - 1.7.0-20
- Modify invalid Source

* Thu Sep 09 2021 wangyue <wangyue92@huawei.com> - 1.7.0-19
- fix rpath problem

* Mon Dec 23 2019 wangzhishun <wangzhishun1@huawei.com> - 1.7.0-18
- Package init

