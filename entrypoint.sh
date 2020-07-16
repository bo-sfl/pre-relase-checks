#!/bin/sh -l
touch pre_release_check.log
python /run_checks.py
cat pre_release_check.log

msg=$(tr '\n' ' ' < pre_release_check.log)
if [ $(cat pre_release_check.log | wc -l) -eq 0 ]; then
  echo "::set-output name=message::Pre-release check passed"
else
  echo "::set-output name=message::$msg"
fi


if [ $(cat pre_release_check.log | wc -l) -eq 0 ]; then
  exit 0
else
  exit 1
fi