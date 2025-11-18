import os
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai


load_dotenv()


app = Flask(__name__, static_folder="../public/static", template_folder="../public")
CORS(app)


GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


email_count = 0
MAX_EMAILS_PER_DAY = 50


if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/send-message', methods=['POST'])
def send_message():
    global email_count
   
    if email_count >= MAX_EMAILS_PER_DAY:
        return jsonify({
            'success': False,
            'message': 'Oops! Our email service has reached its daily limit. Please try again tomorrow.'
        }), 429
   
    data = request.json
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')
   
    if not all([name, email, subject, message]):
        return jsonify({
            'success': False,
            'message': 'All fields are required.'
        }), 400
   
    if '@' not in email or '.' not in email:
        return jsonify({
            'success': False,
            'message': 'Please provide a valid email address.'
        }), 400
   
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = GMAIL_USER
        msg['Subject'] = f"Portfolio Contact: {subject}"
        msg['Reply-To'] = email
       
        body = f"""
        Name: {name}
        Email: {email}
        Subject: {subject}
       
        Message:
        {message}
        """
       
        msg.attach(MIMEText(body, 'plain'))
       
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
       
        email_count += 1
       
        return jsonify({
            'success': True,
            'message': 'Your message has been sent successfully!'
        })
       
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while sending your message. Please try again later.'
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    if not OPENAI_API_KEY:
        return jsonify({
            'success': False,
            'message': 'Chat service is currently unavailable.'
        }), 503
   
    data = request.json
    user_message = data.get('message')
   
    if not user_message:
        return jsonify({
            'success': False,
            'message': 'Message is required.'
        }), 400
   
    try:
        prompt = f"""
        You are an AI assistant representing Kunal Dange, a senior full-stack developer with 8+ years of experience.
       
        About Kunal:
        - Full-Stack Web Developer with expertise in both frontend (React, Vue.js) and backend (Laravel, Node.js)
        - Experience with cloud platforms (AWS, Azure) and DevOps
        - Currently working as Senior Software Engineer at Inorbvict Healthcare
        - Previously worked at Invezza Technologies, HN Web Marketing, and Hosting Duty
        - Education: BE in Information Technology from MMCOE, Pune
       
        Key Projects:
        - KYC360 (RiskScreen): AML compliance platform using Laravel and MSSQL
        - FlightCheck Services: Aircraft maintenance SaaS using Laravel and Vue.js
        - IDIMS: Unified CRM and ERP platform for healthcare
       
        Please respond to the following user query in a professional, helpful manner. If you don't know the answer to something outside of Kunal's professional background, politely indicate that.
       
        User Query: {user_message}
       
        Response:
        """
       
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional AI assistant representing Kunal Dange, a senior full-stack developer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
       
        bot_response = response.choices[0].message.content.strip()
       
        return jsonify({
            'success': True,
            'message': bot_response
        })
       
    except Exception as e:
        print(f"Error with OpenAI API: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'I apologize, but I\'m having trouble responding right now. Please try again later.'
        }), 500


@app.route('/api/reset-email-count', methods=['POST'])
def reset_email_count():
    global email_count
    email_count = 0
    return jsonify({'success': True, 'message': 'Email count reset.'})


if __name__ == '__main__':
    app.run(debug=True)
