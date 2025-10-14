#!/usr/bin/env sh
set -e
# prepare data directory if needed
mkdir -p /data
# prepare configuration directory if needed
mkdir -p /conf
if [ ! -f /conf/neon.yml ]; then
    cp /tpl/neon.dist.yml /conf/neon.yml
fi
if [ ! -f /conf/constant.yml ]; then
    cp /tpl/constant.dist.yml /conf/constant.yml
fi
# prepare analyzer directory if needed
mkdir -p /analyzer
# exec depending on ROLE
case "${ROLE}" in
    server)
        exec /venv/bin/neon-server --config /conf/neon.yml
        ;;
    synchronizer)
        exec /venv/bin/neon-synchronizer --config /conf/neon.yml
        ;;
    *)
        exec "$@"
        ;;
esac
