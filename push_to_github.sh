#!/bin/bash

# Push A/B Testing System to GitHub
# Run: bash push_to_github.sh YOUR_GITHUB_TOKEN

TOKEN=$1

if [ -z "$TOKEN" ]; then
    echo "❌ Please provide your GitHub Personal Access Token"
    echo ""
    echo "Usage: bash push_to_github.sh YOUR_TOKEN"
    echo ""
    echo "Get token from: https://github.com/settings/tokens/new"
    echo "Required scope: 'repo'"
    exit 1
fi

echo "🚀 Pushing to GitHub..."

# Update remote with token
git remote set-url origin https://$TOKEN@github.com/ojavadli/ABtesting.git

# Push
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Pushed to GitHub!"
    echo "🌐 View at: https://github.com/ojavadli/ABtesting"
else
    echo "❌ Push failed. Check your token."
fi

