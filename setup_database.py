from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load secrets from the .env file
load_dotenv()


DB_HOST = os.getenv('DB_HOST')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_USER = 'postgres'
DB_NAME = 'postgres'

CONN_STR = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'

def setup_tables():
    engine = create_engine(CONN_STR)
    
    sql_staging = """
    DROP TABLE IF EXISTS staging_sales;
    CREATE TABLE staging_sales (
        order_id TEXT,
        product TEXT,
        category TEXT,
        price TEXT,
        quantity TEXT,
        payment_method TEXT,
        timestamp TEXT
    );
    """
    
    sql_fact = """
    DROP TABLE IF EXISTS fact_sales;
    CREATE TABLE fact_sales (
        sales_key SERIAL PRIMARY KEY,
        order_id INT,
        product VARCHAR(255),
        category VARCHAR(100),
        quantity INT,
        unit_price DECIMAL(10, 2),
        total_revenue DECIMAL(10, 2),
        payment_method VARCHAR(50),
        transaction_date TIMESTAMP,
        loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with engine.connect() as conn:
        print("Creating Staging Table...")
        conn.execute(text(sql_staging))
        print("Creating Fact Table...")
        conn.execute(text(sql_fact))
        conn.commit() # Important to save changes!
        print("✅ Database Tables Created Successfully.")

if __name__ == "__main__":
    setup_tables()

