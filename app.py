import math
from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
from flask_migrate import Migrate
import matplotlib.pyplot as plt

plt.switch_backend('Agg')  # Use a non-interactive backend for matplotlib

app = Flask(__name__)

# Set the secret key for flash messages
app.config['SECRET_KEY'] = 'sweet_and_sour'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkease.db'
db = SQLAlchemy()
db.init_app(app)

migrate = Migrate(app, db)

app.app_context().push()

# ------------------ MODELS ------------------

class User(db.Model):
    __tablename__ = 'user_details'
    uid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String(10), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False, unique=True)
    pincode = db.Column(db.String(6), nullable=False)
    is_superUser = db.Column(db.Boolean, default=False)

class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    pl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lot_name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=False, unique=True)
    pin_code = db.Column(db.String(10), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user_details.uid'), nullable=False)
    user = db.relationship('User', backref='parking_lot')

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    ps_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.pl_id'), nullable=False)
    parking_lot = db.relationship('ParkingLot', backref='parking_spot')

    status = db.Column(db.String(1), nullable=False, default='A')  # A = Available, O = Occupied
    spot_number = db.Column(db.Integer, nullable=False)


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)  
    status = db.Column(db.String(50), default='Active')  
    vehicle_number = db.Column(db.String(20), nullable=False)  

    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.ps_id'), nullable=False)
    spot = db.relationship('ParkingSpot', backref='reservations')

    user_id = db.Column(db.Integer, db.ForeignKey('user_details.uid'), nullable=False)
    user = db.relationship('User', backref='reservations')


db.create_all()


# ------------------ COMMON ROUTES ------------------

