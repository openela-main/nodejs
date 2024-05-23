# The following macros control the usage of dependencies bundled from upstream.
#
# When to use what:
# - Regular (presumably non-modular) build: use neither (the default in Fedora)
# - Early bootstrapping build that is not intended to be shipped:
#     use --with=bootstrap; this will bundle deps and add `~bootstrap` release suffix
# - Build with some dependencies not avalaible in necessary versions (i.e. module build):
#     use --with=bundled; will bundle deps, but do not add the suffix
#
# create bootstrapping build with bundled deps and extra release suffix
%bcond_with bootstrap
# bundle dependencies that are not available in CentOS
# currently hardcoded to bundle; see Fedora spec on how to make this dependent on bootstrap
%bcond_without bundled

%if 0%{?rhel} && 0%{?rhel} < 9
%bcond_without python3_fixup
%else
%bcond_with python3_fixup
%endif

# LTO is currently broken on Node.js builds
%define _lto_cflags %{nil}

# Heavy-handed approach to avoiding issues with python
# bytecompiling files in the node_modules/ directory
%global __python %{__python3}

# == Master Relase ==
# This is used by both the nodejs package and the npm subpackage that
# has a separate version - the name is special so that rpmdev-bumpspec
# will bump this rather than adding .1 to the end.
%global baserelease 8

%{?!_pkgdocdir:%global _pkgdocdir %{_docdir}/%{name}-%{version}}

# == Node.js Version ==
# Note: Fedora should only ship LTS versions of Node.js (currently expected
# to be major versions with even numbers). The odd-numbered versions are new
# feature releases that are only supported for nine months, which is shorter
# than a Fedora release lifecycle.
%global nodejs_epoch 1
%global nodejs_major 16
%global nodejs_minor 20
%global nodejs_patch 2
%global nodejs_abi %{nodejs_major}.%{nodejs_minor}
# nodejs_soversion - from NODE_MODULE_VERSION in src/node_version.h
%global nodejs_soversion 93
%global nodejs_version %{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}
%global nodejs_release %{baserelease}

%global nodejs_datadir %{_datarootdir}/nodejs

# == Bundled Dependency Versions ==
# v8 - from deps/v8/include/v8-version.h
# Epoch is set to ensure clean upgrades from the old v8 package
%global v8_epoch 2
%global v8_major 9
%global v8_minor 4
%global v8_build 146
%global v8_patch 26
# V8 presently breaks ABI at least every x.y release while never bumping SONAME
%global v8_abi %{v8_major}.%{v8_minor}
%global v8_version %{v8_major}.%{v8_minor}.%{v8_build}.%{v8_patch}
%global v8_release %{nodejs_epoch}.%{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}.%{nodejs_release}

# c-ares - from deps/cares/include/ares_version.h
# https://github.com/nodejs/node/pull/9332
%global c_ares_version 1.19.1

# llhttp - from deps/llhttp/include/llhttp.h
%global llhttp_version 6.0.11

# libuv - from deps/uv/include/uv/version.h
%global libuv_version 1.43.0

# nghttp2 - from deps/nghttp2/lib/includes/nghttp2/nghttp2ver.h
%global nghttp2_version 1.57.0

# nghttp3 - from deps/ngtcp2/nghttp3/lib/includes/nghttp3/version.h
%global nghttp3_major 0
%global nghttp3_minor 7
%global nghttp3_patch 0
%global nghttp3_version %{nghttp3_major}.%{nghttp3_minor}.%{nghttp3_patch}

# ngtcp2 from deps/ngtcp2/ngtcp2/lib/includes/ngtcp2/version.h
%global ngtcp2_major 0
%global ngtcp2_minor 8
%global ngtcp2_patch 1
%global ngtcp2_version %{ngtcp2_major}.%{ngtcp2_minor}.%{ngtcp2_patch}

# ICU - from tools/icu/current_ver.dep
%global icu_major 71
%global icu_minor 1
%global icu_version %{icu_major}.%{icu_minor}

%global icudatadir %{nodejs_datadir}/icudata
%{!?little_endian: %global little_endian %(%{__python3} -c "import sys;print (0 if sys.byteorder=='big' else 1)")}
# " this line just fixes syntax highlighting for vim that is confused by the above and continues literal

%global sys_icu_version %(/usr/bin/icu-config --version)

%if "%{sys_icu_version}" >= "%{icu_version}"
%global bundled_icu 0
%global icu_flag system-icu
%else
%global bundled_icu 1
%global icu_flag full-icu
%endif

# OpenSSL minimum version
%global openssl_minimum 1:1.1.1

# punycode - from lib/punycode.js
# Note: this was merged into the mainline since 0.6.x
# Note: this will be unmerged in an upcoming major release
%global punycode_version 2.1.0

# npm - from deps/npm/package.json
%global npm_epoch 1
%global npm_version 8.19.4

# In order to avoid needing to keep incrementing the release version for the
# main package forever, we will just construct one for npm that is guaranteed
# to increment safely. Changing this can only be done during an update when the
# base npm version number is increasing.
%global npm_release %{nodejs_epoch}.%{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}.%{nodejs_release}

# uvwasi - from deps/uvwasi/include/uvwasi.h
%global uvwasi_version 0.0.13

# histogram_c - assumed from timestamps
%global histogram_version 0.11.2

Name: nodejs
Epoch: %{nodejs_epoch}
Version: %{nodejs_version}
Release: %{nodejs_release}%{?dist}
Summary: JavaScript runtime
License: MIT and ASL 2.0 and ISC and BSD
Group: Development/Languages
URL: http://nodejs.org/

ExclusiveArch: %{nodejs_arches}

# nodejs bundles openssl, but we use the system version in Fedora
# because openssl contains prohibited code, we remove openssl completely from
# the tarball, using the script in Source100
Source0: node-v%{nodejs_version}-stripped.tar.gz
Source1: npmrc
Source2: btest402.js
Source3: https://github.com/unicode-org/icu/releases/download/release-%{icu_major}-%{icu_minor}/icu4c-%{icu_major}_%{icu_minor}-src.tgz
Source100: %{name}-tarball.sh

# The native module Requires generator remains in the nodejs SRPM, so it knows
# the nodejs and v8 versions.  The remainder has migrated to the
# nodejs-packaging SRPM.
Source7: nodejs_native.attr

# Configure npm to look into /etc for configuration
Source8: npmrc.builtin.in

# These are full sources for dependencies included as WASM blobs in the source of Node itself.
# Note: These sources would also include pre-compiled WASM blobs… so they are adjusted not to.
# Recipes for creating these blobs are included in the sources.

