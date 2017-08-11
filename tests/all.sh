#!/bin/bash
set -e

on_exit() {
  exitcode=$?
  if [ $exitcode != 0 ] ; then
    echo -e '\e[41;33;1m'"Failure encountered!"'\e[0m'
  fi
}
trap on_exit EXIT


test_out() {
  set -e
  base_dir="$(cd "$(dirname $0)" ; pwd )"
  if [ -f "${base_dir}/../assets/out" ] ; then
    cmd="../assets/out"
  elif [ -f /opt/resource/out ] ; then
    cmd="/opt/resource/out"
  fi

  cat <<EOM >&2
------------------------------------------------------------------------------
TESTING: $1
Input:
$(cat ${base_dir}/${2}.json)
Output:
EOM

  result="$(cd $base_dir && cat ${2}.json | $cmd . 2>&1 | tee /dev/stderr)"
  echo >&2 ""
  echo >&2 "Result:"
  echo "$result" # to be passed into jq -e
}

# Env variables
export BUILD_PIPELINE_NAME='my-pipeline'
export BUILD_JOB_NAME='my-job'
export BUILD_NAME='my-build'
export BUILD_TEAM_NAME='main'

export RESOURCE_DEBUG=1

# TESTS
test_out simple_playbook out

