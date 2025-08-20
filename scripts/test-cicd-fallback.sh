#!/bin/bash
# Test script for CI/CD fallback logic
# This simulates the deployment process locally

set -e

echo "🧪 Testing CI/CD fallback logic simulation..."

# Create test environment
TEST_DIR="/tmp/cicd-test"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Simulate .last-successful-deployment file
echo "sha-abc1234" > .last-successful-deployment

# Test function similar to the one in the workflow
test_deployment() {
  local tag="$1"
  echo "🧪 Testing deployment with tag: $tag"
  
  # Simulate different failure scenarios
  case "$tag" in
    "latest")
      echo "❌ Simulating failure with latest tag"
      return 1
      ;;
    "sha-abc1234")
      echo "✅ Simulating success with fallback tag"
      return 0
      ;;
    *)
      echo "❓ Unknown tag: $tag"
      return 1
      ;;
  esac
}

# Simulate deployment logic
NEW_IMAGE_TAG="sha-def5678"
echo "📦 New image tag: ${NEW_IMAGE_TAG}"

# Read last successful deployment tag
last_successful_tag="latest"
if [ -f .last-successful-deployment ]; then
  last_successful_tag="$(cat .last-successful-deployment)"
  echo "📋 Last successful deployment tag: $last_successful_tag"
else
  echo "📋 No previous successful deployment found, using 'latest'"
fi

# Try deployment with latest tag first
if test_deployment "latest"; then
  echo "🎉 Deployment successful with latest tag!"
  echo "$NEW_IMAGE_TAG" > .last-successful-deployment
  echo "Updated last successful deployment to $NEW_IMAGE_TAG"
else
  echo "❌ Deployment failed with latest tag, attempting fallback..."
  
  # Try with last successful tag if it's different from latest
  if [ "$last_successful_tag" != "latest" ]; then
    echo "🔄 Attempting rollback to last successful tag: $last_successful_tag"
    if test_deployment "$last_successful_tag"; then
      echo "✅ Rollback successful with tag: $last_successful_tag"
      echo "⚠️  Deployment completed using fallback. Latest changes were not deployed."
    else
      echo "💥 Rollback also failed! Manual intervention required."
      exit 1
    fi
  else
    echo "💥 No fallback available (last successful was also 'latest'). Manual intervention required."
    exit 1
  fi
fi

echo "🏁 Test completed successfully!"

# Clean up
cd /
rm -rf "$TEST_DIR"