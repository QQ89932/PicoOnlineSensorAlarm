import rp2  # Import the rp2 module which contains functions and classes specifically for RP2040
import network  # Import the network module for connecting to WiFi
import ubinascii  # Import the ubinascii module for converting MAC address to hex string
import machine  # Import the machine module for GPIO control
import urequests as requests  # Import the urequests module for HTTP requests
import time  # Import the time module for delay
import socket  # Import the socket module for establishing sockets
import utime
import neopixel # Import neopixel for RGB LED light control
import usocket as socket
import usocket
import ussl

# Umail class code
DEFAULT_TIMEOUT = 10  # Second
LOCAL_DOMAIN = '127.0.0.1'
CMD_EHLO = 'EHLO'
CMD_STARTTLS = 'STARTTLS'
CMD_AUTH = 'AUTH'
CMD_MAIL = 'MAIL'
AUTH_PLAIN = 'PLAIN'
AUTH_LOGIN = 'LOGIN'

class SMTP:
    def cmd(self, cmd_str):
        sock = self._sock
        sock.write('%s\r\n' % cmd_str)
        resp = []
        next = True
        while next:
            code = sock.read(3)
            next = sock.read(1) == b'-'
            resp.append(sock.readline().strip().decode())
        return int(code), resp

    def __init__(self, host, port, ssl=False, username=None, password=None):
        self.username = username
        addr = usocket.getaddrinfo(host, port)[0][-1]
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        sock.settimeout(DEFAULT_TIMEOUT)
        sock.connect(addr)
        if ssl:
            sock = ussl.wrap_socket(sock)
        code = int(sock.read(3))
        sock.readline()
        assert code == 220, 'cant connect to server %d, %s' % (code, resp)
        self._sock = sock

        code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        assert code == 250, '%d' % code
        if not ssl and CMD_STARTTLS in resp:
            code, resp = self.cmd(CMD_STARTTLS)
            assert code == 220, 'start tls failed %d, %s' % (code, resp)
            self._sock = ussl.wrap_socket(sock)

        if username and password:
            self.login(username, password)

    def login(self, username, password):
        self.username = username
        code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        assert code == 250, '%d, %s' % (code, resp)

        auths = None
        for feature in resp:
            if feature[:4].upper() == CMD_AUTH:
                auths = feature[4:].strip('=').upper().split()
        assert auths != None, "no auth method"

        from ubinascii import b2a_base64 as b64
        if AUTH_PLAIN in auths:
            cren = b64("\0%s\0%s" % (username, password))[:-1].decode()
            code, resp = self.cmd('%s %s %s' % (CMD_AUTH, AUTH_PLAIN, cren))
        elif AUTH_LOGIN in auths:
            code, resp = self.cmd("%s %s %s" % (CMD_AUTH, AUTH_LOGIN, b64(username)[:-1].decode()))
            assert code == 334, 'wrong username %d, %s' % (code, resp)
            code, resp = self.cmd(b64(password)[:-1].decode())
        else:
            raise Exception("auth(%s) not supported " % ', '.join(auths))

        assert code == 235 or code == 503, 'auth error %d, %s' % (code, resp)
        return code, resp

    def to(self, addrs,    mail_from=None):
        mail_from = self.username if mail_from == None else mail_from
        code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
        assert code == 250, '%d' % code
        code, resp = self.cmd('MAIL FROM: <%s>' % mail_from)
        assert code == 250, 'sender refused %d, %s' % (code, resp)

        if isinstance(addrs, str):
            addrs = [addrs]
        count = 0
        for addr in addrs:
            code, resp = self.cmd('RCPT TO: <%s>' % addr)
            if code != 250 and code != 251:
                print('%s refused, %s' % (addr, resp))
                count += 1
        assert count != len(addrs), 'recipient refused, %d, %s' % (code, resp)

        code, resp = self.cmd('DATA')
        assert code == 354, 'data refused, %d, %s' % (code, resp)
        return code, resp

    def write(self, content):
        self._sock.write(content)

    def send(self, content=''):
        if content:
            self.write(content)
        self._sock.write('\r\n.\r\n')  # the five letter sequence marked for ending
        line = self._sock.readline()
        return (int(line[:3]), line[4:].strip().decode())

    def quit(self):
        self.cmd("QUIT")
        self._sock.close()

# End of umail code

# Set country code to avoid potential errors
# CN/US/DE/DK/GB/JP (country code: China/USA/Germany/Denmark/UK/Japan)
rp2.country('GB')  # Set the country code for Pico W to UK
wlan = network.WLAN(network.STA_IF)  # Create WLAN connection object
wlan.active(True)  # Activate WLAN interface

# Check the MAC address of Pico W board's wireless WiFi
# Get the MAC address and convert it to hex string
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
print('Pico W MAC address=' + mac)  # Display the hexadecimal MAC address of Pico W board

ssid = 'QiaoDong_SmartHome'  # Set the WiFi name (ssid: service set identifier)
psw = 'Qiaodong666'  # Set the WiFi password

wlan.connect(ssid, psw)  # Connect to the WiFi network

