document.getElementById('loading').style.display = 'none';

document.getElementById('uploadButton').addEventListener('click', function() {
    document.getElementById('fileInput').click();
});
document.getElementById('clearButton').addEventListener('click', function() {
    totalItems = [];
    updateTable();
});
// document.getElementById('midown').addEventListener('click', function() {
//     var heads = 'Item Code *,Qty *,Price *,Mrp *,Selling Price *,Discount 1 Type*,Discount 1*,Discount 2,Type*,Discount 2*,Calculate Expiry On?(MFG/EXP),EXP/MFG Date(DD-MM-YYYY)'
//     saveTextToFile(heads, 'new mi.csv');
// });
document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('loading').style.display = 'block';
        // Create a FormData object to hold the file data
        const formData = new FormData();
        formData.append('file', file);

        // Use fetch to send the file to the server
        fetch('/upload-invoice', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            data.data.shift();
            // append to totalItems
            totalItems = totalItems.concat(data.data);
            updateTable();
            document.getElementById('loading').style.display = 'none';
        })
        .catch(error => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('output').innerText = 'Error uploading file: ' + error;
        });
    }
    event.target.value = '';
});

headers = ['S.No', 'Name', 'MRP', 'Qty', 'Rate', 'Tax %', 'Unit Cost', 'Landing Cost', 'Amount', 'Tax Amount', 'Total'];
totalItems = [];
isTaxInclusive = false;
invTotal = 0;
invTax = 0;
invAmount = 0;
round = (num) => Math.round(num * 100) / 100;
function calculate() {
    invTotal = 0;
    invTax = 0;
    invAmount = 0;
    for (const item of totalItems) {
        qty = parseFloat(item[2]);
        rate = parseFloat(item[3]);
        taxRate = parseFloat(item[4]);
        if(isTaxInclusive) {
            lc = rate;
            uc = round(rate / (1 + taxRate/100));
        } else {
            uc = rate;
            lc = round(rate + rate * taxRate/100);
        }
        item[5] = uc;
        item[6] = lc;
        taxableAmount = round(uc * qty);
        item[7] = taxableAmount;
        tax = round(taxableAmount * taxRate/100);
        item[8] = tax;
        total = round(lc * qty);
        item[9] = total;
        invTax += tax;
        invAmount += taxableAmount;
        invTotal += total;
    }
}

function updateTable() {
    calculate();
    // Create a table to display the data in output div
    const table = document.createElement('table');
    // set style name
    table.className = 'table table-bordered items-table';
    // Create the header row
    const header = table.createTHead();
    const headerRow = header.insertRow();
    for (const key of headers) {
        const th = document.createElement('th');
        th.innerText = key;
        headerRow.appendChild(th);
    }
    // Create the data rows
    const body = table.createTBody();
    count = 0;
    for (const item of totalItems) {
        const row = body.insertRow();
        count++;
        row.insertCell().innerText = count;
        for(const val of item) {
            const cell = row.insertCell();
            cell.innerText = val;
        }
    }
    document.getElementById('output').innerHTML = '';
    // Display Inv Totals. In a text format
    const details = document.createElement('div');
    details.innerHTML = `<h4>Invoice Total: ${round(invTotal)}; Invoice Tax: ${round(invTax)}; Invoice Amount: ${round(invAmount)}</h4>`;
    document.getElementById('output').appendChild(details);
    
    // Clear the output div and add the table
    document.getElementById('output').appendChild(table);
}

document.addEventListener('DOMContentLoaded', function() {
    const taxToggle = document.getElementById('taxToggle');
    isTaxInclusive = taxToggle.checked;

    // Update the variable when the checkbox state changes
    taxToggle.addEventListener('change', function() {
        isTaxInclusive = taxToggle.checked;
        console.log('Tax Inclusive:', isTaxInclusive);
        updateTable();
    });
});

function saveTextToFile(text, filename) {
    // Create a blob with the text
    const blob = new Blob([text], { type: 'text/plain' });
    
    // Create a temporary link element
    const link = document.createElement('a');
    
    // Set the download attribute with filename
    link.download = filename;
    
    // Create a URL for the blob and set it as the href
    link.href = window.URL.createObjectURL(blob);
    
    // Append link to body (required for Firefox)
    document.body.appendChild(link);
    
    // Trigger the download
    link.click();
    
    // Clean up
    document.body.removeChild(link);
    window.URL.revokeObjectURL(link.href);
}