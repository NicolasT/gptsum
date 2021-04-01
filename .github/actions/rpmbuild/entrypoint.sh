#!/bin/bash

set -xue -o pipefail

install -g build -o build -m 0444 \
    $GITHUB_WORKSPACE/python-gptsum.spec \
    /home/build/rpmbuild/SPECS/
install -g build -o build -m 0444 \
    $GITHUB_WORKSPACE/dist/gptsum-$1.tar.gz \
    /home/build/rpmbuild/SOURCES/

su - build -s /bin/bash << EOF
set -xue -o pipefail

cd /home/build/rpmbuild/SPECS
test -f python-gptsum.spec
rpmbuild -ba --define "_version $1" python-gptsum.spec

test -f /home/build/rpmbuild/SRPMS/python-gptsum-$1-1.el8.src.rpm
test -f /home/build/rpmbuild/RPMS/noarch/python3-gptsum-$1-1.el8.noarch.rpm
EOF

mkdir $GITHUB_WORKSPACE/artifacts/
install -m 0444 \
    /home/build/rpmbuild/SRPMS/python-gptsum-$1-1.el8.src.rpm \
    /home/build/rpmbuild/RPMS/noarch/python3-gptsum-$1-1.el8.noarch.rpm \
    $GITHUB_WORKSPACE/artifacts/