timeout = 10  # Set the maximum waiting time for connection to be 10 seconds
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:  # If the WiFi connection succeeds or fails
        break  # Exit the loop
    timeout -= 1
    print('Waiting for connection!')
    time.sleep(1)  # Delay for 1 second

# Define function for flashing onboard LED of Pico W board
def onboard_led_blink(blink_numbers):
    onboard_led = machine.Pin('LED', machine.Pin.OUT)  # Create GPIO control object
    for i in range(blink_numbers):
        onboard_led.value(1)  # Turn on LED
        # onboard_led.on()  # Another way to turn on LED
        time.sleep(0.5)
        onboard_led.value(0)  # Turn off LED
        # onboard_led.off()  # Another way to turn off LED
        time.sleep(0.5)

# Handle connection errors
if wlan_status != 3:  # If the WiFi connection fails
    raise RuntimeError('WiFi connection failed!')  # Raise an exception
else:
    print('WiFi connected...')
    status = wlan.ifconfig()  # Get the WiFi interface configuration information
    print('IP address=' + status[0])  # Output the IP address


# Define function for loading HTML page
def get_html(html_name):
    with open(html_name, 'r') as file:  # Open the HTML file
        html = file.read()  # Read the HTML content
    return html

# Open HTTP Web server socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]  # Get the IP address and port number
s = socket.socket()  # Create socket object
s.bind(addr)  # Bind the socket to the IP address and port number
# Start listening to the port number
s.listen(3)  # Allow up to 3 clients to connect

print('Listening on', addr)

onboard_led = machine.Pin('LED', machine.Pin.OUT)
adc = machine.ADC(26)

 # set up MakerPi Pico Buzzer pin
buzzer_pin = machine.Pin(18, machine.Pin.OUT)
num_pixels = 1
np = neopixel.NeoPixel(machine.Pin(28), num_pixels)  # set up MakerPi Pico RGB light


def turn_red():
    np[0] = (255, 0, 0)  # set RGB red
    np.write()
    buzz()
    buzz()
    buzz()
# buzz 3 times

def turn_green():
    np[0] = (0, 255, 0)  # set RGB green
    np.write()

# use buzzer to buzz
def buzz():
    buzzer_pin.value(100)
    utime.sleep(0.5)
    buzzer_pin.value(0)

last_email_sent = 0

def send_email():
    print('start sending email')
	
	# Using SMTP protocol to send email
    smtp_server = 'smtp.qq.com'
    smtp_port = 465
    email_address = 'do-not_reply@qq.com'
    email_password = 'PASSWORD'  

    #Create a email
    sender = 'do-not_reply@qq.com'
    recipient = 'aaron89932@gmail.com'
    subject = 'Sensor Value Alert'
    body = 'Sensor value is abnormal, please go to check!'

    try:
	    # SEnd Email
        server = SMTP(smtp_server, smtp_port, ssl=True, username=email_address, password=email_password)
        server.to(recipient)
        server.write("Subject: {}\r\n".format(subject))
        server.write("From: {}\r\n".format(sender))
        server.write("To: {}\r\n".format(recipient))
        server.write("\r\n")  # separate headers from body
        server.write(body)
        server.send()
        server.quit()
        print('Email sent successfully.')
    except Exception as e:
        print('Error sending email:', e)


while True:
    try:
        
        value = adc.read_u16()
        # Calculate voltage
        voltage = value * 3.3 / 65535
        # Calculate soil moisture
        humidity = str((voltage - 1.1) / 1.1 * 100)
        
		# if sensor value is small than 100, normal
        if humidity < 100:
            turn_green()
        else:
            turn_red() # abnormal
        
		#Send no more than ONE email within 30 seconds
        if humidity > 100 and time.time() - last_email_sent > 30:
            try:
                send_email()
                last_email_sent = time.time()
            except Exception as e:
                print("Error while sending email:", e)
        humidity_str = str(humidity)
        

        
        # Accept client connection and get the address
        cl, addr = s.accept()
		# Receive client request message
        r = cl.recv(1024)
        r = str(r)
		# Search for the commands to turn on/off the LED in the request message
        onboard_led_on = r.find('?onboard_led=1')
        onboard_led_off = r.find('?onboard_led=0')
        newon = r.find('?onnew_vlaue=1')
		# If '?onboard_led=1' is found, turn on the LED
        if onboard_led_on > -1:
            print('LED on')
            onboard_led.value(1)
		# If '?onboard_led=0' is found, turn off the LED
        if onboard_led_off > -1:
            print('LED off')
            onboard_led.value(0)
        if newon > -1:
            response = humidity_str
        else:
		    # Get the content of the HTML file
            response = get_html('index.html')
		# Send HTTP response header
        if onboard_led_on > -1 or onboard_led_off > -1:
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.close()
        else:
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
			# Send the content of the HTML file
            cl.send(response)
            print('Sent:' + response)
			# Close the client socket
            cl.close()
	# If an OSError occurs, close the client socket and output relevant information
    except OSError as e:
        cl.close()
        print('Connection closed')
        print(repr(e))

