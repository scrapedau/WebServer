const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors'); // For Cross-Origin Requests (optional)
const { Pool } = require('pg'); // PostgreSQL library
const createCsvWriter = require('csv-writer').createObjectCsvWriter; // CSV writer library
const nodemailer = require('nodemailer'); // Email library

// Create an Express app
const app = express();
const PORT = process.env.PORT || 3000; // Use Heroku-assigned port or default to 3000

// Middleware
app.use(bodyParser.json()); // Parse JSON data in request bodies
app.use(bodyParser.urlencoded({ extended: true })); // Parse URL-encoded data
app.use(cors()); // Allow requests from other origins (e.g., your frontend)

// PostgreSQL connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // Add your Heroku DB URI here
  ssl: {
    rejectUnauthorized: false, // This is required for Heroku's hosted PostgreSQL
  },
});

// Query function to fetch data from the database
   async function queryDatabase(
     marketType,
     postcode,
     suburb,
     minDaysOnMarket,
     maxDaysOnMarket,
     minBedrooms,
     maxBedrooms,
     minBathrooms,
     maxBathrooms,
     minCarSpaces,
     maxCarSpaces,
     property_type,
     price// Add this parameter
   ) {
     try {
       const query = `
         SELECT * FROM listings
         WHERE market_type = $1
         AND ($2::INTEGER[] IS NULL OR postcode = ANY($2::INTEGER[]))
         AND ($3::TEXT[] IS NULL OR EXISTS (SELECT 1 FROM UNNEST($3::TEXT[]) AS s WHERE LOWER(suburb) = LOWER(s)))
         AND ($4::INTEGER IS NULL OR days_on_market >= $4::INTEGER)
         AND ($5::INTEGER IS NULL OR days_on_market <= $5::INTEGER)
         AND ($6::INTEGER IS NULL OR bedrooms >= $6::INTEGER)
         AND ($7::INTEGER IS NULL OR bedrooms <= $7::INTEGER)
         AND ($8::INTEGER IS NULL OR bathrooms >= $8::INTEGER)
         AND ($9::INTEGER IS NULL OR bathrooms <= $9::INTEGER)
         AND ($10::INTEGER IS NULL OR car_spaces >= $10::INTEGER)
         AND ($11::INTEGER IS NULL OR car_spaces <= $11::INTEGER)
         AND ($12::TEXT[] IS NULL OR property_type = ANY($12::TEXT[]))
         AND ($13::TEXT[] IS NULL OR EXISTS (SELECT 1 FROM unnest($13::TEXT[]) AS price_filter WHERE price ILIKE '%' || price_filter || '%' ))
       `;

       const values = [
         marketType || null,
         postcode 
            ? postcode.split(',').map(p => parseInt(p.trim(), 10))
            : null,
         suburb
            ? suburb.split(',').map(s => s.trim())
            : null,
         minDaysOnMarket ? parseInt(minDaysOnMarket) : null,
         maxDaysOnMarket ? parseInt(maxDaysOnMarket) : null,
         minBedrooms ? parseInt(minBedrooms) : null,
         maxBedrooms ? parseInt(maxBedrooms) : null,
         minBathrooms ? parseInt(minBathrooms) : null,
         maxBathrooms ? parseInt(maxBathrooms) : null,
         minCarSpaces ? parseInt(minCarSpaces) : null,
         maxCarSpaces ? parseInt(maxCarSpaces) : null,
         Array.isArray(property_type) && property_type.length > 0 ? property_type : null,
         price ? price.split(",").map((p) => p.trim()) : null, // Split price into an array,
       ];

       const { rows } = await pool.query(query, values);
       return rows;
     } catch (error) {
       console.error('Error querying the database:', error);
       throw error;
     }
   }

const path = require('path');
const fs = require('fs');

