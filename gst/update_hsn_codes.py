import pandas as pd
import sys

def update_hsn_codes():
    """
    Update HSNSACCode in InvoiceDetails.csv by matching SKU with correct_data.csv
    """
    try:
        # Read the correct data file
        print("Reading correct_data.csv...")
        correct_data = pd.read_csv('correct_data.csv')
        
        # Create a dictionary mapping SKU to HSN code
        sku_to_hsn = dict(zip(correct_data['SKU'], correct_data['HSN']))
        
        print(f"Loaded {len(sku_to_hsn)} SKU-HSN mappings from correct_data.csv")
        
        # Read the invoice details file
        print("Reading InvoiceDetails.csv...")
        invoice_data = pd.read_csv('InvoiceDetails.csv')
        
        print(f"Loaded {len(invoice_data)} records from InvoiceDetails.csv")
        
        # Convert HSNSACCode column to string
        print("Converting HSNSACCode column to string...")
        invoice_data['HSNSACCode'] = invoice_data['HSNSACCode'].astype(str)
        
        # Count how many records will be updated
        matching_skus = invoice_data['SKU'].isin(sku_to_hsn.keys())
        update_count = matching_skus.sum()
        
        print(f"Found {update_count} records with matching SKUs")
        
        # Update the HSNSACCode column where SKU matches
        invoice_data.loc[matching_skus, 'HSNSACCode'] = invoice_data.loc[matching_skus, 'SKU'].map(sku_to_hsn)
        
        # Write the updated data to a new file
        output_file = 'InvoiceDetails_updated.csv'
        print(f"Writing updated data to {output_file}...")
        invoice_data.to_csv(output_file, index=False)
        
        print(f"Successfully updated {update_count} records and saved to {output_file}")
        
        # Show some statistics
        print("\nUpdate Statistics:")
        print(f"Total records in InvoiceDetails.csv: {len(invoice_data)}")
        print(f"Records with matching SKUs: {update_count}")
        print(f"Records without matching SKUs: {len(invoice_data) - update_count}")
        
        # Show some examples of updated records
        updated_records = invoice_data[matching_skus][['SKU', 'HSNSACCode', 'ItemName']].head(5)
        if not updated_records.empty:
            print("\nSample updated records:")
            print(updated_records.to_string(index=False))
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_hsn_codes() 