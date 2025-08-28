import logging
import psycopg2
from psycopg2.extras import execute_values
from config import DB_CONFIG, TABLE_NAME
import uuid
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        # Table already exists with the correct schema

    def upsert_guideline(self, title, summary, issue_date, products, link_guidance, link_file, country, agency, all_text, json_data=None):
        """
        Insert or update guideline in the existing database schema
        """
        # Convert json_data to JSON string if it's a dict
        if isinstance(json_data, dict):
            json_data = json.dumps(json_data)
        
        with self.conn.cursor() as cur:
            # Check if document already exists based on link_guidance URL
            cur.execute(f"SELECT id FROM {TABLE_NAME} WHERE link_guidance = %s", (link_guidance,))
            existing = cur.fetchone()
            
            if existing:
                # Update existing record
                cur.execute(f"""
                    UPDATE {TABLE_NAME} SET
                        title = %s,
                        summary = %s,
                        issue_date = %s,
                        products = %s,
                        link_file = %s,
                        country = %s,
                        agency = %s,
                        all_text = %s,
                        json_data = %s,
                        updated_at = %s
                    WHERE link_guidance = %s
                """, (title, summary, issue_date, products, link_file, country, agency, all_text, json_data, datetime.now(), link_guidance))
                logging.info(f"   📝 Updated existing document: {title[:50]}...")
            else:
                # Insert new record
                new_id = self._get_next_id()
                cur.execute(f"""
                    INSERT INTO {TABLE_NAME} (
                        id, title, summary, issue_date, products, link_guidance, 
                        link_file, country, agency, all_text, json_data, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (new_id, title, summary, issue_date, products, link_guidance, link_file, 
                      country, agency, all_text, json_data, datetime.now(), datetime.now()))
                logging.info(f"   💾 Inserted new document: {title[:50]}...")
            
            self.conn.commit()

    def _get_next_id(self):
        """Get the next available ID for the sequence"""
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {TABLE_NAME}")
            return cur.fetchone()[0]

    def close(self):
        self.conn.close()
