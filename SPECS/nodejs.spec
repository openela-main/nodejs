%global with_debug 0

# PowerPC, s390x and aarch64 segfault during Debug builds
# https://github.com/nodejs/node/issues/20642
%ifarch %{power64} s390x aarch64
%global with_debug 0
%endif

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
%if %{with bootstrap}
%bcond_without bundled
%else
%bcond_with bundled
%endif

%bcond_without python3_fixup

# This macro serves to provide corepack, which is not provided for now, but might be in the future
%bcond_with corepack

# == Master Relase ==
# This is used by both the nodejs package and the npm subpackage that
# has a separate version - the name is special so that rpmdev-bumpspec
# will bump this rather than adding .1 to the end.
%global baserelease 1

%{?!_pkgdocdir:%global _pkgdocdir %{_docdir}/%{name}-%{version}}

# == Node.js Version ==
# Note: Fedora should only ship LTS versions of Node.js (currently expected
# to be major versions with even numbers). The odd-numbered versions are new
# feature releases that are only supported for nine months, which is shorter
# than a Fedora release lifecycle.
%global nodejs_epoch 1
%global nodejs_major 20
%global nodejs_minor 8
%global nodejs_patch 1
%global nodejs_abi %{nodejs_major}.%{nodejs_minor}
# nodejs_soversion - from NODE_MODULE_VERSION in src/node_version.h
%global nodejs_soversion 115
%global nodejs_version %{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}
%global nodejs_release %{baserelease}

%global nodejs_datadir %{_datarootdir}/nodejs

# == Bundled Dependency Versions ==
# v8 - from deps/v8/include/v8-version.h
# Epoch is set to ensure clean upgrades from the old v8 package
%global v8_epoch 2
%global v8_major 11
%global v8_minor 3
%global v8_build 244
%global v8_patch 8
# V8 presently breaks ABI at least every x.y release while never bumping SONAME
%global v8_abi %{v8_major}.%{v8_minor}
%global v8_version %{v8_major}.%{v8_minor}.%{v8_build}.%{v8_patch}
%global v8_release %{nodejs_epoch}.%{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}.%{nodejs_release}

# c-ares - from deps/cares/include/ares_version.h
# https://github.com/nodejs/node/pull/9332
%global c_ares_version 1.19.1

# llhttp - from deps/llhttp/include/llhttp.h
%global llhttp_version 8.1.1

# libuv - from deps/uv/include/uv/version.h
%global libuv_version 1.46.0

# nghttp2 - from deps/nghttp2/lib/includes/nghttp2/nghttp2ver.h
%global nghttp2_version 1.57.0

# nghttp3 - from deps/ngtcp2/nghttp3/lib/includes/nghttp3/version.h
%global nghttp3_version 0.7.0

# ngtcp2 from deps/ngtcp2/ngtcp2/lib/includes/ngtcp2/version.h
%global ngtcp2_version 0.8.1

# ICU - from tools/icu/current_ver.dep
%global icu_major 73
%global icu_minor 2
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

# simduft from deps/simdutf/simdutf.h
%global simduft_version 3.2.17

# ada from deps/ada/ada.h
%global ada_version 2.6.0

# OpenSSL minimum version
%global openssl_minimum 1:1.1.1

# punycode - from lib/punycode.js
# Note: this was merged into the mainline since 0.6.x
# Note: this will be unmerged in an upcoming major release
# Note: Marked as pending deprecation since 18.16.0
%global punycode_version 2.1.0

# npm - from deps/npm/package.json
%global npm_epoch 1
%global npm_version 10.1.0

# In order to avoid needing to keep incrementing the release version for the
# main package forever, we will just construct one for npm that is guaranteed
# to increment safely. Changing this can only be done during an update when the
# base npm version number is increasing.
%global npm_release %{nodejs_epoch}.%{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}.%{nodejs_release}

# Node.js 16.9.1 and later comes with an experimental package management tool
# corepack - from deps/corepack/package.json
%global corepack_version 0.20.0

# uvwasi - from deps/uvwasi/include/uvwasi.h
%global uvwasi_version 0.0.18

