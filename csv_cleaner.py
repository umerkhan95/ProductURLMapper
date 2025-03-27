import pandas as pd

# Load the CSV file
df = pd.read_csv('/Users/umerkhan/code/crawl4ai_scraper/products_export_1.csv')

# Remove duplicate rows based on the 'Handle' column
df.drop_duplicates(subset=['Handle'], inplace=True)

# Save the updated CSV file
df.to_csv('/Users/umerkhan/code/crawl4ai_scraper/products_export_1.csv', index=False)