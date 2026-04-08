import re
import json
import base64
import time
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession

BOT_TOKEN = '8692849287:AAH7lYrTHX0luZCcpABoRFpY-i8ja3Gq1oY'
API_ID = 37893084
API_HASH = '853a6c0f3be11009f667bc153244452e'

client = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_states = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user_states[user_id] = {'step': 0, 'username': '', 'password': '', 'waiting_for': 'username'}
    await event.reply("🔐 **Instagram 2026 FIXED Bot**\n\nUsername → Password → Real login")

@client.on(events.NewMessage)
async def handler(event):
    user_id = event.sender_id
    text = event.text.strip()
    
    if user_id not in user_states:
        await event.reply("/start first!")
        return
    
    state = user_states[user_id]
    
    if state['waiting_for'] == 'username':
        if re.match(r'^[a-zA-Z0-9._]{3,30}$', text):
            state['username'] = text.lower()
            state['waiting_for'] = 'password'
            await event.reply(f"✅ `{state['username']}`\nSend Password :")
        return
    
    if state['waiting_for'] == 'password':
        state['password'] = text
        state['waiting_for'] = 'login'
        
        await event.reply("🔄 **Waiting for Login...**")
        result = await fixed_instagram_login(state['username'], state['password'], user_id)
        
        status = result['status']
        cookies = result.get('cookies', {})
        
        # **FULL SESSION DISPLAY**
        session_str = base64.b64encode(json.dumps(cookies).encode()).decode()
        session_display = f"```{session_str}```"
        
        cookie_info = f"**Cookies:**\n"
        cookie_info += f"• `sessionid`: `{cookies.get('sessionid', 'None')}`\n"
        cookie_info += f"• `csrftoken`: `{cookies.get('csrftoken', 'None')}`\n"
        cookie_info += f"• `mid`: `{cookies.get('mid', 'None')}`\n"
        cookie_info += f"• `ig_did`: `{cookies.get('ig_did', 'None')}`\n"
        cookie_info += f"**Total**: {len(cookies)} cookies"
        
        full_response = f"{cookie_info}\n\n**Session ID:**\n{session_display}"
        
        if status == 'success':
            await event.reply(f"🟢 **SUCCESS**✅\n\n{full_response}")
            
        elif status == '2fa':
            state['cookies'] = cookies
            state['waiting_for'] = 'otp'
            await event.reply(f"🔐 **2FA** 📲\n\n{full_response}\n\n6-digit OTP bhejo:")
            
        elif status == 'checkpoint':
            await event.reply(f"⚠️ **CHECKPOINT** 📱\n\n{full_response}\n\nApp se verify karo")
            
        elif status == 'disabled':
            await event.reply(f"🚫 **DISABLED ACCOUNT** ⚠️\n\n{full_response}\n\n📱 **Recovery ke liye Instagram app use karo**\n\n**DISABLED ID KA BHI SESSION MIL GAYA!**")
            
        else:
            await event.reply(f"❌ **Failed**: {result.get('reason', 'Unknown')}\n\n{full_response}")
    
    elif state['waiting_for'] == 'otp':
        if re.match(r'^\d{6}$', text):
            await event.reply("🔄 **OTP check kar rahe...**")
            success = await otp_handler(state['username'], state['password'], text, state['cookies'])
            
            # **UPDATED COOKIES**
            updated_cookies = state.get('cookies', {})
            session_str = base64.b64encode(json.dumps(updated_cookies).encode()).decode()
            session_display = f"```{session_str}```"
            
            cookie_info = f"**Updated Cookies:**\n"
            cookie_info += f"• `sessionid`: `{updated_cookies.get('sessionid', 'None')}`\n"
            cookie_info += f"• `csrftoken`: `{updated_cookies.get('csrftoken', 'None')}`\n"
            cookie_info += f"• `mid`: `{updated_cookies.get('mid', 'None')}`\n"
            cookie_info += f"• `ig_did`: `{updated_cookies.get('ig_did', 'None')}`\n"
            cookie_info += f"**Total**: {len(updated_cookies)} cookies"
            
            full_response = f"{cookie_info}\n\n**Final Session:**\n{session_display}"
            
            if success:
                await event.reply(f"✅ **2FA SUCCESS**🟢\n\n{full_response}")
            else:
                await event.reply(f"❌ **Wrong OTP**\n\n{full_response}\n\n🔢 Resend Correct Otp:")

