const express = require('express');
const { MongoClient } = require('mongodb');
const bodyParser = require('body-parser');
const path = require('path');

const app = express();
const PORT = 8081;
const MONGO_URL = 'mongodb://localhost:27017';
const DB_NAME = 'test_database';

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

let db;

// Connect to MongoDB
MongoClient.connect(MONGO_URL)
  .then(client => {
    console.log('✅ Connected to MongoDB');
    db = client.db(DB_NAME);
  })
  .catch(error => console.error('❌ MongoDB connection error:', error));

// Basic authentication middleware
const auth = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || authHeader !== 'Basic YWRtaW46bW91bnRhaW5zdG9yZTEyMw==') { // admin:mountainstore123
    res.set('WWW-Authenticate', 'Basic realm="Mountain Store DB Admin"');
    res.status(401).send('Authentication required');
    return;
  }
  next();
};

// Apply auth to all routes
app.use(auth);

// Routes
app.get('/', async (req, res) => {
  try {
    const collections = await db.listCollections().toArray();
    const stats = {};
    
    for (const collection of collections) {
      const count = await db.collection(collection.name).countDocuments();
      stats[collection.name] = count;
    }
    
    res.render('index', { collections: collections.map(c => c.name), stats });
  } catch (error) {
    res.status(500).send('Error: ' + error.message);
  }
});

app.get('/collection/:name', async (req, res) => {
  try {
    const collectionName = req.params.name;
    const page = parseInt(req.query.page) || 1;
    const limit = 20;
    const skip = (page - 1) * limit;
    
    const documents = await db.collection(collectionName)
      .find({})
      .skip(skip)
      .limit(limit)
      .toArray();
    
    const total = await db.collection(collectionName).countDocuments();
    const totalPages = Math.ceil(total / limit);
    
    res.render('collection', {
      collectionName,
      documents,
      currentPage: page,
      totalPages,
      total
    });
  } catch (error) {
    res.status(500).send('Error: ' + error.message);
  }
});

app.post('/collection/:name/delete/:id', async (req, res) => {
  try {
    const collectionName = req.params.name;
    const documentId = req.params.id;
    
    await db.collection(collectionName).deleteOne({ id: documentId });
    res.redirect(`/collection/${collectionName}`);
  } catch (error) {
    res.status(500).send('Error: ' + error.message);
  }
});

app.get('/collection/:name/edit/:id', async (req, res) => {
  try {
    const collectionName = req.params.name;
    const documentId = req.params.id;
    
    const document = await db.collection(collectionName).findOne({ id: documentId });
    
    if (!document) {
      return res.status(404).send('Document not found');
    }
    
    res.render('edit', { collectionName, document });
  } catch (error) {
    res.status(500).send('Error: ' + error.message);
  }
});

app.post('/collection/:name/update/:id', async (req, res) => {
  try {
    const collectionName = req.params.name;
    const documentId = req.params.id;
    
    // Parse the JSON from the form
    const updateData = JSON.parse(req.body.document);
    delete updateData._id; // Remove _id to avoid conflicts
    
    await db.collection(collectionName).updateOne(
      { id: documentId },
      { $set: updateData }
    );
    
    res.redirect(`/collection/${collectionName}`);
  } catch (error) {
    res.status(500).send('Error: ' + error.message);
  }
});

// API endpoint for quick stats
app.get('/api/stats', async (req, res) => {
  try {
    const collections = await db.listCollections().toArray();
    const stats = {};
    
    for (const collection of collections) {
      const count = await db.collection(collection.name).countDocuments();
      stats[collection.name] = count;
    }
    
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 Mountain Store DB Admin running on http://localhost:${PORT}`);
  console.log(`🔐 Username: admin`);
  console.log(`🔑 Password: mountainstore123`);
});