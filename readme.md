# Dev Branch

# Basic install for Debian Unstable:
- Download and install python3 and all other dependencies if missing
`sudo apt install python3 python3-pip python3-virtualenv python3-psycopg2`
`python3-dev libpq-dev`
- Create a virtual environment
`python3 -m venv venv`
`source venv/bin/activate`
- Install the rest of Python3 requirements with pip:
`pip install -r requirements.txt`
- Install PostgreSQL and start PostgreSQL
`sudo apt install postgresql  postgresql-contrib`
`sudo systemctl start postgresql`
`sudo systemctl enable postgresql`
- Create a database called "convext"
- Start server
``
