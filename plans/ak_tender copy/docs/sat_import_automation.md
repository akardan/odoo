# SAT Import Automation Documentation

This document describes how to use the SAT import functionality in automated jobs, such as scheduled actions or mail processing jobs.

## Overview

The SAT import functionality allows importing tender definitions from Excel files. The implementation is designed to be used both from the UI wizard and from automated jobs.

### Tender Type Determination

The import process determines the tender type primarily based on the material group code:

- **Direct Tender Types (direct)**:
  - 1000-series: Etken Madde, Yardımcı Madde, Pellet Etken Madde
  - 2000-series: Granül/Bulk, Tablet/kapsül, Kaplı Tablet, etc.
  - 3000-series: Katı Ürünler, Likit Ürünler, etc.
  - 4000-series: PVC, Alüminyum Folyo, Şişe, etc.

- **Promotion Tender Types (promotion)**:
  - 5000-series: Promosyon
  - 7000-series: Tanıtım Numuneleri, Tanıtım Malzemeleri

- **Indirect Tender Types (indirect)**:
  - 6000-series: Fason İşçilik, Laboratuar Test, Eğitim-Danışmanlık, etc.
  - 8000-series: Satış Hizmet
  - 9000-series: Demirbaş, Yedek Parça, etc.

If the material group is not available, the system falls back to using the production location:
- 2100 (İlko): direct
- 2000 (Merkez): indirect
- 1100 (İlkopol): indirect

## Import Function

The main import function is `import_sat_from_file` in the `import.sat.wizard` model. This function can be called from any Python code in Odoo, including scheduled actions and custom mail processing jobs.

### Function Signature

```python
def import_sat_from_file(self, file_data, file_name, sheet_name='ILP(300)', update_existing=True):
    """
    Automated import function for SAT data from Excel file
    
    Args:
        file_data (bytes): The binary content of the Excel file
        file_name (str): The name of the file
        sheet_name (str): The name of the sheet to import from
        update_existing (bool): Whether to update existing records
        
    Returns:
        dict: Statistics about the import process
    """
```

### Example Usage in a Scheduled Action

Here's an example of how to use this function in a scheduled action:

```python
def scheduled_import_sat_from_directory(self):
    """
    Scheduled action to import SAT files from a directory
    """
    import os
    import base64
    
    # Directory where SAT files are stored
    directory = '/path/to/sat/files'
    
    # Get all XLS files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.xls') or filename.endswith('.xlsx'):
            file_path = os.path.join(directory, filename)
            
            # Read the file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Import the file
            wizard = self.env['import.sat.wizard']
            stats = wizard.import_sat_from_file(file_data, filename)
            
            # Log the results
            _logger.info(f"Imported {filename}: {stats}")
            
            # Move the file to a processed directory
            os.rename(file_path, os.path.join(directory, 'processed', filename))
```

### Example Usage in a Mail Processing Job

Here's an example of how to use this function in a mail processing job:

```python
def process_sat_emails(self):
    """
    Process emails with SAT attachments
    """
    # Search for emails with the subject "ME5A Günlük Rapor Sonuçları"
    mail_messages = self.env['mail.message'].search([
        ('subject', '=', 'ME5A Günlük Rapor Sonuçları'),
        ('attachment_ids', '!=', False)
    ])
    
    for message in mail_messages:
        # Process each attachment
        for attachment in message.attachment_ids:
            # Check if it's a ZIP file
            if attachment.name == 'ME5A Günlük Rapor Sonuçları.ZIP':
                # Extract the ZIP file
                import zipfile
                import io
                
                zip_data = base64.b64decode(attachment.datas)
                zip_file = zipfile.ZipFile(io.BytesIO(zip_data))
                
                # Find the XLS file in the ZIP
                for zip_info in zip_file.infolist():
                    if zip_info.filename == 'ME5A_RaporuIHALEME5A.XLS':
                        # Extract the file
                        file_data = zip_file.read(zip_info.filename)
                        
                        # Import the file
                        wizard = self.env['import.sat.wizard']
                        stats = wizard.import_sat_from_file(file_data, zip_info.filename)
                        
                        # Log the results
                        _logger.info(f"Imported from email: {stats}")
                        
                        # Mark the message as processed
                        message.write({'starred': True})
```

## Implementation Details

The import process follows these steps:

1. Read the Excel file
2. Process the SAT data from the specified sheet
3. For each row in the sheet:
   - Extract the SAT data
   - Check if the SAT is already imported
   - Create or update the tender record
   - Create the tender line with the product

The function is designed to be robust and handle errors gracefully. It will continue processing rows even if some rows fail.

## Logging

The import process logs detailed information about each step, including:
- Number of processed rows
- Number of created records
- Number of updated records
- Number of skipped records
- Number of errors

These logs can be used to monitor the import process and troubleshoot issues.

## Future Enhancements

Possible future enhancements include:
- Support for multiple sheets in a single file
- Support for different file formats
- More detailed error reporting
- Email notifications for import results