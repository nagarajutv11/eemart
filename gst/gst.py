import pandas as pd
import json
from datetime import datetime
from collections import defaultdict
import hashlib
import re

class GSTOfflineGenerator:
    def __init__(self, gstin, fp, pos_code="36"):
        """
        Initialize GST Offline Generator
        
        Args:
            gstin (str): Your GSTIN number
            fp (str): Filing period in MMYYYY format (e.g., "062025" for Jun 2025)
            pos_code (str): Place of supply code (default: "36" for Kerala)
        """
        self.gstin = gstin
        self.fp = fp
        self.pos_code = pos_code
        
    def load_data(self, filename):
        """Load sales data from CSV/Excel file"""
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename)
            else:
                df = pd.read_excel(filename)
            
            print(f"Loaded {len(df)} records from {filename}")
            return df
        except Exception as e:
            print(f"Error loading file: {e}")
            return None
    
    def load_valid_hsn_codes(self, hsn_file="HSN.csv"):
        """Load valid HSN codes from HSN.csv file"""
        try:
            # Try different encodings to handle the file
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            hsn_df = None
            
            for encoding in encodings:
                try:
                    hsn_df = pd.read_csv(hsn_file, encoding=encoding)
                    print(f"Successfully loaded HSN.csv with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if hsn_df is None:
                print("Failed to load HSN.csv with any encoding")
                return set()
            
            valid_hsn_codes = set()
            
            for _, row in hsn_df.iterrows():
                hsn_code = str(row['HSN_CD']).strip()
                if hsn_code and hsn_code != 'nan':
                    # Clean the HSN code to match the format used in JSON
                    cleaned_code = self.format_hsn_code(hsn_code)
                    if cleaned_code != '99999999':  # Skip invalid codes
                        valid_hsn_codes.add(cleaned_code)
                        # Also add the original code for backward compatibility
                        valid_hsn_codes.add(hsn_code)
            
            print(f"Loaded {len(valid_hsn_codes)} valid HSN codes")
            return valid_hsn_codes
        except Exception as e:
            print(f"Error loading HSN codes: {e}")
            return set()
    
    def extract_invalid_hsn_codes(self, json_file, original_data_file, output_file="hsn_errors.json"):
        """Extract invalid HSN codes from JSON and save to file"""
        print(f"Extracting invalid HSN codes from {json_file}...")
        
        # Load the JSON file
        try:
            with open(json_file, 'r') as f:
                gst_data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return None
        
        # Load valid HSN codes
        valid_hsn_codes = self.load_valid_hsn_codes()
        
        # Extract HSN codes from JSON
        invalid_hsn_entries = []
        valid_count = 0
        total_count = 0
        
        # Check HSN codes in the JSON
        if 'hsn' in gst_data and 'hsn_b2c' in gst_data['hsn']:
            for entry in gst_data['hsn']['hsn_b2c']:
                hsn_code = str(entry.get('hsn_sc', ''))
                total_count += 1
                
                # Check if this HSN code is invalid
                if hsn_code not in valid_hsn_codes and hsn_code != '99999999':
                    invalid_entry = {
                        'hsn': hsn_code,
                        'gst': entry.get('rt', 0)
                    }
                    invalid_hsn_entries.append(invalid_entry)
                else:
                    valid_count += 1
        
        # Save invalid HSN codes to file
        try:
            with open(output_file, 'w') as f:
                json.dump(invalid_hsn_entries, f, indent=2)
            
            print(f"Total HSN codes checked: {total_count}")
            print(f"Valid HSN codes: {valid_count}")
            print(f"Invalid HSN codes: {len(invalid_hsn_entries)}")
            print(f"Invalid HSN codes saved to {output_file}")
            
            return invalid_hsn_entries
            
        except Exception as e:
            print(f"Error saving invalid HSN codes: {e}")
            return None
    
    def format_hsn_code(self, hsn_code):
        """Format HSN code - only pad 7-digit codes to 8 digits with leading zero"""
        if not hsn_code or str(hsn_code).lower() in ['nan', 'none', 'null']:
            return '99999999'  # Default code for invalid entries
        
        # Convert to string and remove decimal points
        hsn_str = str(hsn_code).replace('.0', '')
        
        # Remove any non-digit characters
        digits_only = re.sub(r'[^\d]', '', hsn_str)
        
        if not digits_only:
            return '99999999'  # Default if no digits found
        
        # Only pad if it's exactly 7 digits
        if len(digits_only) == 7:
            return '0' + digits_only  # Add leading zero to make it 8 digits
        elif len(digits_only) == 5:
            return '0' + digits_only
        else:
            return digits_only  # Return as is for other lengths
    
    def clean_numeric_data(self, df):
        """Clean and convert numeric columns"""
        numeric_cols = ['TaxbleAmount', 'CGST', 'SGST', 'IGST', 'CESS', 'Qty', 
                       'SubTotal', 'TotalTax', 'GrandTotal']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Clean HSN codes - ensure all are 8 digits
        if 'HSNSACCode' in df.columns:
            df['HSNSACCode'] = df['HSNSACCode'].apply(self.format_hsn_code)
        
        return df
    
    def generate_b2cs(self, df):
        """Generate B2CS (B2C Small) section"""
        print("Generating B2CS section...")
        
        # Filter out cancelled transactions and zero taxable amounts
        active_df = df[(df['Cancelled'].str.upper() != 'YES') & (df['TaxbleAmount'] > 0)].copy()
        
        if active_df.empty:
            print("No valid B2CS entries found!")
            return []
        
        # Group by tax rate ONLY (combine all HSNs with same rate)
        grouped = active_df.groupby('CGST%').agg({
            'TaxbleAmount': 'sum',
            'CGST': 'sum',
            'SGST': 'sum', 
            'IGST': 'sum',
            'CESS': 'sum'
        }).reset_index()
        
        b2cs_data = []
        for _, row in grouped.iterrows():
            # Skip zero value entries
            if row['TaxbleAmount'] == 0:
                continue
                
            # Calculate total GST rate
            total_rate = row['CGST%'] * 2 if row['CGST%'] > 0 else 0
            
            # Determine supply type based on IGST amount
            sply_ty = "INTER" if row['IGST'] > 0 else "INTRA"
            
            # Create base entry
            b2cs_entry = {
                "sply_ty": sply_ty,
                "rt": total_rate,
                "typ": "OE",
                "pos": self.pos_code,
                "txval": round(row['TaxbleAmount'], 2)
            }
            
            # Add tax amounts based on supply type
            if sply_ty == "INTRA":
                b2cs_entry["camt"] = round(row['CGST'], 2)
                b2cs_entry["samt"] = round(row['SGST'], 2)
                if row['IGST'] > 0:
                    b2cs_entry["iamt"] = round(row['IGST'], 2)
            else:  # INTER
                b2cs_entry["iamt"] = round(row['IGST'], 2)
            
            # Add CESS if present
            if row['CESS'] > 0:
                b2cs_entry["csamt"] = round(row['CESS'], 2)
            else:
                b2cs_entry["csamt"] = 0
            
            b2cs_data.append(b2cs_entry)
        
        print(f"Generated {len(b2cs_data)} B2CS entries")
        return b2cs_data
    
    def generate_hsn_summary(self, df):
        """Generate HSN Summary section"""
        print("Generating HSN Summary...")
        
        # Filter out cancelled transactions and zero taxable amounts
        active_df = df[(df['Cancelled'].str.upper() != 'YES') & (df['TaxbleAmount'] > 0)].copy()
        
        if active_df.empty:
            print("No valid HSN entries found!")
            return {
                "hsn_b2c": []
            }
        
        # Group by HSN code AND tax rate to handle multiple rates per HSN
        hsn_grouped = active_df.groupby(['HSNSACCode', 'CGST%']).agg({
            'Qty': 'sum',
            'TaxbleAmount': 'sum',
            'CGST': 'sum',
            'SGST': 'sum',
            'IGST': 'sum', 
            'CESS': 'sum',
            'SubTotal': 'sum'
        }).reset_index()
        
        # Sort by HSN code first, then by GST rate
        hsn_grouped = hsn_grouped.sort_values(['HSNSACCode', 'CGST%'])
        
        hsn_b2c_data = []
        for i, row in hsn_grouped.iterrows():
            # Skip zero value entries
            if row['TaxbleAmount'] == 0 and row['Qty'] == 0:
                continue
                
            # Get formatted HSN code (already 8 digits from clean_numeric_data)
            hsn_code = str(row['HSNSACCode'])
            
            # Skip invalid HSN codes (including default code)
            if hsn_code == '99999999':
                continue
            
            # Calculate total GST rate
            total_rate = row['CGST%'] * 2 if row['CGST%'] > 0 else 0
            
            hsn_entry = {
                "num": i + 1,
                "hsn_sc": hsn_code,
                "desc": "OTHER",  # Default description
                "uqc": "OTH",  # Others (packets/units)
                "qty": round(row['Qty'], 2),
                "rt": total_rate,
                "txval": round(row['TaxbleAmount'], 2),
                "iamt": round(row['IGST'], 2),
                "camt": round(row['CGST'], 2),
                "samt": round(row['SGST'], 2),
                "csamt": round(row['CESS'], 2)
            }
            hsn_b2c_data.append(hsn_entry)
        
        hsn_data = {
            "hsn_b2c": hsn_b2c_data
        }
        
        print(f"Generated {len(hsn_b2c_data)} HSN B2C entries")
        return hsn_data
    
    def generate_doc_issue(self, df):
        """Generate Document Issue section"""
        print("Generating Document Issue section...")
        
        # Get unique transaction numbers
        unique_transactions = df['TransactionNo'].unique()
        cancelled_transactions = df[df['Cancelled'].str.upper() == 'YES']['TransactionNo'].unique()
        
        # Extract numeric part for range calculation
        def extract_number(trans_no):
            # Extract numbers from transaction number
            numbers = re.findall(r'\d+', str(trans_no))
            return int(numbers[-1]) if numbers else 0
        
        trans_numbers = [extract_number(t) for t in unique_transactions]
        
        if trans_numbers:
            from_num = min(trans_numbers)
            to_num = max(trans_numbers)
            total_issued = len(unique_transactions)
            cancelled_count = len(cancelled_transactions)
            net_issued = total_issued - cancelled_count
        else:
            from_num = to_num = total_issued = cancelled_count = net_issued = 0
        
        doc_issue_data = {
            "doc_det": [
                {
                    "doc_num": 6,
                    "doc_typ": "Receipt Voucher",
                    "docs": [
                        {
                            "num": 1,
                            "to": str(to_num),
                            "from": str(from_num),
                            "totnum": total_issued,
                            "cancel": cancelled_count,
                            "net_issue": net_issued
                        }
                    ]
                }
            ]
        }
        
        print(f"Document range: {from_num} to {to_num}")
        print(f"Total: {total_issued}, Cancelled: {cancelled_count}, Net: {net_issued}")
        return doc_issue_data
    
    def generate_checksum(self, data):
        """Generate checksum for data"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def calculate_total_taxable_value(self, df):
        """Calculate total taxable value"""
        active_df = df[(df['Cancelled'].str.upper() != 'YES') & (df['TaxbleAmount'] > 0)].copy()
        return round(active_df['TaxbleAmount'].sum(), 2)
    
    def calculate_b2cs_total(self, b2cs_data):
        """Calculate total from B2CS entries"""
        return round(sum(entry['txval'] for entry in b2cs_data), 2)
    
    def generate_offline_file(self, filename, output_filename=None):
        """Generate complete GST offline filing file"""
        print(f"Processing file: {filename}")
        print("="*50)
        
        # Load data
        df = self.load_data(filename)
        if df is None:
            return None
        
        # Clean data
        df = self.clean_numeric_data(df)
        
        # Generate sections
        b2cs_data = self.generate_b2cs(df)
        hsn_data = self.generate_hsn_summary(df)
        doc_issue_data = self.generate_doc_issue(df)
        
        # Calculate total taxable value from B2CS entries to ensure consistency
        gt = self.calculate_b2cs_total(b2cs_data)
        
        # Validate data before creating JSON
        if not b2cs_data:
            print("ERROR: No valid B2CS data found!")
            return None
        
        # Create complete offline file structure
        offline_data = {
            "gstin": self.gstin,
            "fp": self.fp,
            "version": "GST3.2.2",
            "hash": "hash",
            "b2b": [],
            "b2cl": [],
            "b2cs": b2cs_data,
            "doc_issue": doc_issue_data,
            "hsn": hsn_data
        }
        
        # Validate JSON structure
        try:
            # Test JSON serialization
            json.dumps(offline_data)
            print("JSON structure validation passed")
        except Exception as e:
            print(f"ERROR: JSON validation failed: {e}")
            return None
        
        # Save to file
        if not output_filename:
            output_filename = f"GST_Offline_{self.fp}_{self.gstin}.json"
        
        try:
            with open(output_filename, 'w') as f:
                json.dump(offline_data, f, indent=2)
        except Exception as e:
            print(f"ERROR: Failed to save file: {e}")
            return None
        
        print("="*50)
        print(f"GST Offline file generated: {output_filename}")
        print(f"B2CS entries: {len(b2cs_data)}")
        print(f"HSN B2C entries: {len(hsn_data['hsn_b2c'])}")
        print(f"Total taxable value: {gt}")
        print(f"Ready for upload to GST portal!")
        
        if offline_data:
            print("\n✅ GST Offline file generated successfully!")
            print("You can now upload this JSON file to GST portal offline utility.")
            
            # Extract invalid HSN codes from the generated JSON
            json_file = f"GST_Offline_{self.fp}_{self.gstin}.json"
            invalid_hsn_codes = self.extract_invalid_hsn_codes(json_file, filename)
            
            if invalid_hsn_codes:
                print(f"\n⚠️  Found {len(invalid_hsn_codes)} invalid HSN codes")
                print("Check hsn_errors.json for details")
            else:
                print("\n✅ All HSN codes are valid!")
        else:
            print("\n❌ Failed to generate GST offline file.")
        return offline_data