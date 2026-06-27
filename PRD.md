# Product Requirements Document (PRD)

## 1. Product Overview
**Name:** Carpediem  
**Description:** Carpediem is a specialized web application designed for a MapleStory guild/community. It tracks character progression (Level, Experience, Legion level), provides a community marketplace, and offers various utilities and calculators to assist players in optimizing their in-game resources. The application continuously scrapes official Nexon rankings to keep data up-to-date without manual intervention.

## 2. Target Audience
- **Primary Users:** Members of the "Carpediem" MapleStory community (Luna/Europe server).
- **Administrators:** Guild leaders or designated moderators who manage character rosters and marketplace listings.

## 3. Core Features & Capabilities

### 3.1. Authentication & Authorization
- **Discord OAuth2 Login:** Users authenticate securely using their Discord accounts. No passwords are required to be managed locally (except for a fallback admin account).
- **Role-Based Access Control:** 
  - Standard Users: Can view directories, use calculators, and interact with the marketplace (buy/sell).
  - Administrators: Hardcoded Discord ID in `.env` grants admin privileges. Admins can add new characters, remove characters, and moderate the marketplace.

### 3.2. Character Tracking & Directory
- **Automated Data Scraping:** The system automatically scrapes the official Nexon Global MapleStory ranking pages to fetch character classes, levels, current EXP, and Legion levels.
- **Background Scheduler:** A multi-threaded background scheduler runs automatically on server startup and daily at 11:30 AM (Peru Time) to fetch the latest EXP snapshots for all registered characters.
- **Experience History:** The app stores historical EXP data, allowing users to view progression charts (Exp History) and calculate time-to-next-level metrics.
- **Directory Grouping:** Characters are displayed in a directory, grouped by Job class and Level brackets.
- **Friends/Ally Tracking:** Support for tracking "Amigo" (Friend) characters separately from core guild members.

### 3.3. Marketplace (Mercado)
- **Item Listings:** Authenticated users can create listings to sell items. Listings include a title, description, price (in Billions "B" mesos), and an uploaded image.
- **Offer System:** Users can place price offers and comments on existing listings.
- **Moderation:** Listing owners and Administrators can delete listings or specific offers.

### 3.4. Player Utilities
- **Fragment Calculator:** Tool to calculate the required fragments for 6th job progression.
- **Symbol Calculator:** Tool to calculate Arcane/Sacred symbol costs and timeframes.
- **Starforce Calculator:** Probability and cost calculator for item enhancement.
- **Flame Calculator:** Tool to calculate bonus stats (flames) for equipment.
- **Boss HP Table:** Reference table for weekly/monthly boss HP values.

### 3.5. News & Information
- **MapleStory News Scraper:** Automatically fetches and caches the latest official news and maintenance updates from the Nexon website.
- **Maintenance Alerts:** Displays active banners on the site if a scheduled maintenance is approaching within 24 hours.

## 4. Technical Architecture

### 4.1. Technology Stack
- **Backend:** Python 3.12, Flask (Web Framework)
- **Database:** SQLite3 (Stored persistently in a Docker volume)
- **Scraping:** Requests, BeautifulSoup4, lxml
- **Frontend:** HTML5, Jinja2 Templates, Vanilla CSS/JS
- **Server:** Gunicorn (WSGI server)

### 4.2. Deployment & Infrastructure
- **Containerization:** Docker & Docker Compose.
- **Reverse Proxy:** Nginx proxying requests to the internal Gunicorn port.
- **Security:** HTTPS enabled via Certbot (Let's Encrypt).
- **Environment Management:** Sensitive credentials (Discord secrets, Admin IDs, Scheduler flags) are passed via a `.env` file injected at runtime.
- **CI/CD:** Custom `redeploy` bash scripts (`dev.sh`) handle automated `git pull`, `docker-compose build`, and restarts directly on the VPS.

## 5. Security Considerations
- **Secure Authentication:** Delegating login to Discord OAuth2 reduces liability of storing passwords.
- **Data Persistence:** Database and uploaded user images are stored in mapped Docker volumes (`/carpediem_data`) to prevent data loss on container restarts.
- **Rate Limiting (Scraping):** The background scraper implements a hardcoded delay (0.5s) between requests to prevent IP bans from Nexon's WAF.

## 6. Future Enhancements (Backlog)
- Implement pagination for the Marketplace if the number of listings grows significantly.
- Add real-time notifications via a Discord Bot when a new market item is posted.
- Provide detailed graphical analytics comparing guild member EXP gains on a weekly/monthly basis.
- Multi-language support (English/Spanish toggle) for the UI.