# Version: jq '.version' deps/cjs-module-lexer/package.json
# Original: https://github.com/nodejs/cjs-module-lexer/archive/refs/tags/1.2.2.tar.gz
# Adjustments: rm -f cjs-module-lexer-1.2.2/lib/lexer.wasm
Source101: cjs-module-lexer-1.2.2.tar.gz
# The WASM blob was made using wasi-sdk v11; compiler libraries are linked in.
# Version source: Makefile
Source102: https://github.com/WebAssembly/wasi-sdk/archive/wasi-sdk-11/wasi-sdk-wasi-sdk-11.tar.gz

# Version: jq '.version' deps/undici/src/package.json
# Original: https://github.com/nodejs/undici/archive/refs/tags/v5.20.0.tar.gz
# Adjustments: rm -f undici-5.20.0/lib/llhttp/llhttp*.wasm*
Source111: undici-5.20.0.tar.gz
# The WASM blob was made using wasi-sdk v14; compiler libraries are linked in.
# Version source: build/Dockerfile
Source112: https://github.com/WebAssembly/wasi-sdk/archive/wasi-sdk-14/wasi-sdk-wasi-sdk-14.tar.gz

# Disable running gyp on bundled deps we don't use
Patch1: 0001-Disable-running-gyp-on-shared-deps.patch
Patch2: 0002-disable-fips-options.patch
Patch3: 0003-deps-nghttp2-update-to-1.57.0.patch
Patch4: 0004-Fix-CVE-2024-22019.patch
# CVE-2025-27983
Patch5: 0005-src-ensure-to-close-stream-when-destroying-session.patch
# CVE-2024-28182
Patch6: 0006-Limit-CONTINUATION-frames-following-an-incoming-HEAD.patch
# CVE-2024-28182
Patch7: 0007-Add-nghttp2_option_set_max_continuations.patch
# CVE-2024-22025
Patch8: 0008-zlib-pause-stream-if-outgoing-buffer-is-full.patch
# CVE-2024-25629
Patch9: 0009-Address-CVE-2024-25629.patch
# CVE-2024-27982
Patch10: 0010-http-do-not-allow-OBS-fold-in-headers-by-default.patch

BuildRequires: make
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-jinja2
%if !%{with python3_fixup}
BuildRequires: python-unversioned-command
%endif
BuildRequires: zlib-devel
BuildRequires: brotli-devel
BuildRequires: gcc >= 8.3.0
BuildRequires: gcc-c++ >= 8.3.0
BuildRequires: jq
# needed to generate bundled provides for npm dependencies
# https://src.fedoraproject.org/rpms/nodejs/pull-request/2
# https://pagure.io/nodejs-packaging/pull-request/10
BuildRequires: nodejs-packaging
BuildRequires: chrpath
BuildRequires: libatomic
BuildRequires: systemtap-sdt-devel

%if %{with bundled}
Provides:      bundled(libuv) = %{libuv_version}
%else
BuildRequires: libuv-devel >= 1:%{libuv_version}
Requires:      libuv >= 1:%{libuv_version}
%endif

%if %{with bundled} || !(0%{?fedora} || 0%{?rhel} >= 9)
Provides:      bundled(nghttp2) = %{nghttp2_version}
%else
BuildRequires: libnghttp2-devel >= %{nghttp2_version}
Requires:      libnghttp2 >= %{nghttp2_version}
%endif

# Temporarily bundle llhttp because the upstream doesn't
# provide releases for it.
Provides: bundled(llhttp) = %{llhttp_version}
Provides: bundled(nghttp3) = %{nghttp3_version}
Provides: bundled(ngtcp2) = %{ngtcp2_version}

BuildRequires: openssl-devel >= %{openssl_minimum}
Requires: openssl >= %{openssl_minimum}

# we need the system certificate store
Requires: ca-certificates

Requires: nodejs-libs%{?_isa} = %{nodejs_epoch}:%{version}-%{release}

# Pull in the full-icu data by default
Recommends: nodejs-full-i18n%{?_isa} = %{nodejs_epoch}:%{version}-%{release}

# we need ABI virtual provides where SONAMEs aren't enough/not present so deps
# break when binary compatibility is broken
Provides: nodejs(abi) = %{nodejs_abi}
Provides: nodejs(abi%{nodejs_major}) = %{nodejs_abi}
Provides: nodejs(v8-abi) = %{v8_abi}
Provides: nodejs(v8-abi%{v8_major}) = %{v8_abi}

# this corresponds to the "engine" requirement in package.json
Provides: nodejs(engine) = %{nodejs_version}

# Node.js currently has a conflict with the 'node' package in Fedora
# The ham-radio group has agreed to rename their binary for us, but
# in the meantime, we're setting an explicit Conflicts: here
Conflicts: node <= 0.3.2-12

# The punycode module was absorbed into the standard library in v0.6.
# It still exists as a seperate package for the benefit of users of older
# versions.  Since we've never shipped anything older than v0.10 in Fedora,
# we don't need the seperate nodejs-punycode package, so we Provide it here so
# dependent packages don't need to override the dependency generator.
# See also: RHBZ#11511811
# UPDATE: punycode will be deprecated and so we should unbundle it in Node v8
# and use upstream module instead
# https://github.com/nodejs/node/commit/29e49fc286080215031a81effbd59eac092fff2f
Provides: nodejs-punycode = %{punycode_version}
Provides: npm(punycode) = %{punycode_version}

# Node.js has forked c-ares from upstream in an incompatible way, so we need
# to carry the bundled version internally.
# See https://github.com/nodejs/node/commit/766d063e0578c0f7758c3a965c971763f43fec85
Provides: bundled(c-ares) = %{c_ares_version}

# Node.js is closely tied to the version of v8 that is used with it. It makes
# sense to use the bundled version because upstream consistently breaks ABI
# even in point releases. Node.js upstream has now removed the ability to build
# against a shared system version entirely.
# See https://github.com/nodejs/node/commit/d726a177ed59c37cf5306983ed00ecd858cfbbef
Provides: bundled(v8) = %{v8_version}

# Node.js is bound to a specific version of ICU which may not match the OS
# We cannot pin the OS to this version of ICU because every update includes
# an ABI-break, so we'll use the bundled copy.
Provides: bundled(icu) = %{icu_version}

# Upstream added new dependencies, but so far they are not available in Fedora
# or there's no option to built it as a shared dependency, so we bundle them
Provides: bundled(uvwasi) = %{uvwasi_version}
Provides: bundled(histogram) = %{histogram_version}

%if 0%{?fedora}
# Make sure to pull in the appropriate packaging macros when building RPMs
Requires: (nodejs-packaging if rpm-build)
%endif

