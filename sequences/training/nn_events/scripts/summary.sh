#!/bin/bash

find $1 -maxdepth 2 -type f -name test_trigger.score -exec echo {} \; -exec head -n 1 {} \; | paste -d" " - - | sort