VEHICLE PARKEASE 
------------------

**About The Project:**


  This Project is made by Vaishnabi Ghose, for Modern Application Devlopment 1 course prject.
  
  Main theme of this project is to make a multi-user app which requires mutiple users that has to login/register themselves and a superuser that get added whenever a new database is created.


  **SUPERUSER:**
  
  
  Superuser can create/delete(only when all the spots are available i.e., empty)/veiw/edit a parking lot.
  
  Superuser can view the status of parking spot and check the parked vehicle details If the parking spot status is occupied.
  
  Superuser can veiw all registered users including himself.
  
  Superuser can search parking lots by pin-code to make it easier for their accessibiliy.
  
  Superuser can view the summary charts like Parking Spot Availability, Parking Reservations and Revenue collected from each parking lot over time.
  
  Default superuser credentials emailID = admin@parkease.com and password = Admin@2025.


  **USER:**

  
  User can choose an available parking lot and allocation is done as per the first available parking spot.
  
  User can change the status of the parking spot to occupied/released, once the vehicle is parked/moved out of the parking.
  
  User can see the reservation details brfore releasing a parking spot.
  
  User can view the summary charts like Reservation History Over Time, Revenue Spent by User in Each Parking Lot, Total Active Reservations Count, Parking Durations of vehicle parked out


**Technologies Used:**


  Python – Used for writing all backend logic.

  Flask – A web framework used to handle routing and server-side functionality.
  
  SQLite – A lightweight, file-based database used to store user info, reservations, parking lots, etc.
  
  SQLAlchemy – ORM (Object Relational Mapper) used to interact with the SQLite database using Python classes.
  
  Flask-Migrate  - flask migration is used so that we can add new columns to the existing database without losing data or create new tables without losing data
  
  HTML with Jinja2 – Used for creating dynamic web pages with server-rendered data.
  
  Matplotlib – Used to generate visual charts like bar graphs, pie charts, and histograms for analytics.
  
  VS Code – The code editor used for writing and managing the project files.


**How to run:**


  Set the root folder such that it includes the main project files like app.py, requirements.txt, and folders like templates and static.

  Create a virtual environment by running the command:
  python -m venv ANY_NAME_OF_VIRTUAL_ENVIRONMENT
  
  Activate the environment using:
  On Windows:
  ANY_NAME_OF_VIRTUAL_ENVIRONMENT\Scripts\activate
  
  On Mac/Linux:
  source ANY_NAME_OF_VIRTUAL_ENVIRONMENT/bin/activate
  
  Prerequisites:
  Python installed on your system
  Packages listed in requirements.txt
  
  Installation:
  After activating the virtual environment, run the following command to install all required packages: pip install -r requirements.txt

**Project link:** https://github.com/23f3001025/vehicle-parkEase
