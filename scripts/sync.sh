#!/bin/bash

branches=("os-1" "os-2" "os-3" "os-4")

for branch in "${branches[@]}"
do
    IFS=' ' read -r name <<< "$branch"
    echo "Syncing $name to remote"

	cd "$name"
    docker-compose stop
    git fetch
    git stash
    git pull
#   git rebase main
    git stash apply
    docker-compose up -d
	cd ..

    echo "Branch $name synced with remote"
done