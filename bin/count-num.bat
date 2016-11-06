@echo off
ls ksync.py ../src/ksync/*.py | xargs cat | perl -lne "{ if ($_ !~ /^\s*$/ && $_ !~ /^\s*#/) { print; } }" | wc -l
ls ksync.py ../src/ksync/*.py | xargs cat | wc -l

echo ----------
echo test code