@app.route('/') 
def default():
    return render_template('default.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        return render_template('userlogin.html', user=user)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
    
        user_exists = User.query.filter_by(username=username).first()
        if not user_exists:
            flash("User does not exist. Please register.")
            return redirect('/register')
        else:
            if user_exists and user_exists.password == password:
                if user_exists.is_superUser:
                    return redirect(f'/superUserdashboard/{user_exists.uid}')  #passing the string id here
                else:
                    return redirect(f'/userdashboard/{user_exists.uid}')
            else:
                flash("Invalid username or password. Please try again.")
                return redirect('/login')

@app.route('/editprofile/<uid>', methods=['GET', 'POST'])
def editprofile(uid):

    if request.method == 'GET':
        user = User.query.filter_by(uid=uid).first()
        return render_template('edit_profile.html', user=user)

    if request.method == 'POST':

        new_password = request.form.get('password')
        new_name = request.form.get('name')
        new_phone = request.form.get('phone')
        new_address = request.form.get('address')
        new_pincode = request.form.get('pincode')

        user_update = User.query.filter_by(uid=uid).first()

        user_update.password = new_password
        user_update.name = new_name
        user_update.phone = new_phone
        user_update.address = new_address
        user_update.pincode = new_pincode

        # Check if phone is changing and if the new phone is already taken
        if new_phone != user_update.phone:
            if User.query.filter_by(phone=new_phone).first():
                flash("Phone number already in use.")
                return redirect(f'/editprofile/{uid}')

        # Check if address is changing and if the new address is already taken
        if new_address != user_update.address:
            if User.query.filter_by(address=new_address).first():
                flash("Address already in use.")
                return redirect(f'/editprofile/{uid}')

        db.session.commit()
        flash("Profile updated successfully.")
        return redirect(f'/editprofile/{uid}')

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    if request.method == 'GET':
        return render_template('forgot_password.html')

    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("User not found.")
            return redirect('/forgotpassword')

        if user.phone != phone:
            flash("Phone number doesn't match our records.")
            return redirect('/forgotpassword')

        # Update the password
        user.password = password
        db.session.commit()

        flash("Password reset successful. Please log in.")
        return redirect('/login')


@app.route('/logout', methods=['GET'])
def logout():
    flash("You have been logged out successfully.")
    return redirect('/login')


# ------------------ USER ROUTES ------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            flash("Phone number already registered. Please use a different phone number.")
            return redirect('/register')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("User already exists. Please log in.")
            return redirect('/register')

        new_user = User(
        username=username,
        password=password,
        name=name,
        phone=phone,
        address=address,
        pincode=pincode,
        is_superUser=False  # Forcefully set to user
    )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect('/login')
    

@app.route('/userdashboard/<uid>', methods=['GET', 'POST'])
def userdashboard(uid):
    user = User.query.filter_by(uid=int(uid)).first()

    if not user:
        flash("❌ User not found.")
        return redirect('/')  
    
    if user.is_superUser:
        flash("⚠️ Access Denied: Superusers cannot access the User Dashboard.")
        return redirect(f"/superUserdashboard/{uid}")
    
    all_pincodes = ParkingLot.query.with_entities(ParkingLot.pin_code).distinct().all()
    price_per_hour = ParkingLot.query.with_entities(ParkingLot.price_per_hour).all()

    results = []
    selected_pincode = None

    # Count user's active reservations
    active_reservations_count = Reservation.query.filter_by(user_id=user.uid, status='Active').count()
    max_active_reservations = 4

    can_book_more = active_reservations_count < max_active_reservations
    if not can_book_more:
        flash("⚠️ You can only book up to 4 parking spots at a time.")

    if request.method == 'POST':
        selected_pincode = request.form.get('pincode')

        if selected_pincode:
            parking_lots = ParkingLot.query.filter_by(pin_code=selected_pincode).all()

            for lot in parking_lots:
                available_spots = ParkingSpot.query.filter_by(lot_id=lot.pl_id, status='A').all()
                results.append({
                    'pl_id': lot.pl_id,
                    'lot_name': lot.lot_name,
                    'price_per_hour':lot.price_per_hour,
                    'available_spot_id': available_spots[0].ps_id if available_spots else None,
                    'available_spot_number': available_spots[0].spot_number if available_spots else None,
                    'lot_address': lot.address,
                    'available_spots': len(available_spots)
                })


    # Fetch user's reservation history
    reservations = Reservation.query.filter_by(user_id=user.uid).order_by(Reservation.parking_timestamp.desc()).all()

    history = []
    for res in reservations:
        if not res.spot:
            continue

        lot = ParkingLot.query.filter_by(pl_id=res.spot.lot_id).first()
        if not lot:
            continue
        
        history.append({
            'lot_id': lot.pl_id,
            'lot_address': lot.address,
            'spot_number': res.spot.spot_number,
            'vehicle_number': res.vehicle_number,
            'parking_timestamp': res.parking_timestamp.strftime('%Y-%m-%d %H:%M'),
            'leaving_timestamp': res.leaving_timestamp.strftime('%Y-%m-%d %H:%M') if res.leaving_timestamp else 'NA',
            'parking_cost': f"₹{res.parking_cost:.2f}" if res.parking_cost else '-',
            'status': 'Released' if res.status.lower() != 'active' else 'Active',
            'reservation_id': res.id  # Added reservation ID for reference
        })

    return render_template(
        'userdashboard.html',
        user=user,
        all_pincodes=all_pincodes,
        price_per_hour=price_per_hour,
        results=results,
        selected_pincode=selected_pincode,
        history=history,
        active_reservations_count=active_reservations_count,
        max_active_reservations=max_active_reservations,
        can_book_more=can_book_more
    )




@app.route('/bookparkingspot/<user_id>/<spot_id>', methods=['GET', 'POST'])
def bookparkingspot(user_id, spot_id):
    user = User.query.filter_by(uid=int(user_id)).first()
    spot = ParkingSpot.query.filter_by(ps_id=int(spot_id)).first()

    if request.method == 'GET':
        return render_template('book_parking_spot.html', user=user, spot=spot)

    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')

        # Check if user has less than 4 active reservations
        active_count = Reservation.query.filter_by(user_id=user.uid, status='Active').count()
        if active_count >= 4:
            return redirect(f'/userdashboard/{user.uid}')

        # Check if vehicle number is already reserved
        existing_reservation = Reservation.query.filter_by(vehicle_number=vehicle_number, status='Active').first()
        if existing_reservation:
            flash(f"Vehicle number {vehicle_number} already has an active reservation.")
            return redirect(f'/userdashboard/{user.uid}')

        if spot and spot.status == 'A':
            spot.status = 'O'
            db.session.commit()

            # Create reservation
            new_reservation = Reservation(
                parking_timestamp=datetime.now(),
                spot_id=spot.ps_id,
                user_id=user.uid,
                status="Active",
                vehicle_number=vehicle_number
            )
            db.session.add(new_reservation)
            db.session.commit()

            flash("Parking spot booked successfully.")
        else:
            flash("Parking spot is not available.")

        return redirect(f'/userdashboard/{user.uid}')


@app.route('/reservationdetails/<reservation_id>', methods=['GET', 'POST'])
def reservationdetails(reservation_id):
    reservation = Reservation.query.filter_by(id=int(reservation_id)).first()
    user = User.query.filter_by(uid=reservation.user_id).first()
    lot = ParkingLot.query.filter_by(pl_id=reservation.spot.lot_id).first()

    # Calculate estimated cost
    if reservation.leaving_timestamp:
        duration = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600  # in hours
    else:
        duration = (datetime.now() - reservation.parking_timestamp).total_seconds() / 3600  # in hours
    
    rounded_duration = math.ceil(duration)
    estimated_cost = rounded_duration * lot.price_per_hour

    if request.method == 'POST':

        # Handle releasing the parking spot
        spot = ParkingSpot.query.filter_by(ps_id=reservation.spot_id).first()
        spot.status = 'A'  
        reservation.status = 'Released'  
        reservation.leaving_timestamp = datetime.now() 
        reservation.parking_cost = estimated_cost 

        db.session.commit()
        flash("Parking spot released successfully.")
        return redirect(f"/userdashboard/{user.uid}")

    return render_template('reservation_details.html', reservation=reservation, user=user, lot=lot, estimated_cost=estimated_cost,rounded_duration=rounded_duration)



@app.route('/releaseparkingspot/<reservation_id>', methods=['POST'])
def releaseparkingspot(reservation_id):
    reservation = Reservation.query.filter_by(id=int(reservation_id)).first()
    spot = ParkingSpot.query.filter_by(ps_id=reservation.spot_id).first()

    spot.status = 'A'  
    reservation.status = 'Released'  
    reservation.leaving_timestamp = datetime.now()  

    db.session.commit()

    flash("Parking spot released successfully.")
    return redirect(f"/userdashboard/{reservation.user_id}")

@app.route('/userSummary/<uid>', methods=['GET', 'POST'])
def userSummary(uid):
    user = User.query.filter_by(uid=int(uid)).first()
    reservations = Reservation.query.filter_by(user_id=user.uid).all()

    if user.is_superUser:
        flash("⚠️ Access Denied: Only Users can access this page.")
        return redirect(f"/superUserdashboard/{uid}")
    
    # ------ chart 1: Reservation History Over Time ------
    reservation_times = [r.parking_timestamp.strftime('%Y-%m-%d') for r in reservations if r.user_id == user.uid]
    unique_dates = list(set(reservation_times))  # Unique dates of reservations
    reservations_per_day = [reservation_times.count(date) for date in unique_dates]

    fig1, ax1 = plt.subplots()
    ax1.plot(unique_dates, reservations_per_day, marker='o', color='blue')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Reservations')
    ax1.set_title('Reservation History Over Time')

    plot_path_1 = "static/reservation_history.png"
    fig1.tight_layout()
    fig1.savefig(plot_path_1)
    plt.close(fig1)

# --- Chart2: Revenue Spent by User in Each Parking Lot --- 

    user_lot_revenue = {}

    for res in reservations:
        if res.user_id == user.uid and res.spot and res.spot.parking_lot and res.parking_cost:
            lot_name = res.spot.parking_lot.lot_name
            if lot_name in user_lot_revenue:
                user_lot_revenue[lot_name] += res.parking_cost  # Add to existing revenue
            else:
                user_lot_revenue[lot_name] = res.parking_cost  # Create a new entry

    lot_names_user = list(user_lot_revenue.keys())
    user_revenues = list(user_lot_revenue.values())

    fig2, ax2 = plt.subplots()
    ax2.bar(lot_names_user, user_revenues, color='green', edgecolor='black', width=0.4)
    ax2.set_xlabel('Parking Lot')
    ax2.set_ylabel('Total Amount Spent (₹)')
    ax2.set_title(f'Total Amount Spent by {user.name} in Each Parking Lot')

    plot_path_2 = "static/user_revenue_per_lot.png"
    fig2.tight_layout()
    fig2.savefig(plot_path_2)
    plt.close(fig2)

#-------- chart 3: Active Reservations Count pie chart --------

    active_reservations = len([r for r in reservations if r.status == 'Active'])

    fig3, ax3 = plt.subplots()

    explode = (0.1, 0)  # "explode" the first slice (Active reservations)
    ax3.pie([active_reservations, len(reservations) - active_reservations],
        labels=['Active', 'Released'], autopct='%1.1f%%', startangle=90,
        explode=explode, colors=['skyblue', 'lightcoral'])
    ax3.set_title(f"Active Reservations Count for {user.name}")

    plot_path_3 = "static/active_reservations_pie_chart.png"
    fig3.tight_layout()
    fig3.savefig(plot_path_3)
    plt.close(fig3)

    #--------- Histogram of Parking Durations ---------
    durations = [(res.leaving_timestamp - res.parking_timestamp).total_seconds() / 60 for res in reservations if res.user_id == user.uid and res.leaving_timestamp]

    bins=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
    fig4, ax4 = plt.subplots()
    ax4.hist(durations, bins=bins, color='purple', edgecolor='black') 
    ax4.set_xlabel('Duration (minutes)')
    ax4.set_ylabel('Number of Parking Sessions') 
    ax4.set_title('Average Parking Duration')

    plot_path_4 = "static/average_parking_duration.png"
    fig4.tight_layout()
    fig4.savefig(plot_path_4)
    plt.close(fig4)


    return render_template('user_summary.html', user=user, reservations=reservations,plot_path_1=plot_path_1, plot_path_2=plot_path_2, plot_path_3=plot_path_3, plot_path_4=plot_path_4)

# ------------------ SUPERUSER ROUTES ------------------


@app.route('/superUserdashboard/<uid>', methods=['GET', 'POST'])
def superUserdashboard(uid):
    if request.method == 'GET':
        user = User.query.filter_by(uid=int(uid)).first()
        if not user:
            flash("❌ User not found.")
            return redirect('/') 

        if not user.is_superUser:
            flash("⚠️ Access Denied: Only superusers can access this page.")
            return redirect(f"/userdashboard/{uid}") 

        lots = ParkingLot.query.all()
        parking_spots = ParkingSpot.query.all()

        for lot in lots:
            lot_spots = [spot for spot in parking_spots if spot.lot_id == lot.pl_id]
            lot.occupied_spots = sum(1 for spot in lot_spots if spot.status == 'O')
            lot.available_spots = sum(1 for spot in lot_spots if spot.status == 'A')

        return render_template('superUserdashboard.html', user=user, parking_lots=lots, parking_spots=parking_spots)
    

@app.route('/allusers/<uid>', methods=['GET'])
def allusers(uid):
    user = User.query.filter_by(uid=int(uid)).first()
    users = User.query.all()
    if not user.is_superUser:
            flash("⚠️ Access Denied: Only superusers can access this page.")
            return redirect(f"/userdashboard/{uid}") 
    
    return render_template('all_users.html', users=users, user=user)


@app.route('/addlot', methods=['GET', 'POST'])
def addlot():
    user = User.query.filter_by(is_superUser=True).first()  
    if request.method == 'GET':
        return render_template('add_parkinglot.html', user=user)

    if request.method == 'POST':
        uid = user.uid  

        lot_name = request.form.get('lot_name')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        price_per_hour = request.form.get('price_per_hour')
        max_spots = request.form.get('max_spots')

        if float(price_per_hour)<= 0.0 or int(max_spots) <= 0:
            flash("Price per hour and maximum spots are required.")
            return redirect('/addlot')

        # Check for existing lot
        existing_lot = ParkingLot.query.filter_by(lot_name=lot_name, address=address).first()
        if existing_lot:
            flash("Parking lot already exists.")
            return redirect('/addlot')

        # Create the parking lot
        new_lot = ParkingLot(
            lot_name=lot_name,
            address=address,
            pin_code=pin_code,
            price_per_hour=float(price_per_hour),
            max_spots=int(max_spots),
            user_id=uid
        )
        db.session.add(new_lot)
        db.session.commit()

        # Create parking spots for the new lot
        for i in range(1, int(max_spots) + 1):
            new_spot = ParkingSpot(
                lot_id=new_lot.pl_id,
                status='A',
                spot_number=i  
            )
            db.session.add(new_spot)

        db.session.commit()

        flash("Parking lot added successfully.")
        return redirect('/addlot')



@app.route('/editparkinglot/<pl_id>', methods=['GET', 'POST'])
def editparkinglot(pl_id):
    
    if request.method == 'GET':
        user = User.query.filter_by(is_superUser=True).first()  
        plot = ParkingLot.query.filter_by(pl_id=pl_id).first()
        return render_template('edit_parkinglot.html', plot=plot,user=user)
    
    if request.method == 'POST':

        new_lot_name = request.form.get('lot_name')
        new_address = request.form.get('address')
        new_pin_code = request.form.get('pin_code')
        new_price_per_hour = request.form.get('price_per_hour')
        new_max_spots = request.form.get('max_spots')

        plot_update = ParkingLot.query.filter_by(pl_id=pl_id).first()

        plot_update.lot_name = new_lot_name
        plot_update.address = new_address
        plot_update.pin_code = new_pin_code
        plot_update.price_per_hour = float(new_price_per_hour)
        plot_update.max_spots = int(new_max_spots)

        # Update the number of parking spots based on the new max_spots 
        current_spot_count = ParkingSpot.query.filter_by(lot_id=pl_id).count()
        if int(new_max_spots) > current_spot_count:
            max_spot_number = db.session.query(func.max(ParkingSpot.spot_number)).filter_by(lot_id=pl_id).scalar() or 0

            for i in range(1, int(new_max_spots) - current_spot_count + 1):
                new_spot = ParkingSpot(
                    lot_id=pl_id,
                    status='A',
                    spot_number=max_spot_number + i
                )
                db.session.add(new_spot)

        elif int(new_max_spots) < current_spot_count:
            # Remove only available spots starting from the highest spot_number
            removable_spots = ParkingSpot.query.filter_by(lot_id=pl_id, status='A').order_by(ParkingSpot.spot_number.desc()).limit(current_spot_count - int(new_max_spots)).all()

            for spot in removable_spots:
                db.session.delete(spot)

        # Check if lot name is changing and if the new lot name is already taken
        if new_lot_name != plot_update.lot_name:
            if ParkingLot.query.filter_by(lot_name=new_lot_name).first():
                flash("Parking lot with this name already exists.")
                return redirect(f'/editparkinglot/{pl_id}')

        # Check if address is changing and if the new address is already taken
        if new_address != plot_update.address:
            if ParkingLot.query.filter_by(address=new_address).first():
                flash("Parking lot with this address already exists.")
                return redirect('/editparkinglot/'+ str(pl_id))
            
        db.session.commit()
        flash("Parking lot updated successfully.")
        return redirect('/editparkinglot/' + str(pl_id))
    


@app.route('/deleteparkinglot/<pl_id>', methods=['GET'])
def deleteparkinglot(pl_id):
    user = User.query.filter_by(is_superUser=True).first()
    parking_lot = ParkingLot.query.filter_by(pl_id=pl_id).first()

    if not parking_lot:
        flash("Parking lot not found.")
        return redirect('/superUserdashboard/' + str(user.uid)) 

    occupied_spots = ParkingSpot.query.filter(ParkingSpot.lot_id == pl_id, ParkingSpot.status != 'A').count()

    if occupied_spots > 0:
        flash("Cannot delete parking lot. All spots must be available before deletion.")
        return redirect('/superUserdashboard/' + str(user.uid))  

    # If all spots are available, delete the parking lot
    ParkingSpot.query.filter_by(lot_id=pl_id).delete() 
    db.session.delete(parking_lot)
    db.session.commit()

    flash("Parking lot deleted successfully.")
    return redirect('/superUserdashboard/' + str(user.uid)) 


@app.route('/spotdetails/<spot_id>')
def spotdetails(spot_id):
    spot = ParkingSpot.query.filter_by(ps_id=spot_id).first()
    if not spot:
        flash("Parking spot not found.")
        return redirect(f'/superUserdashboard/{users.uid}')

    reservation = Reservation.query.filter_by(spot_id=spot_id).order_by(Reservation.parking_timestamp.desc()).first()
    if not reservation:
        flash("No reservation found for this spot.")
        return redirect(f'/superUserdashboard/{users.uid}')

    user = User.query.filter_by(uid=reservation.user_id).first()
    users = User.query.filter_by(uid=User.uid).first()
    lot = ParkingLot.query.filter_by(pl_id=spot.lot_id).first()

    # Calculate estimated cost if released
    duration_hours = 1
    if reservation.leaving_timestamp:
        duration = reservation.leaving_timestamp - reservation.parking_timestamp
        duration_hours = duration.total_seconds() / 3600
    elif reservation.status.lower() == "active":
        duration = datetime.now() - reservation.parking_timestamp
        duration_hours = duration.total_seconds() / 3600


    rounded_duration = math.ceil(duration_hours)
    est_cost = round(rounded_duration * lot.price_per_hour, 2)

    return render_template("spot_details.html", spot=spot, reservation=reservation, user=user, est_cost=est_cost,users=users,rounded_duration=rounded_duration)

@app.route('/superUsersearch/<uid>', methods=['GET', 'POST'])
def superUsersearch(uid):
    user = User.query.filter_by(uid=int(uid)).first()
    all_pincodes = ParkingLot.query.with_entities(ParkingLot.pin_code).distinct().all()
    results = []
    selected_pincode = None

    if not user.is_superUser:
            flash("⚠️ Access Denied: Only superusers can access this page.")
            return redirect(f"/userdashboard/{uid}") 

    if request.method == 'POST':
        selected_pincode = request.form.get('pincode')

        if selected_pincode:
            parking_lots = ParkingLot.query.filter_by(pin_code=selected_pincode).all()

            for lot in parking_lots:
                available_spots = ParkingSpot.query.filter_by(lot_id=lot.pl_id, status='A').all()
                occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.pl_id, status='O').all()
                results.append({
                    'pl_id': lot.pl_id,
                    'lot_name': lot.lot_name,
                    'available_spot_id': available_spots[0].ps_id if available_spots else None,
                    'lot_address': lot.address,
                    'available_spots': len(available_spots),
                    'occupied_spots': len(occupied_spots)
                })

    return render_template("superUser_search.html", user=user, all_pincodes=all_pincodes, results=results, selected_pincode=selected_pincode)

