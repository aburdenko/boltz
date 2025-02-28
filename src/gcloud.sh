export set REGION=us-central1
export set PROJECT_ID=kallogjeri-project-345114
export set REPOSITORY_NAME=boltz-repo
#gcloud services enable artifactregistry.googleapis.com --project kallogjeri-project-345114
#gcloud artifacts repositories create boltz-repo \
#    --repository-format=docker \
#    --location=us-central1 \
#    --project=kallogjeri-project-345114

cmd="pip -install -r requirements.txt"
echo $cmd
cmd="docker build -t boltz-image ."
echo $cmd
cmd="docker run -it --rm boltz-image"
echo $cmd
cmd="docker tag boltz-image us-central1-docker.pkg.dev/kallogjeri-project-345114/boltz-repo/boltz-image"
echo $cmd
cmd="gcloud auth configure-docker $REGION-docker.pkg.dev"
echo $cmd
cmd="docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/boltz-image"
#gcloud ai endpoints create --region=$REGION --display-name=boltz-inference-endpoint

echo $cmd
cmd=$(gcloud ai endpoints create --region=$REGION --display-name=boltz-inference-endpoint --format="value(name)" | sed 's/\.$//')

echo $cmd
ENDPOINT_ID=$cmd
echo $ENDPOINT_ID
cmd="gcloud ai endpoints deploy-model $ENDPOINT_ID --region=$REGION --configuration=~/workspace/boltz/src/boltz/deployment.yaml --display-name boltz1 --model boltz1"

echo $cmd
cmd="gcloud ai models upload \
    --region=us-central1 \
    --display-name=boltz1 \
    --container-image-uri=us-central1-docker.pkg.dev/kallogjeri-project-345114/boltz-repo/boltz-image"

echo $cmd
