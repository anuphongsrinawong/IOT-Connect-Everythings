# backend/app.py
import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from flask_cors import CORS # Import CORS

# สร้าง Flask App
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# กำหนดค่า SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for development

# Store devices in memory (instead of database)
devices = {}

# Function to generate a unique device ID
def generate_device_id():
    """Generate a unique device ID."""
    if not devices:
        return 1
    else:
        return max(devices.keys()) + 1

# SocketIO event handler for connecting
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'message': 'Connected to server'})  # Send message to client

# SocketIO event handler for disconnecting
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Route to get all devices
@app.route('/api/devices', methods=['GET'])
def get_devices():
    """
    Returns all devices.
    """
    device_list = list(devices.values())  # Get values (devices) from the dictionary
    return jsonify(device_list), 200

# Route to get a single device by ID
@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """
    Returns a single device by ID.
    """
    if device_id not in devices:
        return jsonify({'message': 'Device not found'}), 404
    return jsonify(devices[device_id]), 200

# Route to create a new device
@app.route('/api/devices', methods=['POST'])
def create_device():
    """
    Creates a new device.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid input.  Please provide device data.'}), 400

    name = data.get('name')
    type = data.get('type')
    details = data.get('details', None)  # Get details, default to None if not provided.

    if not name or not type:
        return jsonify({'message': 'Name and type are required fields.'}), 400

    # Check if device with same name already exists
    for device in devices.values():  # Iterate through values
        if device['name'] == name:
            return jsonify({'message': 'Device with this name already exists.'}), 400

    device_id = generate_device_id()
    new_device = {
        'id': device_id,
        'name': name,
        'type': type,
        'connection_status': 'Disconnected',
        'last_seen': datetime.utcnow().isoformat(),
        'details': details
    }
    devices[device_id] = new_device  # Use device_id as key
    # Emit a SocketIO event to notify clients of the new device
    socketio.emit('new_device', new_device, broadcast=True)
    return jsonify({'message': 'Device created successfully.', 'device': new_device}), 201

# Route to update an existing device
@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """
    Updates an existing device.
    """
    if device_id not in devices:
        return jsonify({'message': 'Device not found'}), 404
    device = devices[device_id]  # Get device from devices dict.
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid input. Please provide data to update.'}), 400

    # update only if the key is present in the json
    if 'name' in data:
        device['name'] = data['name']
    if 'type' in data:
        device['type'] = data['type']
    if 'connection_status' in data:
        device['connection_status'] = data['connection_status']
    if 'details' in data:
        device['details'] = data['details']
    device['last_seen'] = datetime.utcnow().isoformat()

    devices[device_id] = device  # Update the device in the dictionary
    socketio.emit('device_updated', device, broadcast=True)  # emit update to all
    return jsonify({'message': 'Device updated successfully.', 'device': device}), 200

# Route to delete a device
@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """
    Deletes a device.
    """
    if device_id not in devices:
        return jsonify({'message': 'Device not found'}), 404
    deleted_device = devices.pop(device_id)  # remove from dict and return the device.
    socketio.emit('device_deleted', {'id': device_id}, broadcast=True)  # Notify frontend
    return jsonify({'message': 'Device deleted successfully.', 'deleted_device': deleted_device}), 200

# Function to add initial devices
def add_initial_devices():
    """Adds 5 initial devices to the dictionary."""
    global devices  # Use the global devices dictionary
    if not devices:
        devices = {
            1: {'id': 1, 'name': 'Temperature Sensor 1', 'type': 'Temperature Sensor', 'connection_status': 'Connected', 'last_seen': datetime(2024, 1, 20, 10, 0, 0).isoformat(), 'details': 'Measures temperature in Room A'},
            2: {'id': 2, 'name': 'Humidity Sensor 1', 'type': 'Humidity Sensor', 'connection_status': 'Connected', 'last_seen': datetime(2024, 1, 20, 10, 15, 0).isoformat(), 'details': 'Measures humidity in Room A'},
            3: {'id': 3, 'name': 'Smart Switch 1', 'type': 'Smart Switch', 'connection_status': 'Disconnected', 'last_seen': datetime(2024, 1, 20, 11, 0, 0).isoformat(), 'details': 'Controls light in Room B'},
            4: {'id': 4, 'name': 'Pressure Sensor 1', 'type': 'Pressure Sensor', 'connection_status': 'Connected', 'last_seen': datetime(2024, 1, 20, 12, 0, 0).isoformat(), 'details': 'Measures pressure in Tank 1'},
            5: {'id': 5, 'name': 'Camera 1', 'type': 'Camera', 'connection_status': 'Idle', 'last_seen': datetime(2024, 1, 20, 13, 0, 0).isoformat(), 'details': 'Records video in Lobby'}
        }

# Run the app
if __name__ == '__main__':
    add_initial_devices()  # Add initial devices when the app starts
    socketio.run(app, debug=True, host='0.0.0.0')  # make accessible externally
    # socketio.run(app, debug=True) #remove host='0.0.0.0' if you want to run only on local machine