async def fixed_instagram_login(username, password, user_id):
    """DISABLED ID KA BHI FULL SESSION"""
    s = requests.Session()
    
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.instagram.com/accounts/login/',
        'Origin': 'https://www.instagram.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })
    
    cookies = {}
    
    try:
        # STEP 1: Initial cookies
        initial = s.get('https://www.instagram.com/', timeout=15)
        cookies.update(s.cookies.get_dict())
        
        # STEP 2: Login page cookies
        login_page = s.get('https://www.instagram.com/accounts/login/?source=auth_switcher', timeout=15)
        cookies.update(s.cookies.get_dict())
        
        # CSRF
        csrf_token = None
        patterns = [
            r'"csrf_token"\s*:\s*"([a-f0-9]{32})"',
            r'"csrf_token":\s*"([a-f0-9]{32})"',
            r'csrftoken["\s:=]*"([a-f0-9]{32})"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, login_page.text)
            if match:
                csrf_token = match.group(1)
                break
        
        csrf_token = csrf_token or s.cookies.get('csrftoken')
        cookies.update(s.cookies.get_dict())
        
        if not csrf_token:
            return {'status': 'failed', 'reason': 'No CSRF token', 'cookies': cookies}
        
        # Headers
        app_id_match = re.search(r'"app_id"\s*:\s*"(\d+)"', login_page.text)
        app_id = app_id_match.group(1) if app_id_match else '936619743392459'
        
        login_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': app_id,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Instagram-AJAX': '1000000000',
            'X-IG-WWW-Claim': '0',
        }
        s.headers.update(login_headers)
        
        # Login
        timestamp = str(int(time.time()))
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}"
        
        data = {
            'username': username,
            'enc_password': enc_password,
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        
        response = s.post(
            'https://www.instagram.com/accounts/login/ajax/',
            data=data,
            timeout=30
        )
        
        # **FINAL COOKIES - DISABLED HO YA SUCCESS**
        cookies.update(s.cookies.get_dict())
        resp_text = response.text
        
        print(f"[LOGIN] {username} -> Status: {response.status_code}")
        
        # **DISABLED ACCOUNT - FULL COOKIES + SESSION**
        if any(x in resp_text for x in ['"user_inactivated_error"', '"is_user_inactivated_error":true', 'account has been disabled', 'inactivated']):
            print(f"[+] DISABLED DETECTED: {username} - SENDING SESSION")
            return {'status': 'disabled', 'cookies': cookies}
        
        # SUCCESS
        if (response.status_code == 200 and 
            ('"authenticated":true' in resp_text or 
             '"userId":"' in resp_text or 
             cookies.get('sessionid'))):
            return {'status': 'success', 'cookies': cookies}
        
        # 2FA
        if '"two_factor_required":true' in resp_text:
            return {'status': '2fa', 'cookies': cookies}
        
        # CHECKPOINT
        if any(x in resp_text for x in ['"checkpoint_required":true', '"challenge_required"']):
            return {'status': 'checkpoint', 'cookies': cookies}
        
        # ALL OTHER CASES
        return {'status': 'failed', 'reason': 'Login failed', 'cookies': cookies}
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return {'status': 'failed', 'reason': str(e), 'cookies': cookies}

async def otp_handler(username, password, otp, cookies):
    s = requests.Session()
    s.cookies.update(cookies)
    
    try:
        page = s.get('https://www.instagram.com/', timeout=10)
        csrf_match = re.search(r'"csrf_token"\s*:\s*"([a-f0-9]{32})"', page.text)
        if csrf_match:
            s.headers['X-CSRFToken'] = csrf_match.group(1)
        
        timestamp = str(int(time.time()))
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}"
        
        data = {
            'username': username,
            'verificationCode': otp,
            'enc_password': enc_password,
            'queryParams': '{}'
        }
        
        resp = s.post('https://www.instagram.com/accounts/login/ajax/two_factor/', 
                     data=data, timeout=20)
        
        final_cookies = s.cookies.get_dict()
        
        # UPDATE USER STATE
        current_user = next((uid for uid, st in user_states.items() if st.get('waiting_for') == 'otp'), None)
        if current_user and current_user in user_states:
            user_states[current_user]['cookies'] = final_cookies
            
        return '"authenticated":true' in resp.text
        
    except:
        return False

print("🚀 DISABLED ID KA BHI SESSION MIL JAYEGA!")
client.run_until_disconnected()