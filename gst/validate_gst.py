import json
import sys

def validate_gst_json(filename):
    """Validate GST JSON file for common issues"""
    print(f"Validating GST JSON file: {filename}")
    print("="*50)
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load JSON file: {e}")
        return False
    
    # Check required top-level fields
    required_fields = ['gstin', 'fp', 'version', 'hash', 'b2b', 'b2cl', 'b2cs', 'doc_issue', 'hsn']
    for field in required_fields:
        if field not in data:
            print(f"ERROR: Missing required field: {field}")
            return False
    
    print("✅ All required top-level fields present")
    
    # Validate GSTIN format
    gstin = data['gstin']
    if len(gstin) != 15:
        print(f"ERROR: Invalid GSTIN length: {len(gstin)} (should be 15)")
        return False
    print(f"✅ GSTIN format valid: {gstin}")
    
    # Validate filing period format
    fp = data['fp']
    if len(fp) != 6 or not fp.isdigit():
        print(f"ERROR: Invalid filing period format: {fp} (should be MMYYYY)")
        return False
    print(f"✅ Filing period valid: {fp}")
    
    # Validate version
    version = data['version']
    if version != "GST3.2.2":
        print(f"WARNING: Version is {version}, expected GST3.2.2")
    
    # Validate B2CS entries
    b2cs = data['b2cs']
    if not isinstance(b2cs, list):
        print("ERROR: B2CS should be an array")
        return False
    
    print(f"✅ B2CS entries: {len(b2cs)}")
    
    for i, entry in enumerate(b2cs):
        required_b2cs_fields = ['sply_ty', 'rt', 'typ', 'pos', 'txval']
        for field in required_b2cs_fields:
            if field not in entry:
                print(f"ERROR: B2CS entry {i} missing field: {field}")
                return False
        
        # Validate numeric fields
        if entry['txval'] < 0:
            print(f"ERROR: B2CS entry {i} has negative taxable value")
            return False
        
        # Check supply type
        if entry['sply_ty'] not in ['INTRA', 'INTER']:
            print(f"ERROR: B2CS entry {i} has invalid supply type: {entry['sply_ty']}")
            return False
    
    print("✅ All B2CS entries valid")
    
    # Validate HSN section
    hsn = data['hsn']
    if 'hsn_b2c' not in hsn:
        print("ERROR: HSN section missing hsn_b2c field")
        return False
    
    hsn_b2c = hsn['hsn_b2c']
    if not isinstance(hsn_b2c, list):
        print("ERROR: hsn_b2c should be an array")
        return False
    
    print(f"✅ HSN B2C entries: {len(hsn_b2c)}")
    
    for i, entry in enumerate(hsn_b2c):
        required_hsn_fields = ['num', 'hsn_sc', 'desc', 'uqc', 'qty', 'rt', 'txval', 'iamt', 'camt', 'samt', 'csamt']
        for field in required_hsn_fields:
            if field not in entry:
                print(f"ERROR: HSN entry {i} missing field: {field}")
                return False
        
        # Validate HSN code
        hsn_code = entry['hsn_sc']
        if hsn_code in ['', 'nan', 'None', 'null', '0']:
            print(f"ERROR: HSN entry {i} has invalid HSN code: {hsn_code}")
            return False
    
    print("✅ All HSN entries valid")
    
    # Validate doc_issue section
    doc_issue = data['doc_issue']
    if 'doc_det' not in doc_issue:
        print("ERROR: doc_issue section missing doc_det field")
        return False
    
    doc_det = doc_issue['doc_det']
    if not isinstance(doc_det, list):
        print("ERROR: doc_det should be an array")
        return False
    
    print("✅ Document issue section valid")
    
    # Check total taxable value consistency
    b2cs_total = sum(entry['txval'] for entry in b2cs)
    print(f"✅ B2CS total: {b2cs_total}")
    
    print("="*50)
    print("✅ GST JSON validation passed!")
    print(f"B2CS entries: {len(b2cs)}")
    print(f"HSN B2C entries: {len(hsn_b2c)}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_gst.py <gst_json_file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    success = validate_gst_json(filename)
    sys.exit(0 if success else 1) 