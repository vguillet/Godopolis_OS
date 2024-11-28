from print_pdf import print_pdf_landscape
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from io import BytesIO
import qrcode
from reportlab.lib.utils import ImageReader

# Define the fixed width for 80mm receipt paper (approximately 3.15 inches wide, 226.8 points)
receipt_width = 80 * 2.835   # mm to points conversion (1 mm = 2.835 points)
initial_receipt_height = 200  # Initial height, will modify based on content
logo_path = "casino_logo.png"  # Replace with the path to your logo
pdf_path = "pos_ticket.pdf"

# Register the font
pdfmetrics.registerFont(TTFont('Kidspace', 'C:\\Users\\Augustin\\AppData\\Local\\Microsoft\\Windows\\Fonts\\Kidspace-DEMO.ttf'))
# Function to draw the logo at the top of the receipt
def draw_logo(c, margin_x, receipt_width, receipt_height):
    try:
        logo = Image.open(logo_path)
        logo_width, logo_height = logo.size
        aspect_ratio = logo_width / logo_height
        # Calculate desired logo dimensions
        desired_width = receipt_width - 2 * margin_x  # Respecting the margins
        desired_height = desired_width / aspect_ratio  # Adjust height based on aspect ratio
        
        # Compute the new receipt height: logo height + 150 points (for other content)
        receipt_height = desired_height + 150 + 50 + 70 # Winning + QRCODESs
        
        # Update the canvas size to accommodate the logo and the extra content
        c.setPageSize((receipt_width, receipt_height))

        # Draw the logo at the top
        c.drawImage(logo_path, margin_x, receipt_height - desired_height - 10, width=desired_width, height=desired_height)
        print(f"Logo drawn at: x={margin_x}, y={receipt_height - desired_height - 10}, width={desired_width}, height={desired_height}")
        
        current_y = receipt_height - desired_height - 20  # Update to below the logo with some margin
        return current_y, receipt_height
    except IOError:
        print("Logo file not found. Proceeding without logo.")
        return receipt_height - 10, receipt_height

# Function to draw text information (ReCIP ID, date, client name)
def draw_text(c, margin_x, current_y, rec_id, client_name):
    # Add ReCIP ID below the logo
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, current_y, f"ReCIP ID: {rec_id}")
    print(f"ReCIP ID drawn at: x={margin_x}, y={current_y}")
    current_y -= 20

    # Add current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, current_y, f"Date: {current_time}")
    print(f"Date drawn at: x={margin_x}, y={current_y}")
    current_y -= 20

    # Add client name
    c.setFont("Helvetica-Bold", 10)
    if client_name is not None:
        c.drawString(margin_x, current_y, f"Client: {client_name}")
        print(f"Client name drawn at: x={margin_x}, y={current_y}")
    current_y -= 20
    
    if False:
        # Add dashed separator line
        c.setFont("Helvetica", 9)
        c.drawString(margin_x, current_y, "-" * 32)  # Adjust the number of dashes as needed for receipt width
        print(f"Dashed line drawn at: x={margin_x}, y={current_y}")
        current_y -= 20

    return current_y

# Function to add "WINNING" text at the bottom, centered
def draw_winning(c, receipt_width, current_y, winning_amount="1,200€"):
    # Add separator line
    c.setFont("Helvetica", 9)
    c.drawString(10, current_y, "-" * 32)
    current_y -= 20
    # Add another space
    current_y -= 20

    # Add "WINNING" centered
    c.setFont("Helvetica-Bold", 18)  # Make this bold and large
    c.drawCentredString(receipt_width / 2, current_y, "WINNING")
    current_y -= 30

    # Add the winning amount, 3 times larger
    c.setFont("Kidspace", 30)  # Larger text for winning amount
    c.drawCentredString(receipt_width / 2, current_y, winning_amount)
    current_y -= 35

    # Add bottom separator line
    c.setFont("Helvetica", 9)
    c.drawString(10, current_y, "-" * 32)
    print(f"Winning amount and separators drawn at: x=centered, y={current_y}")

    return current_y

def draw_qr_code(c, receipt_id, receipt_width, current_y):
    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,  # Smaller size
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # Size of each box (unit) in the QR code
        border=2,  # Border size
    )
    qr.add_data(receipt_id)
    qr.make(fit=True)
    
    # Create an image object for the QR code
    img = qr.make_image(fill='black', back_color='white')
    
    # Convert the QR image to a format that ReportLab can handle (ImageReader)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Use ReportLab's ImageReader to read the BytesIO object
    qr_image = ImageReader(buffer)

    # Determine the size of the QR code in points (1 mm = 2.835 points)
    qr_code_size_mm = 20  # For example, 20 mm x 20 mm
    qr_code_size_pt = qr_code_size_mm * mm  # Convert mm to points

    # Print the size of the QR code to the console
    print(f"QR code size: {qr_code_size_mm} mm ({qr_code_size_pt} points)")

    # Calculate the position to center the QR code
    qr_x = (receipt_width - qr_code_size_pt) / 2  # Center horizontally
    qr_y = current_y - qr_code_size_pt - 10  # Add a margin of 10 points under the earnings

    # Draw the QR code on the canvas
    c.drawImage(qr_image, qr_x, qr_y, width=qr_code_size_pt, height=qr_code_size_pt)
    
    # Update the current_y position
    current_y = qr_y - 10  # Leave some space after the QR code
    
    return current_y


# Main function to generate the receipt
def generate_pos_ticket(rec_id, client_name=None, amount="1,200.00"):
    # Create a new PDF with an adjustable height, fixed width
    c = canvas.Canvas(pdf_path, pagesize=(receipt_width, initial_receipt_height))
    
    # Set a margin and starting position for the content
    margin_x = 10
    current_y = initial_receipt_height - 10  # Start closer to the top (adjusted for small margin)

    # Draw the logo and get the updated receipt height and current_y
    current_y, receipt_height = draw_logo(c, margin_x, receipt_width, current_y)
    
    # Draw the text content and get updated current_y
    current_y = draw_text(c, margin_x, current_y, rec_id, client_name)
    
    #
    current_y = draw_qr_code(c, rec_id, receipt_width, current_y)

    # Draw the "WINNING" message at the bottom
    current_y = draw_winning(c, receipt_width, current_y, amount)
    # Finalize the page and save the PDF
    c.showPage()  # End of ticket
    c.save()      # Save the PDF
    print("PDF generation completed and saved.")


if __name__ == "__main__":
    generate_pos_ticket("123456789", "John Doe")
    print_pdf_landscape(pdf_path)