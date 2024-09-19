projectName="Codebuildcft"
if [ "$#" -eq 1 ]; then
  aws --profile $1 codebuild create-webhook --no-verify-ssl --project-name ${projectName} --filter-groups file://webhook.json --build-type "BUILD"
else
  echo "Must provide gossamer3 aws profile"
fi