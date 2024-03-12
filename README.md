My API
Instructions for Running Locally
Installation
Clone this repository to your local machine:

git clone https://github.com/Zonda001/AirportAPI.git
Navigate to the project directory:

cd AirportAPI
Install dependencies using pip:

pip install -r requirements.txt

Features
User management: Create, update, and view user profiles.
Authentication: Obtain authentication tokens for users.
User registration: Create new user accounts.
Filtering: Filter routes, airplanes, flights, etc., by various parameters like source, destination, departure time, etc.

Accessing the API

Register a new user using the /api/user/create/ endpoint.
Obtain an authentication token by sending a POST request to the /api/token/ endpoint with your email and password.
Use the obtained token in the authorization header for accessing protected endpoints.
Explore various endpoints like /api/routes/, /api/airplanes/, /api/flights/, etc., for different functionalities provided by the API.

Superuser

email:aboba@gmail.com
password:aboba
