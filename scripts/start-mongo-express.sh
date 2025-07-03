#!/bin/bash

echo "🍃 Starting MongoDB Express Web Interface..."
echo "📊 Database: test_database"
echo "🔐 Username: admin"
echo "🔑 Password: mountainstore123"
echo "🌐 Access URL: http://localhost:8081"
echo ""

# Set environment variables for mongo-express
export ME_CONFIG_MONGODB_SERVER="localhost"
export ME_CONFIG_MONGODB_PORT="27017"
export ME_CONFIG_BASICAUTH_USERNAME="admin" 
export ME_CONFIG_BASICAUTH_PASSWORD="mountainstore123"
export ME_CONFIG_MONGODB_ENABLE_ADMIN="true"
export ME_CONFIG_SITE_BASEURL="/"
export ME_CONFIG_SITE_COOKIEKEYNNAME="mongo-express"
export ME_CONFIG_SITE_SESSIONSECRET="mountain-store-session"
export ME_CONFIG_OPTIONS_EDITORTHEME="rubyblue"

# Start mongo-express directly
mongo-express