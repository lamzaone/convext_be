# Dev Branch

## TODO


## Basic build/install for Debian:
- Download and install python3 and all other dependencies if missing
        
        sudo apt install python3 python3-pip python3-virtualenv \
        python3-psycopg2 python3-dev libpq-dev

- Create a virtual environment
        
        python3 -m venv venv

        source venv/bin/activate

- Install the rest of Python3 requirements with pip:
        
        pip install -r requirements.txt

- Install PostgreSQL and start PostgreSQL

        sudo apt install postgresql postgresql-contrib

        sudo systemctl start postgresql

        sudo systemctl enable postgresql

- Setup PostgreSQL user and database
        
        sudo -u postgres psql

    If it returns an error try:
        
        sudo -u postgres psql template1

    Once you get the progress prompt (=#), 
    change user pass and create database `convext`. 
    Type:
        
        ALTER USER postgres PASSWORD 'pass';

        CREATE DATABASE convext;

        \q

- Start server
        
        fastapi run --reload

    or

        uvicorn main:app --reload
