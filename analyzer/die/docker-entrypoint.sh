#!/usr/bin/env bash
set -e
# exec
case "${ROLE}" in
    analyzer)
        exec /venv/bin/python /analyzer.py --config /conf/neon.yml
        ;;
    *)
        exec "$@"
        ;;
esac
