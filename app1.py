from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
from bson.errors import InvalidId

app = Flask(__name__)
# Replace with a strong, random key in production
app.secret_key = '1879a49b06ff9b4ef1efd9b63dbd911df26b566d1d0769dd5726607d63d06759'

# MongoDB connection
client = MongoClient('mongodb+srv://vagadisaikiran31:123sai@cluster0.njq1gj3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['travel_booking_db']

# Collections
users_collection = db['users']
flights_collection = db['flights']
trains_collection = db['trains']
bookings_collection = db['bookings']
hotels_collection = db['hotels']

# --- Sample Data Insertion Functions ---
def insert_sample_train_data():
    """Inserts sample train data into the MongoDB collection if it's empty."""
    if trains_collection.count_documents({}) == 0:
        sample_trains = [
            {"_id": ObjectId(), "name": "Duronto Express", "train_number": "12285", "source": "Hyderabad", "destination": "Delhi", "departure_time": "07:00 AM", "arrival_time": "05:00 AM (next day)", "price": 1800, "date": "2025-07-10"},
            {"_id": ObjectId(), "name": "AP Express", "train_number": "12723", "source": "Hyderabad", "destination": "Vijayawada", "departure_time": "09:00 AM", "arrival_time": "03:00 PM", "price": 450, "date": "2025-07-10"},
            {"_id": ObjectId(), "name": "Gouthami Express", "train_number": "12737", "source": "Guntur", "destination": "Hyderabad", "departure_time": "08:00 PM", "arrival_time": "06:00 AM (next day)", "price": 600, "date": "2025-07-10"},
            {"_id": ObjectId(), "name": "Chennai Express", "train_number": "12839", "source": "Bengaluru", "destination": "Chennai", "departure_time": "10:30 AM", "arrival_time": "05:30 PM", "price": 750, "date": "2025-07-11"},
            {"_id": ObjectId(), "name": "Mumbai Mail", "train_number": "12101", "source": "Hyderabad", "destination": "Mumbai", "departure_time": "06:00 PM", "arrival_time": "09:00 AM (next day)", "price": 1200, "date": "2025-07-10"},
            {"_id": ObjectId(), "name": "Godavari Express", "train_number": "12720", "source": "Vijayawada", "destination": "Hyderabad", "departure_time": "05:00 PM", "arrival_time": "11:00 PM", "price": 400, "date": "2025-07-10"},
        ]
        trains_collection.insert_many(sample_trains)
        print("Sample train data inserted into MongoDB.")

def insert_sample_flight_data():
    """Inserts sample flight data into the MongoDB collection if it's empty."""
    if flights_collection.count_documents({}) == 0:
        sample_flights = [
            {"_id": ObjectId(), "airline": "IndiGo", "flight_number": "6E 2345", "source": "Delhi", "destination": "Mumbai", "departure_time": "10:00 AM", "arrival_time": "12:00 PM", "price": 5000, "date": "2025-07-15"},
            {"_id": ObjectId(), "airline": "Air India", "flight_number": "AI 400", "source": "Mumbai", "destination": "Bengaluru", "departure_time": "03:00 PM", "arrival_time": "05:00 PM", "price": 6500, "date": "2025-07-15"},
        ]
        flights_collection.insert_many(sample_flights)
        print("Sample flight data inserted into MongoDB.")

def insert_sample_hotel_data():
    """Inserts sample hotel data into the MongoDB collection if it's empty."""
    if hotels_collection.count_documents({}) == 0:
        sample_hotels = [
            {"_id": ObjectId(), "name": "The Grand Hotel", "location": "Mumbai", "price_per_night": 4000},
            {"_id": ObjectId(), "name": "City Centre Inn", "location": "Delhi", "price_per_night": 2500},
        ]
        hotels_collection.insert_many(sample_hotels)
        print("Sample hotel data inserted into MongoDB.")

def insert_default_user():
    """Inserts a default user if one does not already exist."""
    default_email = "vagadisaikiran31@gmail.com"
    default_password = "123sai"
    if not users_collection.find_one({'email': default_email}):
        hashed_password = generate_password_hash(default_password)
        users_collection.insert_one({'fullname': 'vagadi saikiran', 'email': default_email, 'password': hashed_password})
        print("Default user inserted.")

# --- Routes ---

@app.route('/')
def index():
    """Renders the home page."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match!')
        if users_collection.find_one({'email': email}):
            return render_template('register.html', error='Email already exists!')
        
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({'fullname': fullname, 'email': email, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            session['fullname'] = user.get('fullname', email)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', message='Invalid email or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs out the user by clearing the session."""
    session.pop('email', None)
    session.pop('fullname', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Displays the user dashboard with their bookings."""
    if 'email' not in session:
        return redirect(url_for('login'))

    user_email = session['email']
    user_fullname = session.get('fullname', user_email)
    user_bookings = list(bookings_collection.find({'user_email': user_email}).sort('booking_date', -1))

    for booking in user_bookings:
        if '_id' in booking and isinstance(booking['_id'], ObjectId):
            booking['booking_id'] = str(booking['_id'])
        else:
            booking['booking_id'] = None
        
        if booking.get('booking_type') == 'bus':
            booking['type'] = 'Bus'
            booking['details'] = f"{booking.get('name', 'N/A')} from {booking.get('source', 'N/A')} to {booking.get('destination', 'N/A')}"
        elif booking.get('booking_type') == 'train':
            booking['type'] = 'Train'
            booking['details'] = f"{booking.get('name', 'N/A')} ({booking.get('train_number', 'N/A')}) from {booking.get('source', 'N/A')} to {booking.get('destination', 'N/A')}"
        elif booking.get('booking_type') == 'flight':
            booking['type'] = 'Flight'
            booking['details'] = f"{booking.get('airline', 'N/A')} ({booking.get('flight_number', 'N/A')}) from {booking.get('source', 'N/A')} to {booking.get('destination', 'N/A')}"
        elif booking.get('booking_type') == 'hotel':
            booking['type'] = 'Hotel'
            booking['details'] = f"{booking.get('hotel_name', 'N/A')} in {booking.get('location', 'N/A')}"
        else:
            booking['type'] = 'N/A'
            booking['details'] = 'Booking details not available.'

    return render_template('dashboard.html', name=user_fullname, bookings=user_bookings)

# --- Bus Search and Booking Flow ---

@app.route('/bus')
def bus():
    """Renders the bus search page."""
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('bus.html')

@app.route('/confirm_bus_booking', methods=['POST'])
def confirm_bus_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    name = request.form.get('name')
    source = request.form.get('source')
    destination = request.form.get('destination')
    time = request.form.get('time')
    bus_type = request.form.get('type')
    travel_date = request.form.get('date')
    
    try:
        price_per_person = float(request.form.get('price'))
        num_persons = int(request.form.get('persons'))
    except (TypeError, ValueError):
        print("Error: Invalid price or number of persons provided for bus booking.")
        return redirect(url_for('bus'))

    total_price = price_per_person * num_persons

    booking_details = {
        'name': name,
        'source': source,
        'destination': destination,
        'time': time,
        'type': bus_type,
        'price_per_person': price_per_person,
        'travel_date': travel_date,
        'num_persons': num_persons,
        'total_price': total_price,
        'booking_type': 'bus',
        'user_email': session['email']
    }
    session['pending_booking'] = booking_details

    return render_template('confirm.html', booking=booking_details, booking_type='bus')

@app.route('/final_confirm_booking', methods=['POST'])
def final_confirm_booking():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'User not logged in', 'redirect': url_for('login')}), 401

    booking_data = session.pop('pending_booking', None)
    if not booking_data:
        return jsonify({'success': False, 'message': 'No pending booking to confirm.'}), 400

    try:
        booking_data['booking_date'] = datetime.now().isoformat()
        bookings_collection.insert_one(booking_data)
        return jsonify({
            'success': True,
            'message': 'Bus booking confirmed successfully!'
        })
    except Exception as e:
        print(f"Error saving bus booking to DB: {e}")
        return jsonify({'success': False, 'message': f'Failed to confirm booking: {str(e)}'}), 500

# --- Train Search and Booking Flow ---

@app.route('/train')
def train():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('train.html')

@app.route('/confirm_train_booking', methods=['POST'])
def confirm_train_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    name = request.form.get('name')
    train_number = request.form.get('trainNumber')
    source = request.form.get('source')
    destination = request.form.get('destination')
    departure_time = request.form.get('departureTime')
    arrival_time = request.form.get('arrivalTime')
    travel_date = request.form.get('date')

    try:
        price_per_person = float(request.form.get('price'))
        num_persons = int(request.form.get('persons'))
    except (TypeError, ValueError):
        print("Error: Invalid price or number of persons provided for train booking.")
        return redirect(url_for('train'))

    total_price = price_per_person * num_persons

    booking_details = {
        'name': name,
        'train_number': train_number,
        'source': source,
        'destination': destination,
        'departure_time': departure_time,
        'arrival_time': arrival_time,
        'price_per_person': price_per_person,
        'travel_date': travel_date,
        'num_persons': num_persons,
        'total_price': total_price,
        'booking_type': 'train',
        'user_email': session['email']
    }
    session['pending_booking'] = booking_details

    return render_template('confirmtrain.html', booking=booking_details)

@app.route('/final_confirm_train_booking', methods=['POST'])
def final_confirm_train_booking():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'User not logged in', 'redirect': url_for('login')}), 401

    booking_data = session.pop('pending_booking', None)
    if not booking_data:
        return jsonify({'success': False, 'message': 'No pending booking to confirm.'}), 400

    try:
        booking_data['booking_date'] = datetime.now().isoformat()
        bookings_collection.insert_one(booking_data)
        return jsonify({
            'success': True,
            'message': 'Train booking confirmed successfully!'
        })
    except Exception as e:
        print(f"Error saving train booking to DB: {e}")
        return jsonify({'success': False, 'message': f'Failed to confirm train booking: {str(e)}'}), 500

# --- Flight Search and Booking Flow ---

@app.route('/flight', methods=['GET', 'POST'])
def flight():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('flight.html')

@app.route('/confirm_flight_booking', methods=['POST'])
def confirm_flight_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    airline = request.form.get('airline')
    flight_number = request.form.get('flightNumber')
    source = request.form.get('source')
    destination = request.form.get('destination')
    departure_time = request.form.get('departureTime')
    arrival_time = request.form.get('arrivalTime')
    travel_date = request.form.get('date')

    try:
        price_per_person = float(request.form.get('price'))
        num_persons = int(request.form.get('persons'))
    except (TypeError, ValueError):
        print("Error: Invalid price or number of persons provided for flight booking.")
        return redirect(url_for('flight'))

    total_price = price_per_person * num_persons

    booking_details = {
        'airline': airline,
        'flight_number': flight_number,
        'source': source,
        'destination': destination,
        'departure_time': departure_time,
        'arrival_time': arrival_time,
        'price_per_person': price_per_person,
        'travel_date': travel_date,
        'num_persons': num_persons,
        'total_price': total_price,
        'booking_type': 'flight',
        'user_email': session['email']
    }
    session['pending_booking'] = booking_details

    return render_template('confirmflight.html', booking=booking_details)

@app.route('/final_confirm_flight_booking', methods=['POST'])
def final_confirm_flight_booking():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'User not logged in', 'redirect': url_for('login')}), 401

    booking_data = session.pop('pending_booking', None)
    if not booking_data:
        return jsonify({'success': False, 'message': 'No pending booking to confirm.'}), 400

    try:
        booking_data['booking_date'] = datetime.now().isoformat()
        bookings_collection.insert_one(booking_data)
        return jsonify({
            'success': True,
            'message': 'Flight booking confirmed successfully!'
        })
    except Exception as e:
        print(f"Error saving flight booking to DB: {e}")
        return jsonify({'success': False, 'message': f'Failed to confirm flight booking: {str(e)}'}), 500

# --- Hotel Search and Booking Flow ---

@app.route('/hostel')
def hotel():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('hotel.html')

@app.route('/confirm_hotel_booking', methods=['POST'])
def confirm_hotel_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    hotel_name = request.form.get('hotelName')
    location = request.form.get('location')
    check_in_date = request.form.get('checkInDate')
    check_out_date = request.form.get('checkOutDate')
    
    try:
        num_rooms = int(request.form.get('numRooms'))
        num_guests = int(request.form.get('numGuests'))
        price_per_night = float(request.form.get('pricePerNight'))
        num_nights = int(request.form.get('numNights'))
    except (TypeError, ValueError):
        print("Error: Invalid numeric data provided for hotel booking.")
        return redirect(url_for('hostel'))

    total_price = price_per_night * num_rooms * num_nights

    booking_details = {
        'hotel_name': hotel_name,
        'location': location,
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'num_rooms': num_rooms,
        'num_guests': num_guests,
        'price_per_night': price_per_night,
        'num_nights': num_nights,
        'total_price': total_price,
        'booking_type': 'hotel',
        'user_email': session['email']
    }
    session['pending_booking'] = booking_details

    return render_template('confirmhotel.html', booking=booking_details)

@app.route('/final_confirm_hotel_booking', methods=['POST'])
def final_confirm_hotel_booking():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'User not logged in', 'redirect': url_for('login')}), 401

    booking_data = session.pop('pending_booking', None)
    if not booking_data:
        return jsonify({'success': False, 'message': 'No pending booking to confirm.'}), 400

    try:
        booking_data['booking_date'] = datetime.now().isoformat()
        bookings_collection.insert_one(booking_data)
        return jsonify({
            'success': True,
            'message': 'Hotel booking confirmed successfully!'
        })
    except Exception as e:
        print(f"Error saving hotel booking to DB: {e}")
        return jsonify({'success': False, 'message': f'Failed to confirm hotel booking: {str(e)}'}), 500

# --- Cancel Booking Route ---
@app.route('/cancel', methods=['POST'])
def cancel():
    """
    Handles cancellation of a booking.
    """
    if 'email' not in session:
        return redirect(url_for('login'))

    booking_id = request.form.get('booking_id')
    user_email = session['email']

    if not booking_id:
        print("Error: booking_id is missing for cancellation.")
        return redirect(url_for('dashboard'))

    try:
        object_id_to_delete = ObjectId(booking_id)
        query = {'_id': object_id_to_delete, 'user_email': user_email}
        result = bookings_collection.delete_one(query)
        if result.deleted_count == 1:
            print(f"Booking {booking_id} cancelled by {user_email}")
        else:
            print(f"Booking {booking_id} not found or not owned by {user_email}. Deleted count: {result.deleted_count}")
    except InvalidId:
        print(f"Booking ID '{booking_id}' is not a valid ObjectId.")
    except Exception as e:
        print(f"Error cancelling booking {booking_id}: {e}")

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Insert sample data and default user when the app starts
    insert_sample_train_data()
    insert_sample_flight_data()
    insert_sample_hotel_data()
    insert_default_user()
    app.run(host='0.0.0.0', port=8000, debug=True)