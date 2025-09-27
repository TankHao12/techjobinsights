#!/bin/bash

# =============================================================================
# Backend Deployment Script for Azure Container Registry (ACR)
# =============================================================================
# This script automates the process of building, tagging, and pushing the 
# backend Docker image to Azure Container Registry.
#
# Usage:
#   ./deploy_backend.sh [OPTIONS]
#
# Options:
#   --skip-build    Skip the build step (only tag and push existing image)
#   --no-cache      Build without using cache
#   --no-cleanup    Skip cleaning up local images after deployment
#   --help          Show this help message
#
# Prerequisites:
#   - Docker installed and running
#   - Azure CLI installed and logged in (az login)
#   - ACR credentials configured (az acr login --name techjobinsights)
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOCAL_IMAGE_NAME="comp693_25s2_project__tan_1162169-backend"
ACR_REGISTRY="techjobinsights.azurecr.io"
ACR_IMAGE_NAME="backend"
IMAGE_TAG="latest"
BUILD_CONTEXT="../backend"
DOCKERFILE="../backend/Dockerfile"

# Parse command line arguments
SKIP_BUILD=false
NO_CACHE=""
CLEANUP=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-build    Skip the build step (only tag and push existing image)"
            echo "  --no-cache      Build without using cache"
            echo "  --no-cleanup    Skip cleaning up local images after deployment"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if logged into Azure ACR
check_acr_login() {
    print_warning "Checking Azure ACR login status..."
    if ! docker pull ${ACR_REGISTRY}/backend:latest > /dev/null 2>&1 && \
       ! docker manifest inspect ${ACR_REGISTRY}/backend:latest > /dev/null 2>&1; then
        print_warning "Not logged into Azure ACR or credentials expired"
        echo "Attempting to log in to Azure ACR..."
        if command -v az &> /dev/null; then
            az acr login --name techjobinsights
            if [ $? -eq 0 ]; then
                print_success "Successfully logged into Azure ACR"
            else
                print_error "Failed to log in to Azure ACR. Please run: az acr login --name techjobinsights"
                exit 1
            fi
        else
            print_error "Azure CLI not found. Please install it and run: az acr login --name techjobinsights"
            exit 1
        fi
    else
        print_success "Already logged into Azure ACR"
    fi
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"
    echo "Image: ${LOCAL_IMAGE_NAME}:${IMAGE_TAG}"
    echo "Context: ${BUILD_CONTEXT}"
    echo "Dockerfile: ${DOCKERFILE}"
    
    if docker build $NO_CACHE -t ${LOCAL_IMAGE_NAME}:${IMAGE_TAG} -f ${DOCKERFILE} ${BUILD_CONTEXT}; then
        print_success "Image built successfully"
    else
        print_error "Failed to build image"
        exit 1
    fi
}

# Tag image for ACR
tag_image() {
    print_header "Tagging Image for ACR"
    echo "Source: ${LOCAL_IMAGE_NAME}:${IMAGE_TAG}"
    echo "Target: ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG}"
    
    if docker tag ${LOCAL_IMAGE_NAME}:${IMAGE_TAG} ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG}; then
        print_success "Image tagged successfully"
    else
        print_error "Failed to tag image"
        exit 1
    fi
}

# Push image to ACR
push_image() {
    print_header "Pushing Image to ACR"
    echo "Destination: ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG}"
    
    if docker push ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG}; then
        print_success "Image pushed successfully"
    else
        print_error "Failed to push image"
        exit 1
    fi
}

# Restart Azure Web App
restart_webapp() {
    print_header "Restarting Azure Web App"
    echo "App Name: techjobsinsights-api"
    echo "Resource Group: tech-job-insights"
    
    if az webapp restart --name techjobsinsights-api --resource-group tech-job-insights; then
        print_success "Web App restarted successfully"
    else
        print_error "Failed to restart Web App"
        print_warning "You may need to restart manually using:"
        echo "  az webapp restart --name techjobsinsights-api --resource-group tech-job-insights"
        exit 1
    fi
}

# Clean up local images
cleanup_images() {
    print_header "Cleaning Up Local Images"
    
    local images_removed=0
    
    # Remove the ACR-tagged image
    if docker images -q ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG} > /dev/null 2>&1; then
        echo "Removing ACR-tagged image: ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG}"
        if docker rmi ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null; then
            print_success "Removed ACR-tagged image"
            ((images_removed++))
        else
            print_warning "Could not remove ACR-tagged image (may be in use)"
        fi
    fi
    
    # Remove the local image
    if docker images -q ${LOCAL_IMAGE_NAME}:${IMAGE_TAG} > /dev/null 2>&1; then
        echo "Removing local image: ${LOCAL_IMAGE_NAME}:${IMAGE_TAG}"
        if docker rmi ${LOCAL_IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null; then
            print_success "Removed local image"
            ((images_removed++))
        else
            print_warning "Could not remove local image (may be in use)"
        fi
    fi
    
    if [ $images_removed -eq 0 ]; then
        print_warning "No images were removed"
    else
        print_success "Cleaned up $images_removed image(s)"
    fi
    
    # Optionally prune dangling images
    echo ""
    echo "Checking for dangling images..."
    DANGLING_COUNT=$(docker images -f "dangling=true" -q | wc -l)
    if [ "$DANGLING_COUNT" -gt 0 ]; then
        print_warning "Found $DANGLING_COUNT dangling image(s)"
        echo "Run 'docker image prune' to remove them"
    else
        print_success "No dangling images found"
    fi
}

# Display deployment summary
show_summary() {
    print_header "Deployment Summary"
    echo "Remote Image: ${ACR_REGISTRY}/${ACR_IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    
    print_success "Deployment completed successfully!"
    echo ""
    echo "✓ Backend image built and pushed to Azure Container Registry"
    echo "✓ Web app restarted to pull the new image"
    if [ "$CLEANUP" = true ]; then
        echo "✓ Local images cleaned up to save disk space"
    else
        echo "⚠ Local images not cleaned up (use --no-cleanup to keep them)"
    fi
    echo ""
    echo "The backend should be live at: https://techjobsinsights-api.azurewebsites.net"
    echo ""
}

# Main execution
main() {
    print_header "Backend Deployment to Azure ACR"
    echo "Starting deployment process..."
    
    # Check prerequisites
    check_docker
    check_acr_login
    
    # Build image (unless skipped)
    if [ "$SKIP_BUILD" = false ]; then
        build_image
    else
        print_warning "Skipping build step as requested"
    fi
    
    # Tag and push
    tag_image
    push_image
    
    # Restart the web app to pull the new image
    restart_webapp
    
    # Clean up local images (unless disabled)
    if [ "$CLEANUP" = true ]; then
        cleanup_images
    else
        print_warning "Skipping cleanup as requested (--no-cleanup)"
    fi
    
    # Show summary
    show_summary
}

# Run main function
main
