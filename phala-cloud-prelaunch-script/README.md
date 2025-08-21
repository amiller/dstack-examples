# Default Pre-launch script of Phala Cloud

## Overview

This pre-launch script for Phala Cloud handles:

- Pull private images from Docker Hub
- Pull private images from AWS ECR  
- Remove unused images and containers from local disk
- Expose App ID via `DSTACK_APP_ID` environment variable

## Private registry support

### Docker Hub Authentication

Set these encrypted environment variables:

- `DSTACK_DOCKER_USERNAME` - Your Docker Hub username
- `DSTACK_DOCKER_PASSWORD` - Your Docker Hub password or access token

### AWS ECR Authentication

Set these encrypted environment variables:

- `DSTACK_AWS_ACCESS_KEY_ID` - Your AWS access key ID
- `DSTACK_AWS_SECRET_ACCESS_KEY` - Your AWS secret access key
- `DSTACK_AWS_REGION` - AWS region for your ECR repository
- `DSTACK_AWS_ECR_REGISTRY` - Your AWS ECR registry URL
- `DSTACK_AWS_SESSION_TOKEN` - Only needed for temporary AWS credentials

## Dstack App Related

The following three environment variables will be automatically added by the default pre-launch script from Phala Cloud:

- `DSTACK_APP_ID`: The unique identifier for the Dstack App.
- `DSTACK_GATEWAY_DOMAIN`: The gateway domain for accessing the Dstack App.
- `DSTACK_APP_DOMAIN`: The default domain of the Dstack App.

NOTE: `DSTACK_APP_DOMAIN` equals to `${DSTACK_APP_ID}.${DSTACK_GATEWAY_DOMAIN}`, which acccessing port 80. It equals to `${DSTACK_APP_ID}-80.${DSTACK_GATEWAY_DOMAIN}`.