// Function to generate a CSV file
async function generateCsv(data) {
  const fileName = `data_${Date.now()}.csv`; // Unique file name based on timestamp
  const filePath = path.join(__dirname, fileName); // Generate full path for the CSV

  // Define the CSV file's headers
  const csvWriter = createCsvWriter({
    path: filePath,
    header: [
      { id: 'market_type', title: 'Market Type' },
      { id: 'price', title: 'Price' },
      { id: 'address_line1', title: 'Address Line 1' },
      { id: 'postcode', title: 'Postcode' },
      { id: 'suburb', title: 'Suburb' },
      { id: 'state', title: 'State' },
      { id: 'bedrooms', title: 'Bedrooms' },
      { id: 'bathrooms', title: 'Bathrooms' },
      { id: 'car_spaces', title: 'Car Spaces' },
      { id: 'SQM', title: 'SQM' },
      { id: 'property_type', title: 'Property Type' },
      { id: 'days_on_market', title: 'Days on Market' },
      { id: 'listing_card_tag', title: 'Listing Card Tag' },
      { id: 'alt_image', title: 'alt_image' },
      { id: 'agent_name', title: 'Agent Name' },
      { id: 'agency_name', title: 'Agency Name' },
      {id: 'title', title: 'Title' },
      {id: 'subtitle', title: 'Subtitle' },
      {id: 'url', title: 'URL' },
      {id: 'addressplussuburb', title: 'Full Address' },
    ],
  });

  await csvWriter.writeRecords(data); // Write data to the CSV file
  console.log('CSV generated at:', filePath);

  return filePath; // Return the unique file path
}

// Function to send an email with the CSV attached
async function sendEmail(toEmail, filePath) {
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: 'marketreport.scraped@gmail.com',
      pass: 'ehwe wkzu vswx hgsz',
    },
  });

  const mailOptions = {
    from: 'sales@scraped.au',
    to: toEmail,
    subject: 'SCRAPED AU | LIVE MARKET REPORT',
    text: 'Please find your attached live market report from Scraped AU',
    attachments: [
      {
        filename: path.basename(filePath), // Use only the file name in the email
        path: filePath, // The full file path
      },
    ],
  };

  // Send the email
  try {
    await transporter.sendMail(mailOptions);
    console.log('Email sent successfully to:', toEmail);

    // Delete the file after the email is sent
    fs.unlinkSync(filePath);
    console.log('CSV file deleted:', filePath);
  } catch (error) {
    console.error('Error sending email:', error);
    throw error; // Still throw the error for handling by the caller
  }
}

// POST Route - form handler
app.post('/api/form-handler', async (req, res) => {
  try {
    const {
      market_type,
      postcode,
      suburb,
      min_days_on_market,
      max_days_on_market,
      min_bedrooms,
      max_bedrooms,
      min_bathrooms,
      max_bathrooms,
      min_car_spaces,
      max_car_spaces,
      property_type = [],
      price,
      user_email // Destructure user_email
    } = req.body;

    // Validate important fields
    if (!user_email) {
      return res.status(400).json({ error: 'User email is required.' });
    }

    console.log(`Form received for user with email: ${user_email}`);
    console.log('Querying database...');

    // 1. Query database
    const queryResult = await queryDatabase(
      market_type,
      postcode,
      suburb,
      min_days_on_market,
      max_days_on_market,
      min_bedrooms,
      max_bedrooms,
      min_bathrooms,
      max_bathrooms,
      min_car_spaces,
      max_car_spaces,
      property_type,
      price
    );

    if (queryResult.length === 0) {
      return res.status(404).json({ error: 'No results found for the specified query.' });
    }

    console.log(`Query successful! ${queryResult.length} records found.`);

    // 2. Generate CSV file
    console.log('Generating CSV...');
    const csvFilePath = await generateCsv(queryResult);

    // 3. Send email with CSV attached
    console.log('Sending email...');
    await sendEmail(user_email, csvFilePath);

    // If all actions succeed
    res.status(200).json({ message: 'Database query executed, CSV generated, and email sent successfully!' });

  } catch (error) {
    console.error('Error handling the form submission:', error);
    res.status(500).json({ error: 'An internal server error occurred.' });
  }
});

// Simple test route - GET request
app.get('/', (req, res) => {
  res.send('API is running!');
});

// Start the server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running on http://0.0.0.0:${PORT}`);
});
