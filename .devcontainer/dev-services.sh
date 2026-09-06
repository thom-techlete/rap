#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_dir="${repo_root}/logs"

declare -a SERVICES=(
  "web|8000|${repo_root}/web|uv run python manage.py runserver 0.0.0.0:8000"
  "celery-worker|-|${repo_root}/web|uv run celery -A rap_web worker --loglevel=info --concurrency=2"
  "celery-beat|-|${repo_root}/web|uv run celery -A rap_web beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
)

pid_file() {
  echo "/tmp/rap-$1.pid"
}

log_file() {
  echo "${log_dir}/$1.log"
}

is_port_open() {
  local port="$1"
  ss -ltnH "sport = :${port}" 2>/dev/null | grep -q .
}

is_pid_alive() {
  kill -0 "$1" >/dev/null 2>&1
}

service_is_running() {
  local name="$1"
  local port="$2"
  local pid_path
  local pid

  pid_path="$(pid_file "${name}")"
  if [[ -f "${pid_path}" ]]; then
    pid="$(<"${pid_path}")"
    if [[ -n "${pid}" ]] && is_pid_alive "${pid}"; then
      return 0
    fi
  fi

  [[ "${port}" != "-" ]] && is_port_open "${port}"
}

start_service() {
  local name="$1"
  local port="$2"
  local workdir="$3"
  local command="$4"
  local pid_path
  local log_path

  pid_path="$(pid_file "${name}")"
  log_path="$(log_file "${name}")"

  if service_is_running "${name}" "${port}"; then
    echo "${name} already running."
    return 0
  fi

  rm -f "${pid_path}"
  mkdir -p "${log_dir}"
  nohup setsid bash -lc "cd \"${workdir}\" && exec ${command}" \
    </dev/null >"${log_path}" 2>&1 &
  echo "$!" >"${pid_path}"
  echo "Started ${name}; log: ${log_path}"
}

stop_service() {
  local name="$1"
  local port="$2"
  local pid_path
  local pid
  local attempts=0

  pid_path="$(pid_file "${name}")"
  if [[ ! -f "${pid_path}" ]]; then
    echo "${name} not running."
    return 0
  fi

  pid="$(<"${pid_path}")"
  if [[ -z "${pid}" ]] || ! is_pid_alive "${pid}"; then
    rm -f "${pid_path}"
    echo "${name} not running; removed stale pid file."
    return 0
  fi

  echo "Stopping ${name}..."
  kill "${pid}" >/dev/null 2>&1 || true
  while is_pid_alive "${pid}" && [[ "${attempts}" -lt 20 ]]; do
    sleep 0.5
    attempts=$((attempts + 1))
  done

  if is_pid_alive "${pid}"; then
    kill -9 "${pid}" >/dev/null 2>&1 || true
  fi

  rm -f "${pid_path}"
  echo "${name} stopped."
}

wait_for_web() {
  local attempt=1
  while [[ "${attempt}" -le 60 ]]; do
    if is_port_open 8000; then
      echo "Django is ready on port 8000."
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done

  echo "Django did not become ready." >&2
  tail -n 50 "$(log_file web)" 2>/dev/null || true
  return 1
}

start_all() {
  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port workdir command <<<"${service}"
    start_service "${name}" "${port}" "${workdir}" "${command}"
  done
  wait_for_web
}

stop_all() {
  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port _workdir _command <<<"${service}"
    stop_service "${name}" "${port}"
  done
}

status_all() {
  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port _workdir _command <<<"${service}"
    if service_is_running "${name}" "${port}"; then
      echo "${name}: running"
    else
      echo "${name}: stopped"
    fi
  done
}

case "${1:-start}" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_all
    ;;
  status)
    status_all
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}" >&2
    exit 1
    ;;
esac
