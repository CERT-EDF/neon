# =============================================================================
# BUILD IMAGE
# =============================================================================
FROM python:3.12-alpine AS build
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
ENV CAPA_RULES_URL=https://github.com/mandiant/capa-rules/archive/refs/heads/master.zip
# -----------------------------------------------------------------------------
# COPY PRE-BUILT PACKAGES (OPTIONAL)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
# -----------------------------------------------------------------------------
# SETUP VENV
# -----------------------------------------------------------------------------
RUN apk add build-base curl linux-headers && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    /venv/bin/uv pip install --python /venv/bin/python edf-neon-server flare-capa && \
    mkdir /tpl && \
    curl -L -o /tpl/capa-rules.zip ${CAPA_RULES_URL}
# =============================================================================
# PRODUCTION IMAGE
# =============================================================================
FROM python:3.12-alpine AS production
# -----------------------------------------------------------------------------
# FINAL SETUP
# -----------------------------------------------------------------------------
RUN apk add unzip && \
    mkdir -p /analyzer/capa && \
    ln -s /venv/bin/capa /analyzer/capa/capa
# -----------------------------------------------------------------------------
# COPY FROM BUILD IMAGE
# -----------------------------------------------------------------------------
COPY --from=build /tpl /tpl
COPY --from=build /venv /venv
# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------
COPY analyzer.py /analyzer.py
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