# histogram_c - from deps/histogram/include/hdr/hdr_histogram_version.h
%global histogram_version 0.11.8

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
# Original: https://github.com/nodejs/undici/archive/refs/tags/v5.22.1.tar.gz
# Adjustments: rm -f undici-5.21.0/lib/llhttp/llhttp*.wasm*
Source111: undici-5.26.3.tar.gz
# The WASM blob was made using wasi-sdk v14; compiler libraries are linked in.
# Version source: build/Dockerfile
Source112: https://github.com/WebAssembly/wasi-sdk/archive/wasi-sdk-14/wasi-sdk-wasi-sdk-14.tar.gz

# Disable running gyp on bundled deps we don't use
Patch1: 0001-Disable-running-gyp-on-shared-deps.patch
Patch3: nodejs-fips-disable-options.patch

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

%if %{with bundled}
Provides:      bundled(libuv) = %{libuv_version}
%else
BuildRequires: libuv-devel >= 1:%{libuv_version}
Requires:      libuv >= 1:%{libuv_version}
%endif

%if %{with bundled}
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
%if %{with corepack}
Provides: bundled(corepack) = %{corepack_version}
%endif
Provides: bundled(simduft) = %{simduft_version}
Provides: bundled(ada) = %{ada_version}

# Make sure we keep NPM up to date when we update Node.js
%if 0%{?rhel} < 8
# EPEL doesn't support Recommends, so make it strict
Requires: npm >= %{npm_epoch}:%{npm_version}-%{npm_release}%{?dist}
%else
Recommends: npm >= %{npm_epoch}:%{npm_version}-%{npm_release}%{?dist}
%endif

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


%package full-i18n
Summary: Non-English locale data for Node.js
Requires: %{name}%{?_isa} = %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}

%description full-i18n
Optional data files to provide full-icu support for Node.js. Remove this
package to save space if non-English locales are not needed.


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
%if 0%{?fedora} || 0%{?rhel} >= 8
Recommends: nodejs-docs = %{nodejs_epoch}:%{nodejs_version}-%{nodejs_release}%{?dist}
%endif

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

# Replace any instances of unversioned python' with python3
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

%if %{with python3_fixup}
pathfix.py -i %{__python3} -pn $(find -type f ! -name "*.js")
find . -type f -exec sed -i "s~/usr\/bin\/env python~/usr/bin/python3~" {} \;
find . -type f -exec sed -i "s~/usr\/bin\/python\W~/usr/bin/python3~" {} \;
sed -i "s~usr\/bin\/python2~usr\/bin\/python3~" ./deps/v8/tools/gen-inlining-tests.py
sed -i "s~usr\/bin\/python.*$~usr\/bin\/python3~" ./deps/v8/tools/mb/mb_test.py
find . -type f -exec sed -i "s~python -c~python3 -c~" {} \;
%endif

%build
# Decrease debuginfo verbosity to reduce memory consumption during final
# library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')

export CC='gcc'
export CXX='g++'
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

%{__python3} configure.py --prefix=%{_prefix} --verbose \
           --shared-openssl \
           --shared-zlib \
           --shared-brotli \
           %{!?with_bundled:--shared-libuv} \
           %{!?with_bundled:--shared-nghttp2} \
           --with-intl=small-icu \
           --with-icu-default-data-dir=%{icudatadir} \
           %{!?with_corepack:--without-corepack} \
           --openssl-use-def-ca-store \
           --openssl-default-cipher-list=PROFILE=SYSTEM

%if %{?with_debug} == 1
# Setting BUILDTYPE=Debug builds both release and debug binaries
make BUILDTYPE=Debug %{?_smp_mflags}
%else
make BUILDTYPE=Release %{?_smp_mflags}
%endif

# Extract the ICU data and convert it to the appropriate endianness
pushd deps/
tar xfz %{SOURCE3}

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

%if %{?with_debug} == 1
# Install the debug binary and set its permissions
install -Dpm0755 out/Debug/node %{buildroot}/%{_bindir}/node_g
%endif

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

