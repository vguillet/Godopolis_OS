import os
import win32print
import win32api

def print_pdf_landscape(pdf_path, printer_name=None):
    # Get the default printer if no printer name is provided
    if not printer_name:
        printer_name = win32print.GetDefaultPrinter()

    # Print the PDF file with landscape orientation using Adobe Reader (or default PDF reader)
    # The '/t' flag sends the print job to the default printer, but Adobe Reader will handle the landscape orientation
    print_command = f'"{pdf_path}" /t "{pdf_path}" "{printer_name}"'
    
    # Execute the print command using the default PDF reader
    win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)

def list_printers():
    # Get a list of all installed printers
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    return printers

list_printers()