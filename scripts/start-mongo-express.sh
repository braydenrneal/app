#!/bin/bash

echo "🍃 Starting MongoDB Express Web Interface..."
echo "📊 Database: test_database"
echo "🔐 Username: admin"
echo "🔑 Password: mountainstore123"
echo "🌐 Access URL: http://localhost:8081"
echo ""

# Set the config file path
export ME_CONFIG_OPTIONS_EDITORTHEME="rubyblue"
export ME_CONFIG_MONGODB_SERVER="localhost"
export ME_CONFIG_MONGODB_PORT="27017"
export ME_CONFIG_BASICAUTH_USERNAME="admin"
export ME_CONFIG_BASICAUTH_PASSWORD="mountainstore123"
export ME_CONFIG_MONGODB_ENABLE_ADMIN="true"

# Start mongo-express
cd /app
mongo-express --config /app/mongo-express-config.js