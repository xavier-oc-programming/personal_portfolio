# Xavier Ocón Capdeville — Projects

## Personal Portfolio Website

**Status:** Live at xavieroc.dev
**Repository:** github.com/xavier-oc-programming/personal_portfolio
**Category:** Web Development

### Overview
A production-grade portfolio website built with Flask and PostgreSQL, deployed on Railway with full CI/CD. This is Xavier's flagship project — it demonstrates his ability to build, test, and ship a complete full-stack web application.

### Technical Stack
- **Backend:** Flask (Python), SQLAlchemy ORM, WTForms, Flask-WTF
- **Database:** PostgreSQL (production on Railway), SQLite (local development)
- **Frontend:** Bootstrap 5, custom CSS design system, vanilla JavaScript
- **Infrastructure:** Docker, GitHub Actions CI/CD, Railway deployment
- **Testing:** pytest, pytest-flask — automated test suite covering public routes, admin routes, and the REST API
- **Email:** Resend API for contact form notifications
- **Other:** CORS, CSRF protection, admin authentication, rate limiting, honeypot spam protection

### Key Features
- Custom admin dashboard for managing projects, screenshots, and messages
- Versioned REST API (GET /api/v1/projects, GET /api/v1/projects/{slug}) with full documentation
- Project filtering by category (web, data, software), tag, and sort order
- Contact form with multi-layer spam protection (honeypot, timing check, rate limiting, CSRF)
- GitHub Actions workflow: runs pytest on every push and PR, deploys to Railway on merge to main
- Full SEO: Open Graph tags, JSON-LD structured data, sitemap.xml, robots.txt, canonical URLs
- AI Portfolio Assistant with RAG (Retrieval-Augmented Generation) using Gemini 1.5 Flash and local sentence-transformer embeddings

---

## Data Preprocessing Pipeline

**Status:** Published
**Repository:** github.com/xavier-oc-programming/data-preprocessing-pipeline
**Category:** Data Analysis

### Overview
A reusable, class-based data preprocessing pipeline built on the NYC Airbnb Open Dataset (48,895 rows). Demonstrates Xavier's ability to structure analytical Python code around solid OOP principles and apply standard ML preprocessing techniques.

### Technical Stack
- **Libraries:** Pandas, NumPy, scikit-learn, Matplotlib, Seaborn
- **Dataset:** NYC Airbnb Open Dataset — 48,895 rows, 16 columns

### Architecture
The pipeline uses a clean class-based design with four specialised components:
- **DataLoader** — loads and validates the raw CSV dataset
- **DataCleaner** — handles missing values, outlier capping (IQR method), and feature encoding
- **DataVisualizer** — generates 5 exploratory data analysis visualisations
- **PipelineReport** — summarises preprocessing steps and outputs a final cleaned dataset

### Preprocessing Steps
- Missing value imputation (median for numeric, mode for categorical)
- IQR-based outlier capping for price and other skewed numeric features
- MinMaxScaler for numerical feature normalisation
- Label encoding for categorical columns
- 5 EDA visualisations: price distribution, room type breakdown, neighbourhood map, correlation heatmap, availability scatter plot

---

## 50+ Python Projects on GitHub

**Repository:** github.com/xavier-oc-programming
**Category:** Software / Automation / Web / Data

### Overview
Over 50 Python projects built between July 2024 and the present to develop and demonstrate programming skills across a wide range of domains. Each project is published on GitHub with a README.

### Project Categories

**OOP and Software Design**
- Refactored classic patterns (coffee machine, turtle crossing, blackjack) into clean OOP architecture
- Demonstrated class design, inheritance, encapsulation, and separation of concerns

**Web Development (Flask)**
- Multiple Flask applications including a blog platform, a login system, and a to-do list app
- Database-backed projects using SQLAlchemy and SQLite

**Automation and Web Scraping**
- Gym booking bot: automated gym class reservations using Selenium and Playwright
- Internet speed Twitter bot: measures internet speed and tweets results via the Twitter API
- Tinder bot: automated profile swiping with keyboard shortcut handling via PyAutoGUI
- Amazon price tracker: monitors product prices and sends email alerts

**Data Analysis**
- Analysis scripts using Pandas and Matplotlib on public datasets
- Exploratory data analysis notebooks

**Games and CLI Tools**
- Turtle-based games (crossing, pong, snake)
- Command-line tools for file management, productivity, and text processing
- Trivia quiz app with API-fetched questions

**APIs and Integration**
- Projects consuming RESTful APIs (weather, trivia, astronomy, messaging)
- Habit-tracking app integrating with external APIs via Pixela

### GitHub Profile
All projects are public and can be browsed at github.com/xavier-oc-programming. Each repo includes a description, README, and clean commit history.
