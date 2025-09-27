# Backend Deployment Guide

This guide explains how to use the `deploy_backend.sh` script to automate the deployment of your backend to Azure Container Registry (ACR).

## Overview

The `deploy_backend.sh` script automates three manual steps:
1. **Build** the Docker image from your backend code
2. **Tag** the image for Azure Container Registry
3. **Push** the image to ACR

## Prerequisites

Before using the script, ensure you have:

1. **Docker** installed and running
2. **Azure CLI** installed ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
3. **Logged into Azure**: Run `az login`
4. **ACR credentials configured**: Run `az acr login --name techjobinsights`

## Quick Start

### Basic Usage

```bash
./deploy_backend.sh
```

This will:
- Build the Docker image from `./backend/Dockerfile`
- Tag it as `techjobinsights.azurecr.io/backend:latest`
- Push it to your Azure Container Registry

### Advanced Usage

#### Skip the build step (if image already exists locally)
```bash
./deploy_backend.sh --skip-build
```

#### Build without using cache (clean build)
```bash
./deploy_backend.sh --no-cache
```

#### Show help
```bash
./deploy_backend.sh --help
```

## Workflow

### Typical Development Workflow

1. Make changes to your backend code
2. Test locally (optional)
3. Run the deployment script:
   ```bash
   ./deploy_backend.sh
   ```
4. Update your Azure deployment to use the new image
5. Restart your Azure service

### After Deployment

Once the image is pushed to ACR, you need to update your Azure service:

#### For Azure Container Instances (ACI):
```bash
az container restart --name your-container-name --resource-group your-resource-group
```

#### For Azure App Service:
```bash
az webapp restart --name your-app-name --resource-group your-resource-group
```

#### For Azure Container Apps:
```bash
az containerapp update --name your-app-name --resource-group your-resource-group --image techjobinsights.azurecr.io/backend:latest
```

## Configuration

The script uses the following default values (defined in the script):

- **Local Image Name**: `comp693_25s2_project__tan_1162169-backend`
- **ACR Registry**: `techjobinsights.azurecr.io`
- **ACR Image Name**: `backend`
- **Image Tag**: `latest`
- **Build Context**: `./backend`
- **Dockerfile**: `./backend/Dockerfile`

To customize these values, edit the variables at the top of `deploy_backend.sh`.

## Troubleshooting

### Error: "Docker is not running"
**Solution**: Start Docker Desktop and wait for it to fully initialize.

### Error: "Failed to log in to Azure ACR"
**Solution**: Run these commands manually:
```bash
az login
az acr login --name techjobinsights
```

### Error: "Failed to build image"
**Solution**: 
- Check if `backend/Dockerfile` exists
- Ensure all dependencies are properly defined in `requirements.txt`
- Try building with `--no-cache` flag

### Error: "Failed to push image"
**Solution**:
- Verify your ACR login: `az acr login --name techjobinsights`
- Check your ACR permissions
- Ensure the registry name is correct

### Permission Denied (Windows Git Bash)
If you get a permission error, the script might not be executable. You can run it with:
```bash
bash deploy_backend.sh
```

Or make it executable using Git:
```bash
git add deploy_backend.sh
git update-index --chmod=+x deploy_backend.sh
```

## Script Features

✅ **Automated build, tag, and push**  
✅ **Colored output for better readability**  
✅ **Pre-flight checks** (Docker running, ACR login)  
✅ **Error handling** with clear error messages  
✅ **Summary information** after deployment  
✅ **Flexible options** (skip build, no cache)  

## Alternative: Using Docker Compose

While docker-compose can be configured to build and push images, it's primarily designed for local development orchestration. The standalone script provides:

- Better error handling and feedback
- More control over the deployment process
- Clear separation between development (docker-compose) and deployment
- Easier integration with CI/CD pipelines later

## Integration with CI/CD (Future)

This script can be integrated into GitHub Actions or Azure DevOps pipelines:

### GitHub Actions Example:
```yaml
- name: Deploy Backend to ACR
  run: |
    az login --service-principal -u ${{ secrets.AZURE_CLIENT_ID }} -p ${{ secrets.AZURE_CLIENT_SECRET }} --tenant ${{ secrets.AZURE_TENANT_ID }}
    ./deploy_backend.sh
```

### Azure DevOps Pipeline Example:
```yaml
- script: ./deploy_backend.sh
  displayName: 'Deploy Backend to ACR'
```

## Related Files

- `docker-compose.yml` - Local development orchestration
- `backend/Dockerfile` - Backend Docker image definition
- `backend/requirements.txt` - Python dependencies

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker and Azure CLI logs
3. Ensure all prerequisites are met
4. Check Azure portal for ACR status and permissions
