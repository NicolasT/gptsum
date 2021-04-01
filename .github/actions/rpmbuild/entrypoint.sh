#!/bin/bash

set -xue -o pipefail

su - build -s /bin/bash << EOF
set -xue -o pipefail

cd /home/build/rpmbuild/SPECS
test -f python-gptsum.spec
rpmbuild -ba --define "_version $1" python-gptsum.spec

test -f /home/build/rpmbuild/SRPMS/python-gptsum-$1-1.el8.src.rpm
test -f /home/build/rpmbuild/RPMS/noarch/python3-gptsum-$1-1.el8.noarch.rpm
EOF

install -g $HOST_GID -o $HOST_UID -m 0444 \
    /home/build/rpmbuild/SRPMS/python-gptsum-$1-1.el8.src.rpm \
    /home/build/rpmbuild/RPMS/noarch/python3-gptsum-$1-1.el8.noarch.rpm \
    /artifacts/
