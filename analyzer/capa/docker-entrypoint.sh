#!/usr/bin/env sh
set -e
# init if needed
mkdir -p /analyzer/capa/rules
if [ -z "$(ls -A /analyzer/capa/rules)" ]; then
    unzip -d /analyzer/capa/rules /tpl/capa-rules.zip
    mv /analyzer/capa/rules/capa-rules-master/* /analyzer/capa/rules
    rm -rf /analyzer/capa/rules/capa-rules-master
fi
# exec
case "${ROLE}" in
    analyzer)
        exec /venv/bin/python /analyzer.py --config /conf/neon.yml
        ;;
    *)
        exec "$@"
        ;;
esac
