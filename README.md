# FetDate

A modern dating website built with Python and Flask, featuring a Tinder-like swipe interface where users can find matches based on shared interests and fetishes.

## Features

- User registration and authentication with secure password hashing
- Persistent user profiles stored in PostgreSQL database
- Profile completion with location (country/city) and photo upload
- Separate categories for sexual fetishes and general interests/hobbies
- Modern, responsive design inspired by popular dating apps
- Tinder-like swipe interface for discovering matches
- Profile pages for each user
- List of all registered users
- Multi-language support (English and Russian)
- Dark/light theme toggle
- Photo upload functionality
- Moderation system with admin panel
- User blocking and deletion capabilities
- Admin user management

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Open your browser and go to http://127.0.0.1:5000

## How to Use

1. Register for a new account (the first user will automatically become an admin)
2. Log in with your credentials
3. Complete your profile by adding:
   - Bio
   - Country and city (with dynamic dropdown selection)
   - Profile photo
   - Interests and fetishes
4. After completing your profile, you can:
   - View your profile
   - Browse all users
   - Start swiping to discover matches

## Swipe Interface

The swipe interface allows you to:
- Swipe left ( Reject) to pass on a profile
- Swipe right ( Like) to express interest
- Swipe up for a "Super Like"
- Or use the action buttons at the bottom

## Language Support

The site supports both English and Russian languages. You can switch languages using the globe icon in the top navigation bar.

## Dark/Light Theme

FetDate supports both dark and light themes:
- Toggle between themes using the moon/sun icon in the top navigation bar
- Your theme preference is saved in your browser
- Default theme is light

## Photo Upload

Users can upload profile photos in JPG, JPEG, PNG, or GIF formats. Photos are stored in the `static/uploads` directory.

## Location Features

Users can specify their country and city during profile completion:
- First select a country from the dropdown
- Then select a city from the dynamically loaded list

## Database

FetDate uses PostgreSQL database for persistent storage:
- User profiles and authentication
- User preferences (fetishes and interests)
- Match information
- Administrative data

The database is automatically created on first run.

## Moderation System

FetDate includes a comprehensive moderation system:

### Admin Panel
- Accessible only to admin users
- Manage all registered users
- Block/unblock users
- Delete user accounts
- Promote users to admin status

### User Blocking
- Blocked users cannot access the site
- Blocked users see a special page explaining why they were blocked
- Admins can specify a reason for blocking

### First User Admin
- The first user to register automatically becomes an admin
- Admins can promote other users to admin status

## Persistent Authentication

User sessions are maintained across browser restarts, so you don't need to log in every time.

## Database Setup on Render

To set up the database on Render:

1. Create a PostgreSQL database:
   - In Render Dashboard, click "New" → "PostgreSQL"
   - Name it `fetfinder-db`
   - Select the same region as your web service
   - Choose "Free" plan
   - Click "Create Database"

2. Connect your web service to the database:
   - In your web service settings, add an environment variable:
     - Key: `DATABASE_URL`
     - Value: Copy the "External Database URL" from your PostgreSQL database

3. The database tables will be created automatically on first run.

## Stopping the Server

To stop the server, press Ctrl+C in the terminal where it's running.