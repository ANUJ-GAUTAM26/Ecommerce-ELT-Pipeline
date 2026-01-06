from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
import boto3
import pandas as pd
import io
from sqlalchemy import create_engine

# --- CONFIGURATION ---
# In a real production environment, these would be loaded via Airflow Variables or Connections.
# For this portfolio codebase, we use placeholders to maintain security.
AWS_ACCESS_KEY = 'YOUR_AWS_ACCESS_KEY'
AWS_SECRET_KEY = 'YOUR_AWS_SECRET_KEY'
BUCKET_NAME = 'your-ecommerce-bucket'
DB_CONN = 'postgresql://postgres:Your_DB_password@Your_endpoint:5432/postgres'

def extract_load_logic():
    print("⏳ Starting Extraction...")
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)['Contents']
    latest_file = sorted(objects, key=lambda x: x['LastModified'])[-1]['Key']
    print(f"   Processing file: {latest_file}")
    
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=latest_file)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    
    engine = create_engine(DB_CONN)
    df.to_sql('staging_sales', engine, if_exists='replace', index=False)
    print("✅ Data loaded to staging_sales.")

default_args = {
    'owner': 'anuj',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ecommerce_elt_daily',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval='@daily', 
    catchup=False
) as dag:


    t1_extract_load = PythonOperator(
        task_id='extract_and_load_s3_to_postgres',
        python_callable=extract_load_logic
    )


    t2_transform = PostgresOperator(
        task_id='transform_in_db',
        postgres_conn_id='postgres_default', 
        sql="""
            INSERT INTO fact_sales (order_id, product, category, total_revenue, transaction_date)
            SELECT 
                CAST(order_id AS INT),
                product,
                category,
                (CAST(quantity AS INT) * CAST(price AS DECIMAL(10,2))),
                TO_TIMESTAMP(timestamp, 'YYYY-MM-DD HH24:MI:SS')
            FROM staging_sales;
        """
    )


    t3_cleanup = PostgresOperator(
        task_id='cleanup_staging',
        postgres_conn_id='postgres_default',
        sql="TRUNCATE TABLE staging_sales;"
    )

    t1_extract_load >> t2_transform >> t3_cleanup

