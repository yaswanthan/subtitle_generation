import smtplib
import ssl
import os
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

g_pass = os.environ.get('gmail_password')
def send_subtitle_completion_email(to_email, subtitle_path, sender_email = "yash.aravindan@gmail.com", sender_password = g_pass, smtp_server="smtp.gmail.com", smtp_port=465):
    """
    Sends an email notifying the user that subtitle processing is complete,
    with video and subtitle files attached.
    
    Parameters:
        to_email (str): Recipient's email address.
        video_path (str): Path to the final video file.
        subtitle_path (str): Path to the .srt subtitle file.
        sender_email (str): Sender's email address.
        sender_password (str): Sender's email password or app password.
        smtp_server (str): SMTP server address (default: Gmail).
        smtp_port (int): SMTP server port (default: 465 for SSL).
    """

    msg = EmailMessage()
    msg['Subject'] = ' Subtitle Processing Complete'
    msg['From'] = sender_email
    msg['To'] = to_email

    msg.set_content(
        "Hi,\n\nYour subtitle processing is complete.\n\n"
        "Please find the processed video and subtitle file attached.\n\n"
        "Regards,\nSubtitle Automation Team"
    )

    # Attach subtitle
    subtitle_file = Path(subtitle_path)
    if subtitle_file.exists():
        msg.add_attachment(
            subtitle_file.read_bytes(),
            maintype='text',
            subtype='plain',
            filename=subtitle_file.name
        )

    # Send email securely
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

    print(" Email sent successfully to", to_email)



# send_subtitle_completion_email(
#     to_email="optisol.yas@gmail.com",
#     video_path="uploads/148e2a7a-8c7b-4650-bd04-f41d1cd438ae/original_file/SSYouTube.online_F1 _ Official Trailer_720p.mp4",
#     subtitle_path="uploads/148e2a7a-8c7b-4650-bd04-f41d1cd438ae/srt/full.srt",
#     sender_email="yash.aravindan@gmail.com",
#     sender_password=g_pass
# )
