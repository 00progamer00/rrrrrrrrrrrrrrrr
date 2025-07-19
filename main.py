import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
import logging
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
# Enable CORS for all origins during development.
# For production, restrict to specific origins for security.
CORS(app)

# Set secret key from environment
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Multiple API keys configuration for automatic rotation
API_KEYS = [
    os.getenv("GEMINI_API_KEY"),           # Primary key from Replit secrets
    os.getenv("GOOGLE_API_KEY_1"),        # Backup key 1
    os.getenv("GOOGLE_API_KEY_2"),        # Backup key 2  
    os.getenv("GOOGLE_API_KEY_3"),        # Backup key 3
    # Add more keys if available
]

# Filter out None values
API_KEYS = [key for key in API_KEYS if key is not None]

if not API_KEYS:
    print("Error: No valid API keys found in environment variables.")
    print("Please add at least one API key:")
    print("GEMINI_API_KEY='your_api_key_here'")
    print("GOOGLE_API_KEY_1='your_backup_api_key_here'")
    print("GOOGLE_API_KEY_2='your_second_backup_api_key_here'")
    print("GOOGLE_API_KEY_3='your_third_backup_api_key_here'")
else:
    print(f"✓ Found {len(API_KEYS)} API key(s) for automatic rotation")

MODEL_NAME = 'gemini-2.5-flash'
current_key_index = 0

# Track which keys have been exhausted and when
exhausted_keys = set()
last_reset_time = time.time()

def reset_exhausted_keys_if_needed():
    """Reset exhausted keys every hour to retry them"""
    global exhausted_keys, last_reset_time
    current_time = time.time()
    
    # Reset every hour (3600 seconds)
    if current_time - last_reset_time > 3600:
        if exhausted_keys:
            print("🔄 Resetting exhausted API keys after 1 hour - trying them again")
            exhausted_keys.clear()
            last_reset_time = current_time

def get_next_api_key():
    """Rotate to the next available API key in the list"""
    global current_key_index, exhausted_keys
    
    # Mark current key as exhausted
    exhausted_keys.add(current_key_index)
    
    # Find next non-exhausted key
    for i in range(len(API_KEYS)):
        next_index = (current_key_index + 1 + i) % len(API_KEYS)
        if next_index not in exhausted_keys:
            current_key_index = next_index
            print(f"🔄 Switched to API key #{current_key_index + 1}")
            return API_KEYS[current_key_index]
    
    # All keys exhausted
    print("⚠️ All API keys have been exhausted!")
    return None

def initialize_client():
    """Initialize the Gemini client with the current API key"""
    try:
        return genai.Client(api_key=API_KEYS[current_key_index])
    except Exception as e:
        logging.error(f"Error initializing client with key {current_key_index}: {e}")
        return None

client = initialize_client() if API_KEYS else None