# Make sure we keep NPM up to date when we update Node.js
Recommends: npm >= %{npm_epoch}:%{npm_version}-%{npm_release}%{?dist}

%description
Node.js is a platform built on Chrome's JavaScript runtime
for easily building fast, scalable network applications.
Node.js uses an event-driven, non-blocking I/O model that
makes it lightweight and efficient, perfect for data-intensive
real-time applications that run across distributed devices.


%package devel
Summary: JavaScript runtime - development headers
Group: Development/Languages
Requires: %{name}%{?_isa} = %{epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}
Requires: openssl-devel%{?_isa}
Requires: zlib-devel%{?_isa}
Requires: brotli-devel%{?_isa}
Requires: nodejs-packaging

%if %{without bundled}
Requires: libuv-devel%{?_isa}
%endif

%description devel
Development headers for the Node.js JavaScript runtime.


%package libs
Summary: Node.js and v8 libraries

# Compatibility for obsolete v8 package
%if 0%{?__isa_bits} == 64
Provides: libv8.so.%{v8_major}()(64bit)
Provides: libv8_libbase.so.%{v8_major}()(64bit)
Provides: libv8_libplatform.so.%{v8_major}()(64bit)
%else
# 32-bits
Provides: libv8.so.%{v8_major}
Provides: libv8_libbase.so.%{v8_major}
Provides: libv8_libplatform.so.%{v8_major}
%endif

Provides: v8 = %{v8_epoch}:%{v8_version}-%{nodejs_release}%{?dist}
Provides: v8%{?_isa} = %{v8_epoch}:%{v8_version}-%{nodejs_release}%{?dist}
Obsoletes: v8 < 1:6.7.17-10

%description libs
Libraries to support Node.js and provide stable v8 interfaces.


%package full-i18n
Summary: Non-English locale data for Node.js
Requires: %{name}%{?_isa} = %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}

%description full-i18n
Optional data files to provide full-icu support for Node.js. Remove this
package to save space if non-English locales are not needed.


%package -n v8-devel
Summary: v8 - development headers
Epoch: %{v8_epoch}
Version: %{v8_version}
Release: %{v8_release}%{?dist}
Requires: %{name}-devel%{?_isa} = %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}

%description -n v8-devel
Development headers for the v8 runtime.


%package -n npm
Summary: Node.js Package Manager
Epoch: %{npm_epoch}
Version: %{npm_version}
Release: %{npm_release}%{?dist}

# We used to ship npm separately, but it is so tightly integrated with Node.js
# (and expected to be present on all Node.js systems) that we ship it bundled
# now.
Obsoletes: npm < 0:3.5.4-6
Provides: npm = %{npm_epoch}:%{npm_version}
Requires: nodejs = %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}
Recommends: nodejs-docs = %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}

# Do not add epoch to the virtual NPM provides or it will break
# the automatic dependency-generation script.
Provides: npm(npm) = %{npm_version}

%description -n npm
npm is a package manager for node.js. You can use it to install and publish
your node programs. It manages dependencies and does other cool stuff.


%package docs
Summary: Node.js API documentation
Group: Documentation
BuildArch: noarch

# We don't require that the main package be installed to
# use the docs, but if it is installed, make sure the
# version always matches
Conflicts: %{name} > %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}
Conflicts: %{name} < %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}

%description docs
The API documentation for the Node.js JavaScript runtime.


%prep
%autosetup -p1 -n node-v%{nodejs_version}

# remove bundled dependencies that we aren't building
rm -rf deps/zlib
rm -rf deps/brotli
rm -rf deps/v8/third_party/jinja2
rm -rf tools/inspector_protocol/jinja2

# check for correct versions of dependencies we are bundling
check_wasm_dep() {
  local -r name="$1" source="$2" packagejson="$3"
  local -r expected_version="$(jq -r '.version' "${packagejson}")"

  if ls "${source}"|grep -q --fixed-strings "${expected_version}"; then
    printf '%s version matches\n' "${name}" >&2
  else
    printf '%s version MISMATCH: %s !~ %s\n' "${name}" "${expected_version}" "${source}" >&2
    return 1
  fi
}

check_wasm_dep cjs-module-lexer '%{SOURCE101}' deps/cjs-module-lexer/package.json
check_wasm_dep undici           '%{SOURCE111}' deps/undici/src/package.json

# Replace any instances of unversioned python' with python3
%if %{with python3_fixup}
pathfix.py -i %{__python3} -pn $(find -type f ! -name "*.js")
find . -type f -exec sed -i "s~/usr\/bin\/env python~/usr/bin/python3~" {} \;
find . -type f -exec sed -i "s~/usr\/bin\/python\W~/usr/bin/python3~" {} \;
sed -i "s~usr\/bin\/python2~usr\/bin\/python3~" ./deps/v8/tools/gen-inlining-tests.py
sed -i "s~usr\/bin\/python.*$~usr\/bin\/python3~" ./deps/v8/tools/mb/mb_unittest.py
find . -type f -exec sed -i "s~python -c~python3 -c~" {} \;
%endif

%build
# When compiled on armv7hl this package generates an out of range
# reference to the literal pool.  This is most likely a GCC issue.
%ifarch armv7hl
%define _lto_cflags %{nil}
%endif

%ifarch s390 s390x %{arm} %ix86
# Decrease debuginfo verbosity to reduce memory consumption during final
# library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif

export CC='%{__cc}'
export CXX='%{__cxx}'
%{?with_python3_fixup:export NODE_GYP_FORCE_PYTHON=%{__python3}}

# build with debugging symbols and add defines from libuv (#892601)
# Node's v8 breaks with GCC 6 because of incorrect usage of methods on
# NULL objects. We need to pass -fno-delete-null-pointer-checks
extra_cflags=(
    -D_LARGEFILE_SOURCE
    -D_FILE_OFFSET_BITS=64
    -DZLIB_CONST
    -fno-delete-null-pointer-checks
)
export CFLAGS="%{optflags} ${extra_cflags[*]}" CXXFLAGS="%{optflags} ${extra_cflags[*]}"
export LDFLAGS="%{build_ldflags}"

%{__python3} configure.py --prefix=%{_prefix} \
           --shared \
           --libdir=%{_lib} \
           --shared-openssl \
           --shared-zlib \
           --shared-brotli \
           %{!?with_bundled:--shared-libuv} \
           %{!?with_bundled:--shared-nghttp2} \
           %{?with_bundled:--without-dtrace}%{!?with_bundled:--with-dtrace} \
           --with-intl=small-icu \
           --with-icu-default-data-dir=%{icudatadir} \
           --without-corepack \
           --openssl-conf-name=openssl_conf \
           --openssl-use-def-ca-store \
           --openssl-default-cipher-list=PROFILE=SYSTEM