%if %{with corepack}
# Corepack contains a number of executable"shims", including some for Windows
# PowerShell. Drop the executable bit for those so we don't pick up an
# automatic dependency on /usr/bin/pwsh that we cannot satisfy.
chmod -x %{buildroot}%{_prefix}/lib/node_modules/corepack/shims/*.ps1
%endif

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
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.node, '%{nodejs_version}')"
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.v8.replace(/-node\.\d+$/, ''), '%{v8_version}')"
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.ares.replace(/-DEV$/, ''), '%{c_ares_version}')"

# Ensure we have punycode and that the version matches
%{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"punycode\").version, '%{punycode_version}')"

# Ensure we have npm and that the version matches
# NODE_PATH=%{buildroot}%{_prefix}/lib/node_modules:%{buildroot}%{_prefix}/lib/node_modules/npm/node_modules %{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"npm\").version, '%{npm_version}')"
NODE_PATH=%{buildroot}%{_prefix}/lib/node_modules:%{buildroot}%{_prefix}/lib/node_modules/npm/node_modules %{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(JSON.parse(require(\"fs\").readFileSync(\"%{buildroot}%{_prefix}/lib/node_modules/npm/package.json\")).version, '%{npm_version}')"

# Make sure i18n support is working
NODE_PATH=%{buildroot}%{_prefix}/lib/node_modules:%{buildroot}%{_prefix}/lib/node_modules/npm/node_modules LD_LIBRARY_PATH=%{buildroot}%{_libdir} %{buildroot}/%{_bindir}/node --icu-data-dir=%{buildroot}%{icudatadir} %{SOURCE2}


%pretrans -n npm -p <lua>
-- Remove all of the symlinks from the bundled npm node_modules directory
-- This scriptlet can be removed in Fedora 31
base_path = "%{_prefix}/lib/node_modules/npm/node_modules/"
d_st = posix.stat(base_path)
if d_st then
  for f in posix.files(base_path) do
    path = base_path..f
    st = posix.stat(path)
    if st and st.type == "link" then
      os.remove(path)
    end
  end
end

-- Replace the npm docs directory with a symlink
-- Drop this scriptlet when F31 is EOL
path = "%{_prefix}/lib/node_modules/npm/doc"
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

-- Replace the npm docs directory with a symlink
-- Drop this scriptlet when F31 is EOL
path = "%{_prefix}/lib/node_modules/npm/html"
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

%if %{with corepack}
# corepack
%{_bindir}/corepack
%{_prefix}/lib/node_modules/corepack
%endif

%{_rpmconfigdir}/fileattrs/nodejs_native.attr
%{_rpmconfigdir}/nodejs_native.req
%license LICENSE
%doc CHANGELOG.md onboarding.md GOVERNANCE.md README.md
%doc %{_mandir}/man1/node.1*


%files devel
%if %{?with_debug} == 1
%{_bindir}/node_g
%endif
%{_includedir}/node
%{_datadir}/node/common.gypi
%{_pkgdocdir}/gdbinit


%files full-i18n
%dir %{icudatadir}
%{icudatadir}/icudt%{icu_major}*.dat


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
%doc %{_mandir}/man5/npmrc.5*
%doc %{_mandir}/man5/package-json.5*
%doc %{_mandir}/man5/package-lock-json.5*
%doc %{_mandir}/man5/npm-shrinkwrap-json.5*
%doc %{_mandir}/man5/npm-global.5.*
%doc %{_mandir}/man5/npm-json.5.*
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
* Wed Oct 18 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:20.8.1-1
- Update node and nghttp
- Add fips patch
- Fixes CVE-2023-44487 (nghttp)
- Fixes CVE-2023-45143, CVE-2023-39331, CVE-2023-39332, CVE-2023-38552, CVE-2023-39333

* Thu Aug 10 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:20.5.1-1
- Rebase to new security release
- Address CVE-2023-32002, CVE-2023-32004, CVE-2023-32558 (high)
- Address CVE-2023-32006, CVE-2023-32559 (medium)
- Address CVE-2023-32005, CVE-2023-32003 (low)
- Resolves: #2186718
- Resolves RHELPLAN-155624

* Thu Jul 27 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:20.5.0-1
- Update to v20.5.0
- Remove dtrace support
- bcond corepack, so we don't provide it by default
- Decrease debuginfo verbosity for all arches
- Resolves: #2186718
- Resolves RHELPLAN-155624

* Wed Jul 12 2023 Jan Staněk <jstanek@redhat.com> - 1:18.16.1-1
- Rebase to 18.16.1
  Resolves: rhbz#2188290 rhbz#2166926
  Resolves: CVE-2023-30581 CVE-2023-30588 CVE-2023-30589 CVE-2023-30590
- Replace /usr/etc/npmrc symlink with builtin configuration
  Resolves: rhbz#2222287

* Tue May 30 2023 Jan Staněk <jstanek@redhat.com> - 1:18.14.2-3
- Update bundled c-ares to 1.19.1
  Resolves: CVE-2022-4904
  Resolves: CVE-2023-31124 CVE-2023-31130 CVE-2023-31147 CVE-2023-32067

* Tue Mar 21 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:18.14.2-2
- Provide simduft

* Tue Mar 21 2023 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:18.14.2-1
- Rebase to 18.14.2
- Resolves: #2178086
- Resolves: CVE-2022-25881, CVE-2023-23936, CVE-2023-24807
- Resolves: CVE-2023-23918, CVE-2023-23919, CVE-2023-23920

* Fri Nov 18 2022 Jan Staněk <jstanek@redhat.com> - 1:18.12.1-2
- Update version of bundled histogram

* Wed Nov 09 2022 Jan Staněk <jstanek@redhat.com> - 1:18.12.1-1
- Rebase to version 18.12.1
  Resolves: rhbz#2125580 CVE-2022-43548 CVE-2022-3517

* Tue Sep 27 2022 Jan Staněk <jstanek@redhat.com> - 1:18.9.1-1
- Rebase to version 18.9.1
  Resolves: CVE-2022-35255 CVE-2022-35256

* Fri Aug 26 2022 Jan Staněk <jstanek@redhat.com> - 1:18.8.0-1
- Rebase to version 18.8.0
- Include sources for WASM blobs

* Fri Jul 15 2022 Jan Staněk <jstanek@redhat.com> - 1:18.6.0-1
- Rebase to version 18.6.0
  Resolves: CVE-2022-32212 CVE-2022-32213 CVE-2022-32214 CVE-2022-32215
  Resolves: CVE-2022-29244

* Tue May 31 2022 Jan Staněk <jstanek@redhat.com> - 1:18.2.0-1
- Rebase to version 18.2.0

* Mon Apr 25 2022 Jan Staněk <jstanek@redhat.com> - 1:16.14.0-5
- Unify configure calls into single command
- Refactor bootstrap-related parts
- Decouple dependency bundling from bootstrapping

* Mon Apr 11 2022 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.14.0-4
- Apply lock file validation fixes
- Resolves: CVE-2021-43616
- Resolves: RHBZ#2070013

* Mon Dec 06 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.13.1-3
- Resolves: RHBZ#2026329
- Add corepack to spec

* Mon Dec 06 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.13.1-2
- Resolves: RHBZ#2026329
- Update npm version test

* Thu Dec 02 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.13.1-1
- Resolves: RHBZ#2014132, RHBZ#2014126, RHBZ#2013828, RHBZ#2024920
- Resolves: RHBZ#2026329
- Rebase to LTS release and to fix multiple low and medium CVEs

* Mon Sep 13 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.8.0-1
- Resolves CVE-2021-32803, CVE-2021-32804, CVE-2021-37701, CVE-2021-37712
- Resolves: RHBZ#1993948, RHBZ#1993941, RHBZ#2000151, RHBZ#2002176

* Mon Aug 30 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.7.0-2
- Resolves CVE-2021-22930, CVE-2021-22931, CVE-2021-22939,
- CVE-2021-22940, CVE-2021-32803, CVE-2021-32804, CVE-2021-3672
- Resolves: RHBZ#1988608, RHBZ#1993816, RHBZ#1993810
- Resolves: RHBZ#1993097, RHBZ#1993948, RHBZ#1993941, RHBZ#1994963
- fix python3 in gyp

* Wed Aug 18 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.7.0-1
- Resolves CVE-2021-22930, CVE-2021-22931, CVE-2021-22939,
- CVE-2021-22940, CVE-2021-32803, CVE-2021-32804, CVE-2021-3672
- Resolves: RHBZ#1988608, RHBZ#1993816, RHBZ#1993810
- Resolves: RHBZ#1993097, RHBZ#1993948, RHBZ#1993941, RHBZ#1994963

* Fri Jul 09 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.4.2-1
- Resolves: RHBZ#1979847
- Resolves CVE-2021-22918(libuv)
- Use system cipher list(1842826, 1952915)

* Tue May 11 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:16.1.0-1
- Resolves: RHBZ#1953991
- Rebase to v16.x
- Update version of gcc and gcc-c++ needed
- Remove libs conditionals
- Remove unused patches
- Bundle nghttp3 and ngtcp2

* Mon Mar 01 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.16.0-2
- Resolves RHBZ#1930775
- remove --debug-nghttp2 option

* Mon Mar 01 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.16.0-1
- Resolves CVE-2021-22883 CVE-2021-22884
- Resolves: RHBZ#1934566, RHBZ#1934599
- Rebase, remove ini patch

* Tue Jan 26 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.15.4-2
- Add patch for yarn crash
- Resolves: RHBZ#1915296

* Tue Jan 19 2021 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.15.4-1
- Security rebase to 14.15.4
- https://nodejs.org/en/blog/vulnerability/january-2021-security-releases/
- Resolves: RHBZ#1913001, RHBZ#1912953
- Resolves: RHBZ#1912636, RHBZ#1898602, RHBZ#1898768, RHBZ#1893987, RHBZ#1893184

* Thu Oct 29 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.15.0-1
- Resolves: RHBZ#1858864
- Update to LTS release

* Mon Sep 21 2020 Jan Staněk <jstanek@redhat.com> - 1:14.11.0-1
- Security update to 14.11.0

* Wed Jun 03 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.4.0-1
- Security update to 14.4.0
- Resolves: RHBZ#1815402

* Thu May 21 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.3.0-1
- Update to 14.3.0
- Fix optflags to save memory
- Resolves: RHBZ#1815402

* Wed May 06 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:14.2.0-1
- Update to 14.2.0
- build with python3 only
- some clean up

* Tue Mar 17 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:12.16.1-2
- Fix CVE-2020-10531

* Thu Feb 20 2020 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:12.16.1-1
- Rebase to 12.16.1

* Wed Jan 15 2020 Jan Staněk <jstanek@redhat.com> - 1:12.14.1-1
- Rebase to 12.14.1

* Fri Nov 29 2019 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:12.13.1-1
- Resolves: RHBZ# 1773503, update to 12.13.1
- minor clean up and sync with Fedora spec
- turn off debug builds

* Thu Aug 01 2019 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:12.4.0-2
- Add condition to libs

* Wed Jun 12 2019 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:12.4.0-1
- Update to v12.x
- Add v8-devel and libs subpackages from fedora

* Thu Mar 14 2019 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:10.14.1-2
- move nodejs-packaging BR out of conditional

* Tue Dec 11 2018 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:10.14.1-1
- Resolves RHBZ#1644207
- fixes node-gyp permissions
- rebase

* Thu Oct 11 2018 Jan Staněk <jstanek@redhat.com> - 1:10.11.0-2
- BuildRequire nodejs-packaging for proper npm dependency generation
- Resolves: rhbz#1615947

* Mon Oct 08 2018 Jan Staněk <jstanek@redhat.com> - 1:10.11.0-1
- Rebase to 10.11.0
- Import changes from fedora
- Resolves: rhbz#1621766

* Mon Jul 30 2018 Zuzana Svetlikova <zsvetlik@redhat.com> - 1:10.7.0-5
- Import sources from fedora
- Allow using python2 at %%build and %%install
- turn off debug for aarch64

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

