import boto3
import pandas as pd
import random
from datetime import datetime, timedelta
import io
import os
from dotenv import load_dotenv


load_dotenv()

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')


def generate_data(num_rows=500):
    print("Generating data with 30-day history...")
    products = ['Laptop', 'Headphones', 'Mouse', 'Keyboard', 'Monitor']
    categories = ['Electronics', 'Electronics', 'Accessories', 'Accessories', 'Electronics']
    payment_methods = ['Credit Card', 'PayPal', 'Debit Card']
    
    data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for _ in range(num_rows):
        prod_idx = random.randint(0, len(products)-1)
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        fake_timestamp = start_date + timedelta(seconds=random_seconds)
        
        row = {
            'order_id': random.randint(10000, 99999),
            'product': products[prod_idx],
            'category': categories[prod_idx],
            'price': round(random.uniform(20.0, 500.0), 2),
            'quantity': random.randint(1, 5),
            'payment_method': random.choice(payment_methods),
            'timestamp': fake_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
        }
        data.append(row)
    
    return pd.DataFrame(data)

def upload_to_s3(df):
    print(f"Uploading {len(df)} rows to S3...")
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    
    filename = f'sales_data_historical_{datetime.now().strftime("%Y%m%d%H%M")}.csv'
    
    try:
        s3.put_object(Body=csv_buffer.getvalue(), Bucket=BUCKET_NAME, Key=filename)
        print(f"✅ Success! Uploaded {filename} to bucket {BUCKET_NAME}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    df_sales = generate_data(500) 
    upload_to_s3(df_sales)