#!/bin/bash

git config user.name 'GitHub Actions'
git config user.email 'actions@github.com'
git add .  # This will stage all changes in the repository
git commit -m "Automated data update"
git push