#!/usr/bin/env sh
set -e
# init if needed
mkdir -p /analyzer/yara/rules
if [ -z "$(ls -A /analyzer/yara/rules)" ]; then
    unzip -d /analyzer/yara/rules /tpl/yara-rules.zip
    mv /analyzer/yara/rules/rules-master/* /analyzer/yara/rules
    rm -rf /analyzer/yara/rules/rules-master
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
