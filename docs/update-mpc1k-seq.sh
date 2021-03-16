#!/bin/bash
echo just copying README.md...
tail -n+4 ../seq/README.md > _posts/mpc1k-seq_README.md

if [ "$1" = "doit"  ]; then
  echo "commiting and pushing..."
  git add _posts/mpc1k-seq_README.md 
  git commit -m "mpc1k-seq_README.md update"
  git push
else
  echo "to also commit and push, add argument \"doit\""
fi
