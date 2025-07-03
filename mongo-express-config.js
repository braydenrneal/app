module.exports = {
  mongodb: {
    // MongoDB connection settings
    server: 'localhost',
    port: 27017,
    
    // Database settings
    autoReconnect: true,
    poolSize: 4,
    
    // Admin settings
    admin: true,
    adminUsername: '',
    adminPassword: '',
    
    // Authentication settings for the database (if auth is enabled)
    auth: [
      {
        database: 'test_database',
        username: '',
        password: ''
      }
    ]
  },

  site: {
    // Web interface settings
    baseUrl: '/',
    cookieKeyName: 'mongo-express',
    cookieSecret: 'mountain-store-secret',
    host: '0.0.0.0',
    port: 8081,
    requestSizeLimit: '50mb',
    sessionSecret: 'mountain-store-session',
    sslEnabled: false,
    sslCert: '',
    sslKey: ''
  },

  // Default database
  defaultDatabase: 'test_database',

  // Database blacklist
  databaseBlacklist: ['admin', 'local', 'config'],

  // Collection blacklist
  collectionBlacklist: [],

  // Read-only mode
  readOnly: false,

  // GridFS options
  gridFSEnabled: false,

  // Authentication options
  basicAuth: {
    username: 'admin',
    password: 'mountainstore123'
  },

  options: {
    // Display options
    documentsPerPage: 10,
    editorTheme: 'rubyblue',
    
    // The options below aren't being used yet, but are available for future use
    maxPropSize: 100,
    skip: 0,
    sort: {}
  }
};