# API Endpoint for AI Assistant
@app.route('/api/ask-ai', methods=['POST'])
def ask_ai():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt is required in the request body."}), 400

    global client
    
    # Reset exhausted keys if enough time has passed
    reset_exhausted_keys_if_needed()
    
    for attempt in range(len(API_KEYS)):
        try:
            # Create the prompt with context
            context_prompt = f"""
You are a helpful customer support assistant for ZTX Hosting, a premium game server hosting company that provides Minecraft, Rust, ARK, and other game server hosting services.

**IMPORTANT LANGUAGE INSTRUCTIONS:**
- Detect the customer's language first:
  * If customer uses Hindi words or phrases (like "kya", "hai", "mujhe", "aapka", "pricing", "plans", etc.), respond in natural Hinglish
  * If customer writes completely in English, respond in English only
- For Hinglish responses: Mix Hindi and English naturally like "Aapka server ready hai", "Best plans available hain", "Support 24/7 milta hai"
- Keep the tone friendly and conversational in both languages

**About ZTX Hosting Team:**
- **Founder:** Bibek Mondal - Visionary leader and founder of ZTX Hosting
- **Co-Founder:** Jeteex - Co-founder and key partner in ZTX Hosting
- **Admin:** Mr. Akashay Thakur - System administrator and technical lead
- **Developer:** Progamer - Lead developer responsible for our hosting infrastructure and platform development in Asia

**Company Information:**
- ZTX Hosting is a premium hosting provider with a strong presence in Asia
- We specialize in game server hosting with cutting-edge infrastructure
- Our team consists of experienced professionals dedicated to providing the best hosting solutions
- We focus on delivering high-performance, reliable hosting services across Asian markets

IMPORTANT: 
- If someone asks about password reset, account login issues, or forgotten passwords, always suggest they use Pterodactyl panel for password reset. Tell them to visit the Pterodactyl login page and use the "Forgot Password" option there.
- If someone asks about ZTX Hosting website login page or client portal login, tell them that the login page is "Coming Soon" and will be available soon. For now, they can contact support via Discord, WhatsApp, or email for any account-related queries.
- When customers ask for Discord link or Discord server, provide this link: https://discord.gg/svjjbKTA5J

Here are our VPS Hosting Plans:

1. **VPS Start** - ₹400/month
   - RAM: 6 GB
   - CPU: 2 Core
   - Disk: 25 GB

2. **VPS Pro** - ₹800/month  
   - RAM: 16 GB
   - CPU: 4 Core
   - Disk: 60 GB

3. **VPS Elite** - ₹1000/month
   - RAM: 24 GB
   - CPU: 6 Core
   - Disk: 90 GB

4. **VPS Ultra** - ₹1500/month
   - RAM: 32 GB
   - CPU: 16 Core
   - Disk: 160 GB

5. **VPS Titan** - ₹2900/month
   - RAM: 64 GB
   - CPU: 24 Core
   - Disk: 360 GB

Here are our Dedicated Hosting Plans:

1. **Dedicated Start** - ₹1999/month
   - RAM: 32 GB
   - CPU: Dual Xeon E5-2670
   - Storage: 2x 480 GB SSD
   - Bandwidth: 1Gbps Unmetered

2. **Dedicated Pro** - ₹5000/month
   - RAM: 64 GB DDR4
   - CPU: AMD EPYC 7302P
   - Storage: 2x 1TB NVMe
   - Bandwidth: 2Gbps Unmetered

3. **Dedicated Elite** - ₹10000/month
   - RAM: 128 GB DDR4
   - CPU: AMD Ryzen 9 5950X
   - Storage: 2x 2TB NVMe
   - Bandwidth: 2.5Gbps Unmetered

4. **Dedicated Ultra** - ₹8000/month
   - RAM: 256 GB ECC
   - CPU: Intel Xeon Gold 6248R
   - Storage: 4x 2TB NVMe RAID
   - Bandwidth: 5Gbps Unmetered

**Why Choose ZTX Hosting?**

We provide the best infrastructure and support for your gaming needs with these key advantages:

🚀 **High Performance**
- Latest generation hardware with NVMe storage for maximum speed
- Optimized servers specifically designed for gaming
- Lightning-fast load times and smooth gameplay experience

🛡️ **DDoS Protection**
- Enterprise-grade protection against attacks and malicious traffic
- Advanced security measures to keep your servers online 24/7
- Proactive monitoring and automatic threat detection

💬 **24/7 Support**
- Our expert team is available around the clock to assist you
- Quick response times via Discord, WhatsApp, and email
- Technical support from experienced gaming professionals

🌐 **Global Network**
- Low-latency servers in North America, Europe, and Asia
- Strategic server locations for optimal connectivity
- Redundant network infrastructure for maximum uptime

⚡ **Additional Benefits:**
- **Instant Setup**: Get your server running within minutes
- **Auto Backups**: Your data is automatically backed up regularly
- **Easy Control Panel**: User-friendly interface for server management
- **Full Root Access**: Complete control over your server configuration
- **99.9% Uptime**: Reliable hosting with minimal downtime
- **Flexible Scaling**: Easily upgrade or downgrade your plan anytime
- **Mod & Plugin Support**: Full compatibility with popular game modifications
- **Premium Hardware**: High-end CPUs and SSDs for optimal performance
- **Competitive Pricing**: Best value for money in the Indian market
- **Indian Servers**: Low ping for Indian players with local data centers

Here are our Game Hosting Plans:

**Currently Available:**

**Minecraft Hosting Plans:**
1. **Grass Plan** - ₹100/month
   - RAM: 2 GB
   - CPU: 100%
   - Disk: 5 GB NVMe
   - Backup Slots: 1

2. **Dirt Plan** - ₹200/month
   - RAM: 4 GB
   - CPU: 150%
   - Disk: 10 GB NVMe
   - Backup Slots: 2

3. **Stone Plan** - ₹300/month
   - RAM: 6 GB
   - CPU: 160%
   - Disk: 15 GB NVMe
   - Backup Slots: 2

4. **Wood Plan** - ₹400/month
   - RAM: 8 GB
   - CPU: 200%
   - Disk: 20 GB NVMe
   - Backup Slots: 2

5. **Iron Plan** - ₹600/month
   - RAM: 12 GB
   - CPU: 250%
   - Disk: 30 GB NVMe
   - Backup Slots: 3

6. **Gold Plan** - ₹800/month
   - RAM: 16 GB
   - CPU: 350%
   - Disk: 40 GB NVMe
   - Backup Slots: 4

7. **Diamond Plan** - ₹1300/month
   - RAM: 24 GB
   - CPU: 450%
   - Disk: 50 GB NVMe
   - Backup Slots: 8

8. **Netherite Plan** - ₹1760/month
   - RAM: 32 GB
   - CPU: 550%
   - Disk: 70 GB NVMe
   - Backup Slots: 10

9. **Bedrock Plan** - ₹3500/month
   - RAM: 64 GB
   - CPU: 950%
   - Disk: 100 GB NVMe
   - Backup Slots: 10

**Coming Soon:**
- **Rust** - Lag-free Rust server hosting with instant setup and DDoS protection
- **ARK: Survival** - Run your ARK servers smoothly with auto updates and platform support
- **Counter-Strike 2** - Low-latency Counter-Strike 2 servers with competitive tickrate and protection
- **GTA FiveM** - Premium FiveM hosting for RP servers with high performance and custom scripts support

Please answer the following customer question in a helpful, professional, and friendly manner. If the question is about hosting, servers, technical issues, or gaming, provide detailed and accurate information. If someone asks about VPS plans or dedicated hosting plans, provide the above pricing and specifications. If it's unrelated to hosting or gaming, politely redirect them to hosting-related topics.

Customer Question: {prompt}

Please provide a clear, helpful response in a conversational tone. You can use formatting like bullet points or numbered lists if it helps organize the information better.
"""

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=context_prompt
            )
            
            ai_response_text = ""
            if response.text:
                ai_response_text = response.text
            else:
                ai_response_text = "AI could not generate a complete response. Please try asking something else or rephrase your query."

            return jsonify({"answer": ai_response_text})
            
        except Exception as e:
            error_str = str(e).upper()
            logging.error(f"Error generating AI content: {e}")
            
            if "QUOTA" in error_str or "RATE LIMIT" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logging.info(f"API key #{current_key_index + 1} quota exhausted, rotating to next key")
                next_key = get_next_api_key()
                if next_key is None:
                    # All keys exhausted
                    break
                client = genai.Client(api_key=next_key)
                continue
                
            errorMessage = 'AI query ka jawab nahi de sakta. Kripya phir se koshish karein.'

            if "SAFETY" in error_str:
                errorMessage = 'Main is query ka jawab nahi de sakta safety reasons ki wajah se. Kripya alag tarah se sawal puchein.'
            elif "API KEY" in error_str:
                errorMessage = 'Invalid or expired API key. Please check your API keys in the .env file.'
            elif "404" in error_str and "MODEL" in error_str:
                errorMessage = f'The selected AI model ({MODEL_NAME}) is not found or supported for your API key. Please choose an available model.'
            
            return jsonify({"error": errorMessage}), 500
    
    # If all keys have been tried and failed
    return jsonify({"error": "All API keys have exhausted their quotas. Please try again later."}), 500

# Serve the frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    print(f"Server running on http://0.0.0.0:5000")
    print("AI Assistant Backend (Python) is ready!")

