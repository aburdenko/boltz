#! /bin/bash
export set REGION=us-central1
export set PROJECT_ID=kallogjeri-project-345114
export set REPOSITORY_NAME=boltz-repo


cmd=$(gcloud ai endpoints create --region=$REGION --display-name=boltz-inference-endpoint --format="value(name)" | sed 's/\.$//')

echo $cmd
ENDPOINT_ID=$cmd
echo $ENDPOINT_ID
cmd="gcloud ai endpoints deploy-model $ENDPOINT_ID --region=$REGION --configuration=./deployment.yaml --display-name boltz1 --model boltz1"
echo $cmd
$cmd

echo $cmd
cmd="gcloud ai endpoints deploy-model projects/273872083706/locations/us-central1/endpoints/1997950066622464000 \
  --region=us-central1 \
  --configuration=./deployment.yaml \
  --display-name=boltz1 \
  --model=projects/273872083706/locations/us-central1/models/boltz1"
echo $cmd
$cmd

# echo $cmd
# ENDPOINT_ID=$cmd
# echo $ENDPOINT_ID
# cmd="gcloud ai endpoints deploy-model $ENDPOINT_ID --region=$REGION --configuration=./deployment.yaml --display-name boltz1 --model boltz1"
# echo $cmd
# $cmd
