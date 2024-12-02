#!/bin/bash

export PATH=$HOME/postgresql/bin:$PATH
db_dir=~/personal-odc
db_log=/tmp/db.log

_start() {
  pg_ctl --pgdata "$db_dir" -l "$db_log" "$@" start
}

_stop() {
  pg_ctl --pgdata "$db_dir" -l "$db_log" "$@" stop
}

_status() {
  pg_ctl --pgdata "$db_dir" -l "$db_log" "$@" status
}

_log() {
  tail -f "$db_log"
}

_env() {
  echo "unset DB_PASSWORD"
  echo "unset DB_HOSTNAME"
  echo "unset DB_PORT"
  echo "unset DB_USERNAME"
  echo "unset DB_INDEX_DRIVER"
  echo "unset DB_DATABASE"
  echo "export DATACUBE_DB_URL='postgresql:///datacube?host=/tmp'"
#  echo "export ODC_EMIT_DB_URL='postgresql:///datacube?host=/tmp'"
#  echo "export ODC_ENVIRONMENT=emit"
}

_init() {
  if [ -d "$db_dir" ]; then
    echo "Database already exists at $db_dir"
    return 1
  fi
  echo "Initialising PostgreSQL data directory in $db_dir"
  initdb --pgdata "$db_dir"
  echo "Starting local PostgreSQL server"
  _start
  echo "Creating local 'datacube' database."
  createdb datacube

}

_delete() {
  if [ -d "$db_dir" ]; then
    echo "Stopping local PostgreSQL server"
    _stop
    echo "Deleting PostgreSQL data directory in $db_dir"
    rm -rf "$db_dir"
  fi
}

_fetch() {
  local db_url="${1:-$db_snapshot_s3}"
  if [ -d "$db_dir" ]; then
    echo "Database already exists at $db_dir"
    return 1
  fi
  printf "Fetching database\n %s\n %s\n" "$db_url" "$db_dir"
  mkdir -p "$db_dir"
  aws s3 cp "$db_url" - | tar -xJ -C "$db_dir"
}

_snapshot(){
  local out="/tmp/datacube-$(date +%Y%m%dT%H%M).tar.xz"
  printf "Saving to %s\n" "$out"
  (cd $db_dir && tar -c . | xz -zv -4 -T 0) > "$out"
  printf "Database snapshot created at %s\n" "$out"
  printf "To upload to S3, run:\n"
  printf "> aws s3 cp %s %s/\n" "$out" $(dirname "$db_snapshot_s3")
  printf "> aws s3 cp %s %s\n" "$out" "$db_snapshot_s3"
}

main() {
  case "$1" in
  "start")
    shift
    _start "$@"
    ;;
  "stop")
    shift
    _stop "$@"
    ;;
  "status")
    shift
    _status "$@"
    ;;
  "log")
    shift
    _log "$@"
    ;;
  "init")
    shift
    _init "$@"
    ;;
  "env")
    shift
    _env "$@"
    ;;
  "fetch")
    shift
    _fetch "$@"
    ;;
  "snapshot")
    shift
    _snapshot "$@"
    ;;
  "delete")
    shift
    _delete "$@"
    ;;
  *) echo "Invalid parameter. Please use on of 'start,stop,status,init,log,env,fetch,snapshot,delete'." ;;
  esac
}

main "$@"