make BUILDTYPE=Release %{?_smp_mflags}

# Extract the ICU data and convert it to the appropriate endianness
pushd deps/
tar xfz %SOURCE3

pushd icu/source

mkdir -p converted
%if 0%{?little_endian}
# The little endian data file is included in the ICU sources
install -Dpm0644 data/in/icudt%{icu_major}l.dat converted/

%else
# For the time being, we need to build ICU and use the included `icupkg` tool
# to convert the little endian data file into a big-endian one.
# At some point in the future, ICU releases will start including both data
# files and we should switch to those.
mkdir -p data/out/tmp

%configure
%make_build

icu_root=$(pwd)
LD_LIBRARY_PATH=./lib ./bin/icupkg -tb data/in/icudt%{icu_major}l.dat \
                                       converted/icudt%{icu_major}b.dat
%endif

popd # icu/source
popd # deps


%install
rm -rf %{buildroot}

./tools/install.py install %{buildroot} %{_prefix}

# Set the binary permissions properly
chmod 0755 %{buildroot}/%{_bindir}/node
chrpath --delete %{buildroot}%{_bindir}/node

# Install library symlink
ln -s libnode.so.%{nodejs_soversion} %{buildroot}%{_libdir}/libnode.so

# Install v8 compatibility symlinks
for header in %{buildroot}%{_includedir}/node/libplatform %{buildroot}%{_includedir}/node/v8*.h; do
    header=$(basename ${header})
    ln -s ./node/${header} %{buildroot}%{_includedir}/${header}
done
ln -s ./node/cppgc %{buildroot}%{_includedir}/cppgc
for soname in libv8 libv8_libbase libv8_libplatform; do
    ln -s libnode.so.%{nodejs_soversion} %{buildroot}%{_libdir}/${soname}.so
    ln -s libnode.so.%{nodejs_soversion} %{buildroot}%{_libdir}/${soname}.so.%{v8_major}
done

# own the sitelib directory
mkdir -p %{buildroot}%{_prefix}/lib/node_modules

# ensure Requires are added to every native module that match the Provides from
# the nodejs build in the buildroot
install -Dpm0644 %{SOURCE7} %{buildroot}%{_rpmconfigdir}/fileattrs/nodejs_native.attr
cat << EOF > %{buildroot}%{_rpmconfigdir}/nodejs_native.req
#!/bin/sh
echo 'nodejs(abi%{nodejs_major}) >= %nodejs_abi'
echo 'nodejs(v8-abi%{v8_major}) >= %v8_abi'
EOF
chmod 0755 %{buildroot}%{_rpmconfigdir}/nodejs_native.req

