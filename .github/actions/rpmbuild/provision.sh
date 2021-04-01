#!/bin/bash

set -xue -o pipefail

dnf install --assumeyes epel-release
dnf install --assumeyes --enablerepo="powertools" \
	dnf-plugins-core \
        epel-rpm-macros \
	python3-devel \
	python3-setuptools \
	"python3dist(dataclasses)" \
	"python3dist(importlib-metadata)" \
	"python3dist(packaging)" \
	"python3dist(py)" \
	"python3dist(pytest)" \
	"python3dist(pytest-benchmark)" \
	"python3dist(pytest-mock)" \
	rpm-build \
	rpmdevtools
dnf clean all

useradd -m -U build
su - build -s /bin/bash << EOF
set -xue -o pipefail

rpmdev-setuptree

cat > /home/build/.rpmmacros << EOF2
%_topdir %(echo \\\$HOME)/rpmbuild
EOF2
EOF
