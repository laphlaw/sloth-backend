from flask import Blueprint, request, jsonify
from . import db
from .models import Alarm, Location
from datetime import datetime, time
from flask import g
from functools import wraps
import jwt
from .config import Config
from .auth import token_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/alarms', methods=['POST'])
@token_required
def set_alarm():
    data = request.get_json()
    alarm_time = data.get('time')  # Expecting "HH:MM" format
    gps_lat = data.get('gps_lat')
    gps_lng = data.get('gps_lng')

    if not all([alarm_time, gps_lat, gps_lng]):
        return jsonify({'message': 'Missing required fields.'}), 400

    try:
        alarm_time_obj = datetime.strptime(alarm_time, '%H:%M').time()
    except ValueError:
        return jsonify({'message': 'Invalid time format. Use HH:MM.'}), 400

    alarm = Alarm(
        time=alarm_time_obj,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        user_id=request.user.id
    )
    db.session.add(alarm)
    db.session.commit()

    return jsonify({'message': 'Alarm set successfully.', 'alarm_id': alarm.id}), 201

@api_bp.route('/alarms', methods=['GET'])
@token_required
def get_alarms():
    alarms = Alarm.query.filter_by(user_id=request.user.id).all()
    alarms_list = []
    for alarm in alarms:
        alarms_list.append({
            'id': alarm.id,
            'time': alarm.time.strftime('%H:%M'),
            'is_active': alarm.is_active,
            'gps_lat': alarm.gps_lat,
            'gps_lng': alarm.gps_lng,
            'created_at': alarm.created_at.isoformat()
        })
    return jsonify({'alarms': alarms_list}), 200

@api_bp.route('/alarms/<int:alarm_id>/kill', methods=['POST'])
@token_required
def kill_alarm(alarm_id):
    alarm = Alarm.query.filter_by(id=alarm_id, user_id=request.user.id).first()
    if not alarm:
        return jsonify({'message': 'Alarm not found.'}), 404

    alarm.is_active = False
    db.session.commit()
    return jsonify({'message': 'Alarm killed successfully.'}), 200

@api_bp.route('/locations', methods=['POST'])
@token_required
def create_location():
    data = request.get_json()
    name = data.get('name')
    gps_lat = data.get('gps_lat')
    gps_lng = data.get('gps_lng')

    if not all([name, gps_lat, gps_lng]):
        return jsonify({'message': 'Missing required fields.'}), 400

    location = Location(
        name=name,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        user_id=request.user.id
    )
    db.session.add(location)
    db.session.commit()

    return jsonify({'message': 'Location saved successfully.', 'location_id': location.id}), 201

@api_bp.route('/locations', methods=['GET'])
@token_required
def get_locations():
    locations = Location.query.filter_by(user_id=request.user.id).all()
    locations_list = []
    for loc in locations:
        locations_list.append({
            'id': loc.id,
            'name': loc.name,
            'gps_lat': loc.gps_lat,
            'gps_lng': loc.gps_lng,
            'created_at': loc.created_at.isoformat()
        })
    return jsonify({'locations': locations_list}), 200

@api_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@token_required
def delete_location(location_id):
    location = Location.query.filter_by(id=location_id, user_id=request.user.id).first()
    if not location:
        return jsonify({'message': 'Location not found.'}), 404

    db.session.delete(location)
    db.session.commit()
    return jsonify({'message': 'Location deleted successfully.'}), 200
