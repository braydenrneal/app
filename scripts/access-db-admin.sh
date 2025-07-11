#!/bin/bash

echo "🍃 MongoDB Database Admin Interface"
echo "=================================="
echo ""
echo "🌐 Web Interface: http://localhost:8081"
echo "🔐 Username: admin"
echo "🔑 Password: mountainstore123"
echo ""
echo "📊 Current Database Stats:"
curl -s -u admin:mountainstore123 "http://localhost:8081/api/stats" | python3 -m json.tool
echo ""
echo "💡 Features:"
echo "  • View all collections and documents"
echo "  • Edit documents directly"
echo "  • Delete documents"
echo "  • Browse paginated data"
echo "  • Real-time database statistics"
echo ""
echo "🚀 To access the web interface:"
echo "  1. Open your browser"
echo "  2. Go to the URL above"
echo "  3. Enter the credentials when prompted"
echo ""