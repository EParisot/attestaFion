#!/bin/bash
gcloud config set project attestafion
git pull
gcloud builds submit --tag gcr.io/attestafion/attestafion
gcloud run deploy --image gcr.io/attestafion/attestafion --platform managed