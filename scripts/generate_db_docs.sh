#!/bin/bash

# ==============================================================================
# Generate Database Schema Documentation using SchemaSpy
#
# This script runs SchemaSpy in a Docker container to analyze the application's
# PostgreSQL database. It generates a comprehensive, browsable HTML report
# of the database schema, including tables, columns, comments, and
# entity-relationship diagrams.
#
# The script is configured to connect to the database service defined in the
# project's docker-compose.yml file.
#
# Requirements:
# - Docker must be running.
# - The application's Docker containers (especially the database) should be
#   running (`docker-compose up`).
#
# Usage:
#   ./scripts/generate_db_docs.sh
#
# Output:
#   The generated HTML documentation will be placed in the `docs/database/`
#   directory. Open `docs/database/index.html` in your browser to view it.
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---

# Database connection details (from docker-compose.yml)
# Note: We connect to the host machine's port, not the internal Docker network.
DB_HOST="localhost"
DB_PORT="5433" # Mapped to 5432 in docker-compose.yml
DB_NAME="migration_db"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Output directory for the generated documentation
# Using a relative path from the project root
OUTPUT_DIR="$(pwd)/docs/database"

# SchemaSpy Docker image
SCHEMASPY_IMAGE="schemaspy/schemaspy:latest"

# JDBC driver for PostgreSQL
# Download it if it doesn't exist to avoid re-downloading every time.
JDBC_DIR="$(pwd)/scripts/drivers"
JDBC_JAR="postgresql-42.7.3.jar"
JDBC_PATH="${JDBC_DIR}/${JDBC_JAR}"
JDBC_URL="https://jdbc.postgresql.org/download/postgresql-42.7.3.jar"

# --- Script Logic ---

# 1. Ensure the output directory exists
echo "Ensuring output directory exists at ${OUTPUT_DIR}..."
mkdir -p "${OUTPUT_DIR}"

# 2. Download JDBC driver if it's missing
echo "Checking for PostgreSQL JDBC driver..."
if [ ! -f "${JDBC_PATH}" ]; then
    echo "JDBC driver not found. Downloading..."
    mkdir -p "${JDBC_DIR}"
    curl -L -o "${JDBC_PATH}" "${JDBC_URL}"
    echo "Driver downloaded successfully."
else
    echo "JDBC driver already exists."
fi

# 3. Pull the latest SchemaSpy image
echo "Pulling the latest SchemaSpy Docker image..."
docker pull "${SCHEMASPY_IMAGE}"

# 4. Run SchemaSpy
echo "Running SchemaSpy to generate documentation..."
# Explanation of Docker command options:
#   --rm: Automatically remove the container when it exits.
#   -v: Mount the output directory and JDBC driver into the container.
#   --net="host": Use the host's network stack. This is the simplest way to
#                 allow the container to connect to localhost on the host machine.
docker run --rm \
  -v "${OUTPUT_DIR}:/output" \
  -v "${JDBC_DIR}:/drivers" \
  --net="host" \
  "${SCHEMASPY_IMAGE}" \
    -t pgsql \
    -host "${DB_HOST}" \
    -port "${DB_PORT}" \
    -db "${DB_NAME}" \
    -u "${DB_USER}" \
    -p "${DB_PASSWORD}" \
    -dp /drivers/${JDBC_JAR} \
    -s public

echo "✅ Database documentation generated successfully!"
echo "You can view it by opening this file in your browser:"
echo "file://${OUTPUT_DIR}/index.html"