@app.route('/superUsersummary/<uid>', methods=['GET'])
def superUsersummary(uid):
    user = User.query.filter_by(uid=int(uid)).first()
    parking_lots = ParkingLot.query.all()
    parking_spots = ParkingSpot.query.all()
    reservations = Reservation.query.all()

    if not user.is_superUser:
            flash("⚠️ Access Denied: Only superusers can access this page.")
            return redirect(f"/userdashboard/{uid}") 
    
    # --- Chart 1: Parking Spot Availability ---
    
    available_spots = len([ps for ps in parking_spots if ps.status == 'A'])
    occupied_spots = len([ps for ps in parking_spots if ps.status == 'O'])
    
    # Data for the pie chart
    labels = ['Available', 'Occupied']
    sizes = [available_spots, occupied_spots]
    colors = ['skyblue', 'lightcoral']  # Colors for the pie chart

    fig1, ax1 = plt.subplots()

    explode = (0.1, 0)  # "explode" the first slice (Available spots
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, explode=explode, shadow=True)
    ax1.set_title("Parking Spot Availability")

    plot_path_1 = "static/spot_availability_pie.png"
    fig1.tight_layout()
    fig1.savefig(plot_path_1)
    plt.close(fig1)

    # --- Chart 2: Parking Reservations Over Time ---

    reservation_times = [r.parking_timestamp.strftime('%Y-%m-%d') for r in reservations]# This line creates a list of dates (as strings) from all the reservation timestamps.
    unique_dates = list(set(reservation_times))# Get unique dates from reservation timestamps
    reservations_per_day = [reservation_times.count(date) for date in unique_dates]# Count reservations for each unique date

    fig2, ax2 = plt.subplots()
    ax2.plot(unique_dates, reservations_per_day, marker='o', color='green')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Reservations Count')
    ax2.set_title('Parking Reservations Over Time')

    plot_path_2 = "static/reservations_over_time.png"
    fig2.savefig(plot_path_2)
    plt.close(fig2)

    # --- Chart 3: Revenue collected from each Parking Lot over time ---

    # Step 1: Create a dictionary to hold revenue totals per lot
    lot_revenue = {}

    for res in reservations:
        if res.spot and res.spot.parking_lot and res.parking_cost:
            lot_name = res.spot.parking_lot.lot_name
            if lot_name in lot_revenue:
                lot_revenue[lot_name] += res.parking_cost # Add to existing revenue
            else:
                lot_revenue[lot_name] = res.parking_cost # create new entry

    # Step 2: Prepare data for chart
    lot_names = list(lot_revenue.keys())
    revenues = list(lot_revenue.values())

    # Step 3: Create bar chart
    fig3, ax3 = plt.subplots()
    ax3.bar(lot_names, revenues, color='purple', edgecolor='black', width=0.4)
    ax3.set_xlabel('Parking Lot')
    ax3.set_ylabel('Total Revenue Collected (₹)')
    ax3.set_title('Total Revenue from Each Parking Lot')

    plot_path_3 = "static/revenue_per_lot.png"
    fig3.tight_layout()
    fig3.savefig(plot_path_3)
    plt.close(fig3)

    # Render the template and pass chart image paths
    return render_template("superUser_summary.html", user=user, parking_lots=parking_lots, parking_spots=parking_spots, reservations=reservations, plot_path_1=plot_path_1, plot_path_2=plot_path_2, plot_path_3=plot_path_3)


# -------------------------------------------------------
def create_admin():
    existing_admin = User.query.filter_by(is_superUser=True).first()
    if not existing_admin:
        admin = User(
            username='admin@parkease.com',
            password='Admin@2025',
            name='Admin ParkEase',
            phone='9876543210',
            address='101 Admin Plaza, Bhubaneswar',
            pincode='751001',
            is_superUser=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully.")
    else:
        print("ℹ️ Admin user already exists.")



if __name__ == '__main__':
    create_admin()  # Create admin if it doesn't exist
    app.run(debug=True)
