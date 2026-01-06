import boto3
import pandas as pd
import io
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os
from dotenv import load_dotenv

load_dotenv()


AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_USER = 'postgres'
DB_NAME = 'postgres'


DB_CONN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

def run_pipeline():
    print("⏳ Extracting from S3...")
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)['Contents']
    latest_file = sorted(objects, key=lambda x: x['LastModified'])[-1]['Key']
    
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=latest_file)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    print(f"   Extracted {len(df)} rows from {latest_file}")

    print("⏳ Loading to Staging...")
    engine = create_engine(DB_CONN)
    df.to_sql('staging_sales', engine, if_exists='replace', index=False)
    print("   Data loaded to 'staging_sales'.")

    print("⏳ Transforming data...")
    sql_transform = """
    INSERT INTO fact_sales (order_id, product, category, quantity, unit_price, total_revenue, payment_method, transaction_date)
    SELECT 
        CAST(order_id AS INT),
        product,
        category,
        CAST(quantity AS INT),
        CAST(price AS DECIMAL(10,2)),
        (CAST(quantity AS INT) * CAST(price AS DECIMAL(10,2))) as total_revenue,
        payment_method,
        TO_TIMESTAMP(timestamp, 'YYYY-MM-DD HH24:MI:SS')
    FROM staging_sales
    WHERE order_id IS NOT NULL;
    """
    
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE fact_sales;")) 
        conn.execute(text(sql_transform))
        conn.commit()
        print("✅ Success! Pipeline Finished. Data is ready for Tableau.")

if __name__ == "__main__":
    run_pipeline()

