import paho.mqtt.client as mqtt
import json
import cv2
import numpy as np

from flask import Flask, request, render_template_string, jsonify

mqtt_topic = "casino/tickets"
MQTT_PORT = 1883
MQTT_ADRESS = "192.168.1.177"
MQTT_ADRESS = "localhost"
HOST_ADRESS = "0.0.0.0"
def subscript_test():
    # Callback when a message is received
    def on_message(client, userdata, msg):
        print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    # Initialize MQTT client
    client = mqtt.Client()
    client.on_message = on_message

    # Connect to the broker and subscribe to the topic
    client.connect(MQTT_ADRESS, 1883, 60)  # Replace with your MQTT broker address and port
    client.subscribe(mqtt_topic)

    # Start the MQTT client
    print(f"Subscribed to topic: {mqtt_topic}")
    client.loop_forever()
    

# Load the JSON file
with open("example.json", "r") as file:
    croupiers = json.load(file)

# Create a logo image with OpenCV and save it
logo_image = np.zeros((100, 300, 3), dtype=np.uint8)
logo_image[:] = (50, 50, 50)  # Dark gray background
cv2.putText(logo_image, "Casino Logo", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
cv2.imwrite("static/logo.png", logo_image)

# Flask application
app = Flask(__name__)

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_ADRESS, MQTT_PORT, 60)  # Replace with your MQTT broker address and port

# HTML template (unchanged)
html_template = """

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tickets Générateur</title>
    <style>
        body {
            background-color: black;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            width: 90%;
            max-width: 400px;
            padding: 20px;
            border: 1px solid #444;
            border-radius: 10px;
            background-color: #222;
        }
        .logo img {
            width: 100%;
            height: auto;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-size: 16px; /* Ensure at least 16px font size */
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #555;
            border-radius: 5px;
            background-color: #333;
            color: white;
            font-size: 16px; /* Ensure at least 16px font size */
        }
        button {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 5px;
            background-color: #444;
            color: white;
            font-size: 16px; /* Ensure at least 16px font size */
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: #555;
        }
        #popup {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            padding: 20px;
            color: white;
            border-radius: 10px;
            font-size: 1.2em;
            text-align: center;
        }
        #popup.success {
            background-color: green;
        }
        #popup.error {
            background-color: red;
        }
    </style>
    <script>
        function showPopup(message, isSuccess) {
            const popup = document.getElementById("popup");
            popup.textContent = message;
            popup.className = isSuccess ? "success" : "error";
            popup.style.display = "block";
            setTimeout(() => {
                popup.style.display = "none";
                if (isSuccess) {
                    document.getElementById("matricule").value = "";
                    document.getElementById("prenom").value = "";
                    document.getElementById("raison").value = "";
                    document.getElementById("montant").value = "";
                }
            }, 1000);
        }

        async function handleSubmit(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const response = await fetch("/submit", {
                method: "POST",
                body: formData
            });
            const result = await response.json();
            showPopup(result.message, result.success);
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="/static/logo.png" alt="Casino Logo">
        </div>
        <form onsubmit="handleSubmit(event)">
            <div class="form-group">
                <label for="matricule">Matricule de Croupier</label>
                <input type="text" id="matricule" name="matricule" required>
            </div>
            <div class="form-group">
                <label for="prenom">Prénom</label>
                <input type="text" id="prenom" name="prenom" required>
            </div>
            <div class="form-group">
                <label for="raison">Raison</label>
                <input type="text" id="raison" name="raison">
            </div>
            <div class="form-group">
                <label for="montant">Montant</label>
                <input type="number" id="montant" name="montant" required>
            </div>
            <button type="submit">Envoyer</button>
        </form>
    </div>
    <div id="popup"></div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/submit', methods=['POST'])
def submit():
    matricule = request.form['matricule']
    prenom = request.form['prenom']
    montant = request.form['montant']
    raison = request.form['raison']

    # Check if the matricule is valid
    if matricule in croupiers.keys():
        ticket = {
            "matricule": matricule,
            "prenom": prenom,
            "montant": montant,
            "raison": raison
        }
        # Publish to MQTT
        mqtt_client.publish(mqtt_topic, json.dumps(ticket))
        return jsonify(success=True, message="Ticket envoyé avec succès !")
    else:
        return jsonify(success=False, message="Erreur : matricule invalide !")

# Run Flask app on port 1886
if __name__ == '__main__':
    app.run(debug=False, host=HOST_ADRESS, port=1886)
