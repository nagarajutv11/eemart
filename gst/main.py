from gst import GSTOfflineGenerator

generator = GSTOfflineGenerator(
    gstin="36BNFPP4883B1ZV",     # Your 15-digit GSTIN
    fp="092025",                 # Quarter end month + year (MMYYYY)
    pos_code="36"               # Kerala code
)

# Generate the offline file
generator.generate_offline_file("InvoiceDetails_updated.csv")