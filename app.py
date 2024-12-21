import pickle
from flask import Flask, redirect, request, url_for, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import numpy as np
import pandas as pd
import joblib
app = Flask(__name__)
scalar=joblib.load(open('scaler.joblib','rb'))

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Trupti%4030@localhost:3306/diabetes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Add Flask-Migrate initialization here
bcrypt = Bcrypt(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.String(100), nullable=False)
    suggestion = db.Column(db.String(100), nullable=False)
    rating=db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    fname = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(10), nullable=False)
    blood = db.Column(db.String(5), nullable=False)
    illness = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# Load the scaler (assuming it has been saved earlier after fitting it on the training data)
with open('diabetes_model.joblib', 'rb') as f:
    model = joblib.load(f)
    
@app.route('/calculate', methods=['POST'])
def cal():
    if 'user_id' not in session:
        
        flash("You need to log in first!", 'danger')
        return redirect(url_for('login'))

    try:
        # Convert form values to floats and handle non-numeric values
        data = []
        for key, value in request.form.items():
            if key == 'terms_checkbox':  # Handle checkbox separately
                if value != 'on':  # If the checkbox is not checked, skip
                    flash("You need to accept the terms and conditions.", 'danger')
                    return redirect(url_for('predict'))  # Redirect back to the prediction form
            else:
                try:
                    data.append(float(value))
                except ValueError:
                    # If a non-numeric value is found, log an error or handle it accordingly
                    print(f"Non-numeric value encountered: {value}")
                    flash("Please enter valid numeric values.", 'danger')
                    return redirect(url_for('predict'))  # Redirect back to the prediction form

        print("Input Data:", data)

        # Transform the input using the loaded scaler
        final_input = scalar.transform(np.array(data).reshape(1, -1))
        print("Transformed Input:", final_input)

        # Predict using the model
        prediction = model.predict(final_input)[0]
        print("Prediction:", prediction)
        probabilities = model.predict_proba(final_input)
        confidence = max(probabilities[0])
        conf_per = round(confidence * 100)

        # Flash appropriate message
        if prediction == 0:
            flash(f"No Diabetes: confidence/accuracy of prediction: {conf_per}%", 'success')
        else:
            flash(f"Diabetes: confidence/accuracy of prediction: {conf_per}%", 'danger')

    except Exception as e:
        # Log the error and flash a generic error message
        print("Error during prediction:", e)
        flash("An error occurred while processing your request.", 'danger')

    # Render the prediction page
    return render_template('predict.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        fname = request.form['fname']
        contact = request.form['contact']
        blood = request.form['blood']
        illness = request.form['illness']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(username=username, fname=fname, contact=contact, blood=blood, illness=illness, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/predict')
def predict():   
    return render_template('predict.html')


@app.route('/terms & conditions')
def terms():   
    return render_template('terms.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        feedback = request.form['feedback']
        suggestion = request.form['suggestion']
        rating = int(request.form['rating'])

        new_feedback = Feedback(name=name, contact=contact, feedback=feedback, email=email, suggestion=suggestion, rating=rating)
        db.session.add(new_feedback)
        db.session.commit()  # Commit the new feedback entry to the database
        
        return redirect(url_for('feedbackdata'))  # Redirect to the feedback data page
    
    return render_template('feedback.html')

@app.route('/feedback_data')
def feedbackdata():
    feedback_list = Feedback.query.all()  # Fetch all feedback data from the database
    if feedback_list:
        return render_template('feedback_data.html', feedback=feedback_list)
    else:
        return render_template('feedback_data.html', feedback=None)  # No data available case

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('predict'))
        else:
            flash("Invalid credentials. Please try again.")  # Flash message for failed login
    
    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login_page')
def calllogin():
    return render_template('login.html')

@app.route('/contactus')
def contact():
    return render_template('contact.html')

@app.route('/signup_data_record', methods=['GET', 'POST'])
def cxdata():
    if request.method == 'POST':
        username = request.form['username']
        fname = request.form['fname']
        contact = request.form['contact']
        blood = request.form['blood']
        illness = request.form['illness']
        email = request.form['email']

        # Pass data to the template for rendering
        return render_template('login_data.html', users=[{'username': username, 'fname': fname, 'contact': contact, 'blood': blood, 'illness': illness, 'email': email}])

    # For GET requests, fetch data from the database and display it
    users = User.query.all()
    if users:
        return render_template('login_data.html', users=users)
    else:
        return "No data available. Please submit the signup form first."

@app.route('/admin_home_page')
def admin_homepage():
    return render_template('admin_home_page.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch admin credentials from the database
        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            return redirect(url_for('admin_homepage'))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template('admin.html')

@app.route('/admin_login')
def call_admin():
    return render_template('admin.html')

@app.route('/')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)
