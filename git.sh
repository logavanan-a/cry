#!/bin/sh
echo Welcome Boss
echo You want to pull or push ?
read git_name
echo Enter branch name ?
read git_branch
if [ $git_name == 'pull' ]
then
   git pull origin $git_branch
elif [ $git_name == 'push' ]
then
   echo Enter Message to commit ?
   read git_msg
   git add -A
   git status
   git commit -m"$git_msg"
   git push origin $git_branch
else
   echo "None of the condition met"
fi