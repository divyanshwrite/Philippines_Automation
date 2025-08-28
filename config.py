import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'quriousri',
    'user': os.getenv('PGUSER', 'fda_user'),
    'password': os.getenv('PGPASSWORD', ''),  # Set your password here or via env
    'port': 5432,
}

# Table and schema
TABLE_NAME = 'source.medical_guidelines'

# Download folder
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'Philippines_Extract')
FDA_DOWNLOAD_DIR = os.path.join(DOWNLOAD_DIR, 'fda')
PH_DOWNLOAD_DIR = os.path.join(DOWNLOAD_DIR, 'ph')

# FDA API endpoint (example, update as needed)
FDA_API_URL = 'https://www.fda.gov.ph/wp-json/wp/v2/posts?categories=latest-issuances&per_page=100&page={page}'

# PH guidance base URL
PH_GUIDANCE_URL = 'https://www.fda.gov.ph/latest-issuances/'