# install documentation
mkdir -p %{buildroot}%{_pkgdocdir}/html
cp -pr doc/* %{buildroot}%{_pkgdocdir}/html
rm -f %{buildroot}%{_pkgdocdir}/html/nodejs.1

# node-gyp needs common.gypi too
mkdir -p %{buildroot}%{_datadir}/node
cp -p common.gypi %{buildroot}%{_datadir}/node

# Install the GDB init tool into the documentation directory
mv %{buildroot}/%{_datadir}/doc/node/gdbinit %{buildroot}/%{_pkgdocdir}/gdbinit

# install NPM docs to mandir
mkdir -p %{buildroot}%{_mandir} \
         %{buildroot}%{_pkgdocdir}/npm

cp -pr deps/npm/man/* %{buildroot}%{_mandir}/
rm -rf %{buildroot}%{_prefix}/lib/node_modules/npm/man
ln -sf %{_mandir}  %{buildroot}%{_prefix}/lib/node_modules/npm/man

# Install Gatsby HTML documentation to %%{_pkgdocdir}
cp -pr deps/npm/docs %{buildroot}%{_pkgdocdir}/npm/
rm -rf %{buildroot}%{_prefix}/lib/node_modules/npm/docs

ln -sf %{_pkgdocdir}/npm %{buildroot}%{_prefix}/lib/node_modules/npm/docs

# Node tries to install some python files into a documentation directory
# (and not the proper one). Remove them for now until we figure out what to
# do with them.
rm -f %{buildroot}/%{_defaultdocdir}/node/lldb_commands.py \
      %{buildroot}/%{_defaultdocdir}/node/lldbinit

# Some NPM bundled deps are executable but should not be. This causes
# unnecessary automatic dependencies to be added. Make them not executable.
# Skip the npm bin directory or the npm binary will not work.
find %{buildroot}%{_prefix}/lib/node_modules/npm \
    -not -path "%{buildroot}%{_prefix}/lib/node_modules/npm/bin/*" \
    -executable -type f \
    -exec chmod -x {} \;

# The above command is a little overzealous. Add a few permissions back.
chmod 0755 %{buildroot}%{_prefix}/lib/node_modules/npm/node_modules/@npmcli/run-script/lib/node-gyp-bin/node-gyp
chmod 0755 %{buildroot}%{_prefix}/lib/node_modules/npm/node_modules/node-gyp/bin/node-gyp.js

# Drop the NPM builtin configuration in place
sed -e 's#@SYSCONFDIR@#%{_sysconfdir}#g' \
    %{SOURCE8} > %{buildroot}%{_prefix}/lib/node_modules/npm/npmrc

# Drop the NPM default configuration in place
mkdir -p %{buildroot}%{_sysconfdir}
cp %{SOURCE1} %{buildroot}%{_sysconfdir}/npmrc

# Install the full-icu data files
install -Dpm0644 -t %{buildroot}%{icudatadir} deps/icu/source/converted/*


%check
# Fail the build if the versions don't match
LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.node, '%{nodejs_version}')"
LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.v8.replace(/-node\.\d+$/, ''), '%{v8_version}')"
LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.ares.replace(/-DEV$/, ''), '%{c_ares_version}')"

# Ensure we have punycode and that the version matches
LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"punycode\").version, '%{punycode_version}')"

# Ensure we have npm and that the version matches
LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}%{_bindir}/node %{buildroot}%{_bindir}/npm version --json |jq -e '.npm == "%{npm_version}"'

# Make sure i18n support is working
NODE_PATH=%{buildroot}%{_prefix}/lib/node_modules:%{buildroot}%{_prefix}/lib/node_modules/npm/node_modules LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}/%{_bindir}/node --icu-data-dir=%{buildroot}%{icudatadir} %{SOURCE2}


%pretrans -n npm -p <lua>
-- Replace the npm man directory with a symlink
-- Drop this scriptlet when F31 is EOL
path = "%{_prefix}/lib/node_modules/npm/man"
st = posix.stat(path)
if st and st.type == "directory" then
  status = os.rename(path, path .. ".rpmmoved")
  if not status then
    suffix = 0
    while not status do
      suffix = suffix + 1
      status = os.rename(path .. ".rpmmoved", path .. ".rpmmoved." .. suffix)
    end
    os.rename(path, path .. ".rpmmoved")
  end
end


%files
%{_bindir}/node
%dir %{_prefix}/lib/node_modules
%dir %{_datadir}/node
%dir %{_datadir}/systemtap
%dir %{_datadir}/systemtap/tapset
%{_datadir}/systemtap/tapset/node.stp

%if %{without bundled}
%dir %{_usr}/lib/dtrace
%{_usr}/lib/dtrace/node.d
%endif

%{_rpmconfigdir}/fileattrs/nodejs_native.attr
%{_rpmconfigdir}/nodejs_native.req
%license LICENSE
%doc AUTHORS CHANGELOG.md onboarding.md GOVERNANCE.md README.md
%doc %{_mandir}/man1/node.1*


%files devel
%{_includedir}/node
%{_libdir}/libnode.so
%{_datadir}/node/common.gypi
%{_pkgdocdir}/gdbinit


%files full-i18n
%dir %{icudatadir}
%{icudatadir}/icudt%{icu_major}*.dat


%files libs
%license LICENSE
%{_libdir}/libnode.so.%{nodejs_soversion}
%{_libdir}/libv8.so.%{v8_major}
%{_libdir}/libv8_libbase.so.%{v8_major}
%{_libdir}/libv8_libplatform.so.%{v8_major}
%dir %{nodejs_datadir}/


%files -n v8-devel
%{_includedir}/libplatform
%{_includedir}/v8*.h
%{_includedir}/cppgc
%{_libdir}/libv8.so
%{_libdir}/libv8_libbase.so
%{_libdir}/libv8_libplatform.so


%files -n npm
%{_bindir}/npm
%{_bindir}/npx
%{_prefix}/lib/node_modules/npm
%config(noreplace) %{_sysconfdir}/npmrc
%ghost %{_sysconfdir}/npmignore
%doc %{_mandir}/man1/npm*.1*
%doc %{_mandir}/man1/npx.1*
%doc %{_mandir}/man5/folders.5*
%doc %{_mandir}/man5/install.5*
%doc %{_mandir}/man5/npm-global.5*
%doc %{_mandir}/man5/npm-json.5*
%doc %{_mandir}/man5/npm-shrinkwrap-json.5*
%doc %{_mandir}/man5/npmrc.5*
%doc %{_mandir}/man5/package-json.5*
%doc %{_mandir}/man5/package-lock-json.5*
%doc %{_mandir}/man7/config.7*
%doc %{_mandir}/man7/dependency-selectors.7*
%doc %{_mandir}/man7/developers.7*
%doc %{_mandir}/man7/logging.7*
%doc %{_mandir}/man7/orgs.7*
%doc %{_mandir}/man7/package-spec.7*
%doc %{_mandir}/man7/registry.7*
%doc %{_mandir}/man7/removal.7*
%doc %{_mandir}/man7/scope.7*
%doc %{_mandir}/man7/scripts.7*
%doc %{_mandir}/man7/workspaces.7*


%files docs
%doc doc
%dir %{_pkgdocdir}
%{_pkgdocdir}/html
%{_pkgdocdir}/npm/docs


%changelog
* Tue May 07 2024 Jan Staněk <jstanek@redhat.com> - 1:16.20.2-8
- Actually apply the patch for CVE-2024-27982

* Wed Apr 24 2024 Jan Staněk <jstanek@redhat.com> - 1:16.20.2-7
- Backport patch for CVE-2024-27982

* Tue Apr 09 2024 Jan Staněk <jstanek@redhat.com> - 1:16.20.2-6
- Use system OpenSSL configuration section

* Mon Apr 08 2024 Jan Staněk <jstanek@redhat.com> - 1:16.20.2-5
- Backport patches for several CVEs.
  Fixes CVE-2024-22025 CVE-2024-25629 CVE-2024-27983 CVE-2024-28182

* Tue Mar 05 2024 Honza Horak <hhorak@redhat.com> - 1:16.20.2-4
- Fix CVE-2024-22019

* Fri Oct 13 2023 Jan Staněk <jstanek@redhat.com> - 1:16.20.2-3
- Update version of bundled nghttp2 in spec file

* Thu Oct 12 2023 Jan Staněk <jstanek@redhat.com> - 1:16.20.2-2
- Update bundled nghttp2 to 1.57.0 (CVE-2023-44487)

* Wed Aug 30 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.20.2-1
- Rebase to 16.20.2
  Resolves: CVE-2023-32002 CVE-2023-32006 CVE-2023-32559

* Mon Jul 31 2023 Honza Horak <hhorak@redhat.com> - 1:16.20.1-2
- Fix segfault that happens when processing fips-related options
  Resolves: BZ#2227796

* Thu Jul 13 2023 Jan Staněk <jstanek@redhat.com> - 1:16.20.1-1
- Rebase to 16.20.1
  Resolves: rhbz#2188291
  Resolves: CVE-2023-30581 CVE-2023-30588 CVE-2023-30589 CVE-2023-30590
- Replace /usr/etc/npmrc symlink with builtin configuration
  Resolves: rhbz#2177781

* Wed May 31 2023 Jan Staněk <jstanek@redhat.com> - 1:16.19.1-2
- Update bundled c-ares to 1.19.1
  Resolves: CVE-2023-31124 CVE-2023-31130 CVE-2023-31147 CVE-2023-32067

* Mon Mar 27 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.19.1-1
- Rebase to 16.19.1
- Resolves: rhbz#2153714
- Resolves: CVE-2023-23918 CVE-2023-23919 CVE-2023-23936 CVE-2023-24807 CVE-2023-23920
- Resolves: CVE-2022-25881 CVE-2022-4904

* Wed Dec 07 2022 Jan Staněk <jstanek@redhat.com> - 1:16.18.1-3
- Update sources of undici WASM blobs
  Resolves: rhbz#2151617

* Mon Dec 05 2022 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.18.1-2
- Add back libs and v8-devel subpackages
- Related: RHBZ#2121126
- Record previously fixed CVE
- Resolves: CVE-2021-44906

* Wed Nov 16 2022 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.18.1-1
- Rebase + CVEs
- Resolves: #2142808
- Resolves: #2142826, #2131745, #2142855

* Tue Sep 27 2022 Jan Staněk <jstanek@redhat.com> - 16.17.1-1
- Rebase to version 16.17.1
  Resolves: CVE-2022-35255 CVE-2022-35256

* Tue Aug 23 2022 Jan Staněk <jstanek@redhat.com> - 16.16.0-1
- Rebase to version 16.16.0
  Resolves: RHBZ#2106290
  Resolves: CVE-2022-32212 CVE-2022-32213 CVE-2022-32214 CVE-2022-32215
  Resolves: CVE-2022-29244

* Thu Apr 21 2022 Jan Staněk <jstanek@redhat.com> - 16.14.0-5
- Decouple dependency bundling from bootstrapping

* Tue Apr 05 2022 Jan Staněk <jstanek@redhat.com> - 16.14.0-4
- Apply lock file validation fixes
  Resolves: CVE-2021-43616

* Thu Mar 31 2022 Jan Staněk <jstanek@redhat.com> - 16.14.0-3
- Refactor bootstap handling and configure script invocation
  Resolves: rhbz#2056969

* Sun Feb 13 2022 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.14.0-2
- Build with bootstrap by default due to old versions of dependencies available
- Resolves: #2042995, #2042970, #2042981, #2042989
- Resolves: #2029936, #2024890, #2014499, #2014135
- Resolves: #2013834, #1945299

* Fri Feb 11 2022 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.14.0-1
- Update to latest version
- Use jinja and jq
- Don't fix python3
- Resolves: CVE-2022-21824, CVE-2021-44531, CVE-2021-44532, CVE-2021-44533
- Resolves CVE-2020-15095
- Resolves: CVE-2021-3918, CVE-2021-22959, CVE-2021-22960
- Resolves: CVE-2021-3807, CVE-2021-27290

* Wed Sep 29 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.10.0-1
- Rebase to 16.10.0, add corepack, fix PowerShell dependency
- Resolves: RHBZ#2000539, #2000548, #2000549, #2002177

* Thu Aug 12 2021 Jan Staněk <jstanek@redhat.com> - 1:16.6.2-1
- Rebase to 16.6.2
  Resolves: CVE-2021-22931 CVE-2021-22939 CVE-2021-22940

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 1:16.5.0-3
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Thu Jul 22 2021 Zuzana Svetlikova <zsvetlik@redhat.com - 1:16.5.0-2
- Bump for gating
- Resolves: RHBZ#1979926

* Tue Jul 20 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.5.0-1
- Rebase to 16.5.0
- Fixes CVE-2021-22918(libuv)
- Resolves: RHBZ#1979926

* Wed Jun 16 2021 Mohan Boddu <mboddu@redhat.com> - 1:16.3.0-2
- Rebuilt for RHEL 9 BETA for openssl 3.0
  Related: rhbz#1971065

* Tue Jun 01 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.3.0-1
- Resolves: RHBZ#1953491
- Rebase to 16.3.0
- includes https://github.com/nodejs/node/pull/38732

* Thu May 20 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.2.0-1
- Resolves: RHBZ#1953491
- Rebase to 16.2.0
- includes https://github.com/nodejs/node/pull/38633 (FIPS for OpenSSL 3.0)

* Wed May 19 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.1.0-1
- Resolves: RHBZ#1953491
- Support for OpenSSL 3.0.0
- Rebase to v16.x
- Update version of gcc and gcc-c++ needed
- Bundle nghttp3 and ngtcp2

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com>
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Tue Mar 30 2021 Jonathan Wakely <jwakely@redhat.com> - 1:14.16.0-4
- Rebuilt for removed libstdc++ symbol (#1937698)

* Tue Mar 09 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.16.0-3
- Only require nodejs-packaging on Fedora
- remove --debug-nghttp2 (#1930775)
- always build with systemtap

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:14.15.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 04 2021 Stephen Gallagher <sgallagh@redhat.com> - 1:14.15.4-1
- Update to 14.15.4

* Wed Dec 02 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.15.1-1
- Update to 14.15.1

* Tue Oct 20 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.14.0-2
- Don't build with LTO on aarch64

* Mon Oct 19 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.14.0-1
- Update to 14.14.0

* Fri Oct 09 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.13.1-1
- Update to 14.13.1

* Thu Oct 01 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.13.0-1
- Update to 14.13.0

* Wed Sep 16 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.11.0-1
- Update to 14.11.0

* Tue Sep 08 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.10.0-1
- Update to 14.10.0

* Fri Aug 21 2020 Jeff Law <law@redhat.com> - 1:14.7.0-2
- Narrow LTO opt-out to just armv7hl

* Fri Jul 31 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.7.0-1
- Update to 14.7.0

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:14.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue Jul 07 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.5.0-1
- Update to 14.5.0

* Tue Jul 07 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.4.0-3
- Update for new packaging guidelines

* Tue Jun 30 2020 Jeff Law <law@redhat.com> - 1:14.4.0-2
- Disable LTO

* Wed Jun 03 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.4.0-1
- Security update to 14.4.0

* Thu May 21 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.3.0-1
- Update to 14.3.0

* Wed May 06 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.2.0-1
- Update to 14.2.0

* Wed Apr 29 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:14.1.0-1
- Update to 14.1.0

* Fri Apr 24 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.0.0-2
- Keep the fix scripts for Koji

* Thu Apr 23 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.0.0-1
- Update to 14.0.0
- v14.x should be python3 compatible, so commented out py sed scripts

* Wed Apr 15 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:13.13.0-1
- Update to 13.13.0
- Add bundled uvwasi and histogram_c provides
- Add shared brotli dependency
- Remove icustrip.py patch, which was merged in upstream

* Tue Mar 17 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:13.11.0-2
- Fix python3 issue in icustrip.py

* Mon Mar 16 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:13.11.0-1
- Update to 13.11.0

* Wed Feb 26 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:13.9.0-2
- Build with python 3 only

* Tue Feb 25 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:13.9.0-1
- Release Node.js 13.9.0

* Tue Feb 25 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.16.1-1
- Update to 12.16.1
- Fixes six regressions introduced in 12.16.0

* Fri Feb 14 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.16.0-1
- Update to 12.16.0
- Drop upstreamed patch

* Thu Feb 06 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.15.0-1
- Update to 12.15.0

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:12.14.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Jan 13 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.14.1-3
- Fix issue with header symlinks in v8-devel

* Tue Jan 07 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.14.1-2
- Drop unneeded dependency on http-parser-devel

* Tue Jan 07 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.14.1-1
- Update to 12.14.1
- https://github.com/nodejs/node/blob/v12.14.1/doc/changelogs/CHANGELOG_V12.md

* Mon Jan 06 2020 Stephen Gallagher <sgallagh@redhat.com> - 1:12.14.0-2
- Update to 12.14.0
- https://github.com/nodejs/node/blob/v12.14.0/doc/changelogs/CHANGELOG_V12.md
- Add new subpackage nodejs-full-i18n to enable optional non-English locale
  support
- Update documentation packaging for NPM

* Mon Dec 02 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.13.1-1
- Update to 12.13.1
- https://github.com/nodejs/node/blob/v12.13.1/doc/changelogs/CHANGELOG_V12.md

* Tue Oct 29 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.13.0-6
- Add proper i18n support

* Tue Oct 29 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.13.0-5
- Fix issue with NPM docs being replaced with a symlink

* Mon Oct 28 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.13.0-2
- Simplify npmrc default configuration

* Mon Oct 28 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.13.0-1
- Update to 12.13.0 (LTS)
- https://github.com/nodejs/node/blob/v12.13.0/doc/changelogs/CHANGELOG_V12.md
- NPM no longer clobbers RPM-installed Node.js modules
- Drop no-longer needed patch to suppress `npm update -g npm` message

* Wed Sep 04 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.10.0-1
- Update to 12.10.0
- https://github.com/nodejs/node/blob/v12.10.0/doc/changelogs/CHANGELOG_V12.md#12.10.0

* Wed Aug 21 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.9.0-1
- Update to 12.9.0
- https://github.com/nodejs/node/blob/v12.9.0/doc/changelogs/CHANGELOG_V12.md#12.9.0

* Thu Aug 15 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.8.2-1
- Update to 12.8.1
- Resolves: CVE-2019-9511 "Data Dribble"
- Resolves: CVE-2019-9512 "Ping Flood"
- Resolves: CVE-2019-9513 "Resource Loop"
- Resolves: CVE-2019-9514 "Reset Flood"
- Resolves: CVE-2019-9515 "Settings Flood"
- Resolves: CVE-2019-9516 "0-Length Headers Leak"
- Resolves: CVE-2019-9517 "Internal Data Buffering"
- Resolves: CVE-2019-9518 "Empty Frames Flood"
- https://github.com/nodejs/node/blob/v12.8.1/doc/changelogs/CHANGELOG_V12.md#12.8.1

* Mon Aug 05 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.7.0-3
- Fix epoch dependencies
- Carry data files for ICU

* Fri Aug 02 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.7.0-2
- Change v8-devel release field to avoid duplicated package names

* Thu Aug 01 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.7.0-1
- Update to 12.7.0
- https://nodejs.org/en/blog/release/v12.7.0/

* Tue Jul 30 2019 Tom Hughes <tom@compton.nu> - 1:12.6.0-2
- Bump release to fix dependencies

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1:12.6.0-1.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu Jun 27 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.6.0-1
- Update to 12.6.0
- https://nodejs.org/en/blog/release/v12.6.0/
- https://nodejs.org/en/blog/release/v12.5.0/

* Tue Jun 04 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.4.0-1
- Update to 12.4.0
- https://nodejs.org/en/blog/release/v12.4.0/

* Fri May 24 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.3.1-1
- Update to 12.3.1
- https://nodejs.org/en/blog/release/v12.3.1/
- https://nodejs.org/en/blog/release/v12.3.0/

* Wed May 15 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.2.0-1
- Update to 12.2.0
- https://nodejs.org/en/blog/release/v12.2.0/

* Tue Apr 30 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.1.0-1
- Update to 12.1.0
- https://nodejs.org/en/blog/release/v12.1.0/

* Wed Apr 24 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.0.0-3
- Fix upgrade bug for v8-devel (BZ #1702609)

* Tue Apr 23 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.0.0-2
- Node.js 12.x requires OpenSSL 1.1.1+

* Tue Apr 23 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:12.0.0-1
- Release 12.0.0
- https://nodejs.org/en/blog/release/v12.0.0/

* Thu Apr 11 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:11.13.0-1
- Update to 11.13.0
- https://nodejs.org/en/blog/release/v11.13.0/
- https://nodejs.org/en/blog/release/v11.12.0/
- https://nodejs.org/en/blog/release/v11.11.0/

* Fri Mar 01 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:11.10.1-1
- Update to 11.10.1
- https://nodejs.org/en/blog/release/v11.10.1/
- https://nodejs.org/en/blog/release/v11.10.0/
- https://nodejs.org/en/blog/release/v11.9.0/
- https://nodejs.org/en/blog/release/v11.8.0/

* Fri Jan 18 2019 Stephen Gallagher <sgallagh@redhat.com> - 1:11.7.0-1
- Update to 11.7.0
- https://nodejs.org/en/blog/release/v11.7.0/
- https://nodejs.org/en/blog/release/v11.6.0/
- https://nodejs.org/en/blog/release/v11.5.0/
- https://nodejs.org/en/blog/release/v11.4.0/

* Thu Nov 29 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:11.3.0-1
- Update to 11.3.0
- https://nodejs.org/en/blog/release/v11.2.0/
- https://nodejs.org/en/blog/release/v11.3.0/

* Fri Nov 02 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:11.1.0-1
- Update to 11.1.0
- https://nodejs.org/en/blog/release/v11.1.0/

* Thu Nov 01 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:11.0.0-1
- Update to 11.0.0
- https://nodejs.org/en/blog/release/v11.0.0/

* Thu Nov 01 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.13.0-1
- Update to 10.13.0
- https://nodejs.org/en/blog/release/v10.13.0/

* Thu Oct 11 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.12.0-1
- Update to 10.12.0
- https://nodejs.org/en/blog/release/v10.12.0/

* Wed Oct 10 2018 Jan Staněk <jstanek@redhat.com> - 1:10.11.0-2
- Add non-bootstrap BR for nodejs-packaging

* Thu Sep 20 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.11.0-1
- Update to 10.11.0
- https://nodejs.org/en/blog/release/v10.11.0/

* Wed Sep 19 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.10.0-2
- Really, finally fix npm dep executable permissions

* Tue Sep 11 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.10.0-1
- Update to 10.10.0
- https://nodejs.org/en/blog/release/v10.10.0/
- Fix issue with npm permissions

* Tue Aug 21 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.9.0-2
- Clean up automatic dependencies for npm

* Thu Aug 16 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.9.0-1
- Update to 10.9.0
- https://nodejs.org/en/blog/release/v10.9.0/

* Tue Aug 07 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.8.0-1
- Update to 10.8.0
- https://nodejs.org/en/blog/release/v10.8.0/

* Fri Jul 20 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.7.0-4
- Fix npm upgrade scriptlet
- Fix unexpected trailing .1 in npm release field

* Fri Jul 20 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.7.0-3
- Restore annotations to binaries
- Fix unexpected trailing .1 in release field

* Thu Jul 19 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.7.0-2
- Update to 10.7.0
- https://nodejs.org/en/blog/release/v10.7.0/
- https://nodejs.org/en/blog/release/v10.6.0/

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1:10.5.0-1.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Jun 21 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.5.0-1
- Update to 10.5.0
- https://nodejs.org/en/blog/release/v10.5.0/

* Thu Jun 14 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.4.1-1
- Update to 10.4.1 to address security issues
- https://nodejs.org/en/blog/release/v10.4.1/
- Resolves: rhbz#1590801
- Resolves: rhbz#1591014
- Resolves: rhbz#1591019

* Thu Jun 07 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.4.0-1
- Update to 10.4.0
- https://nodejs.org/en/blog/release/v10.4.0/

* Wed May 30 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.3.0-1
- Update to 10.3.0
- Update npm to 6.1.0
- https://nodejs.org/en/blog/release/v10.3.0/

* Tue May 29 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.2.1-2
- Fix up bare 'python' to be python2
- Drop redundant entry in docs section

* Fri May 25 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.2.1-1
- Update to 10.2.1
- https://nodejs.org/en/blog/release/v10.2.1/

* Wed May 23 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.2.0-1
- Update to 10.2.0
- https://nodejs.org/en/blog/release/v10.2.0/

* Thu May 10 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.1.0-3
- Fix incorrect rpm macro

* Thu May 10 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.1.0-2
- Include upstream v8 fix for ppc64[le]
- Disable debug build on ppc64[le] and s390x

* Wed May 09 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.1.0-1
- Update to 10.1.0
- https://nodejs.org/en/blog/release/v10.1.0/
- Reenable node_g binary

* Thu Apr 26 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:10.0.0-1
- Update to 10.0.0
- https://nodejs.org/en/blog/release/v10.0.0/
- Drop workaround patch
- Temporarily drop node_g binary due to
  https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85587

* Fri Apr 13 2018 Rafael dos Santos <rdossant@redhat.com> - 1:9.11.1-2
- Use standard Fedora linker flags (bug #1543859)

* Thu Apr 05 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.11.1-1
- Update to 9.11.1
- https://nodejs.org/en/blog/release/v9.11.0/
- https://nodejs.org/en/blog/release/v9.11.1/

* Wed Mar 28 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.10.0-1
- Update to 9.10.0
- https://nodejs.org/en/blog/release/v9.10.0/

* Wed Mar 21 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.9.0-1
- Update to 9.9.0
- https://nodejs.org/en/blog/release/v9.9.0/

* Thu Mar 08 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.8.0-1
- Update to 9.8.0
- https://nodejs.org/en/blog/release/v9.8.0/

* Thu Mar 01 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.7.0-1
- Update to 9.7.0
- https://nodejs.org/en/blog/release/v9.7.0/
- Work around F28 build issue

* Sun Feb 25 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.6.1-1
- Update to 9.6.1
- https://nodejs.org/en/blog/release/v9.6.1/
- https://nodejs.org/en/blog/release/v9.6.0/

* Mon Feb 05 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:9.5.0-1
- Package Node.js 9.5.0

* Thu Jan 11 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:8.9.4-2
- Fix incorrect Requires:

* Thu Jan 11 2018 Stephen Gallagher <sgallagh@redhat.com> - 1:8.9.4-1
- Update to 8.9.4
- https://nodejs.org/en/blog/release/v8.9.4/
- Switch to system copy of nghttp2

* Fri Dec 08 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.9.3-2
- Update to 8.9.3
- https://nodejs.org/en/blog/release/v8.9.3/
- https://nodejs.org/en/blog/release/v8.9.2/

* Thu Nov 30 2017 Pete Walter <pwalter@fedoraproject.org> - 1:8.9.1-2
- Rebuild for ICU 60.1

* Thu Nov 09 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.9.1-1
- Update to 8.9.1

* Tue Oct 31 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.9.0-1
- Update to 8.9.0
- Drop upstreamed patch

* Thu Oct 26 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.8.1-1
- Update to 8.8.1 to fix a regression

* Wed Oct 25 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.8.0-1
- Security update to 8.8.0
- https://nodejs.org/en/blog/release/v8.8.0/

* Sun Oct 15 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.7.0-1
- Update to 8.7.0
- https://nodejs.org/en/blog/release/v8.7.0/

* Fri Oct 06 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.6.0-2
- Use bcond macro instead of bootstrap conditional

* Wed Sep 27 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.6.0-1
- Fix nghttp2 version
- Update to 8.6.0
- https://nodejs.org/en/blog/release/v8.6.0/

* Wed Sep 20 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.5.0-3
- Build with bootstrap + bundle libuv for modularity
- backport patch for aarch64 debug build

* Wed Sep 13 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.5.0-2
- Disable debug builds on aarch64 due to https://github.com/nodejs/node/issues/15395

* Tue Sep 12 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.5.0-1
- Update to v8.5.0
- https://nodejs.org/en/blog/release/v8.5.0/

* Thu Sep 07 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.4.0-2
- Refactor openssl BR

* Wed Aug 16 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.4.0-1
- Update to v8.4.0
- https://nodejs.org/en/blog/release/v8.4.0/
- http2 is now supported, add bundled nghttp2
- remove openssl 1.0.1 patches, we won't be using them in fedora

* Thu Aug 10 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.3.0-1
- Update to v8.3.0
- https://nodejs.org/en/blog/release/v8.3.0/
- update V8 to 6.0
- update minimal gcc and g++ requirements to 4.9.4

* Wed Aug 09 2017 Tom Hughes <tom@compton.nu> - 1:8.2.1-2
- Bump release to fix broken dependencies

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:8.2.1-1.2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:8.2.1-1.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 21 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.2.1-1
- Update to v8.2.1
- https://nodejs.org/en/blog/release/v8.2.1/

* Thu Jul 20 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.2.0-1
- Update to v8.2.0
- https://nodejs.org/en/blog/release/v8.2.0/
- Update npm to 5.3.0
- Adds npx command

* Tue Jul 18 2017 Igor Gnatenko <ignatenko@redhat.com> - 1:8.1.4-3
- s/BuildRequires/Requires/ for http-parser-devel%%{?_isa}

* Mon Jul 17 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.1.4-2
- Rename python-devel to python2-devel
- own %%{_pkgdocdir}/npm

* Tue Jul 11 2017 Stephen Gallagher <sgallagh@redhat.com> - 1:8.1.4-1
- Update to v8.1.4
- https://nodejs.org/en/blog/release/v8.1.4/
- Drop upstreamed c-ares patch

* Thu Jun 29 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.1.3-1
- Update to v8.1.3
- https://nodejs.org/en/blog/release/v8.1.3/

* Wed Jun 28 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:8.1.2-1
- Update to v8.1.2
- remove GCC 7 patch, as it is now fixed in node >= 6.12

