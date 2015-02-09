#!/usr/bin/env bash

echo -n "Enter the name of your part: "
read part_name

export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
workon gridbots

python -m gridbots.runners.spec_from_part $part_name
time python -m gridbots.compute dual_build_part
python -m gridbots.play dual_build_part
