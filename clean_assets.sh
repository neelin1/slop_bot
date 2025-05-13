#!/bin/bash

# Clean assets script for the character conversation generator
# This script removes all files in the info_videos/assets directory while preserving the folder structure

BASE_DIR="info_videos/assets"

# Make sure the base directory exists
if [ ! -d "$BASE_DIR" ]; then
  echo "❌ Error: Assets directory not found at $BASE_DIR"
  exit 1
fi

echo "🧹 Cleaning out assets directory while preserving folder structure..."

# List of subdirectories to preserve
SUBDIRS=(
  "audio"
  "audio/conversation" 
  "content_images"
  "teachers"
  "output"
)

# First, create a temporary backup of the directory structure
echo "📁 Creating backup of directory structure..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/assets_backup_$TIMESTAMP"
mkdir -p $BACKUP_DIR

# Backup the directory structure
for subdir in "${SUBDIRS[@]}"; do
  mkdir -p "$BACKUP_DIR/$subdir"
done

# Count files before cleaning
FILE_COUNT=$(find "$BASE_DIR" -type f | wc -l | tr -d ' ')
echo "📊 Found $FILE_COUNT files to remove"

# Remove files but preserve .gitkeep files if they exist
echo "🗑️ Removing files..."
find "$BASE_DIR" -type f -not -name ".gitkeep" -delete

# Create empty subdirectories in case some were missing
echo "🔨 Recreating directory structure..."
for subdir in "${SUBDIRS[@]}"; do
  mkdir -p "$BASE_DIR/$subdir"
  # Add .gitkeep to ensure empty directories are tracked in git
  touch "$BASE_DIR/$subdir/.gitkeep"
done

# Confirm operation completed
echo "✅ Done! Assets directory cleaned while preserving structure."
echo "   Directory structure backed up to: $BACKUP_DIR" 