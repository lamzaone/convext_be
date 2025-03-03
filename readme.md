# Dev Branch

## TODO

- ~~Multiple files upload support~~
- ~~Find async way to make ZIP files~~
- Find a way to send labels from convert.sh instead of extensions and yet find
  the extension of the converted file, so you can check the filename.
- Add more formats for conversion
- ~~Start working on database/accounts/mini-cloud~~
- ~~Rewrite upload endpoint~~
- Write file deletion endpoint for logged in user
- Check for disk usage by usage and block new uploads if not enought space
  left(?)

## Basic build/install for Debian:
- Download and install python3 and all other dependencies if missing
        
        sudo apt install python3 python3-pip python3-virtualenv python3-venv \
        python3-psycopg2 python3-dev libpq-dev

- Download and install all auxiliary programs

        sudo apt install ffmpeg libreoffice imagemagick ghostscript \
        default-jre libreoffice-java-common unrar p7zip-full \
        tar gzip unzip rar pdftohtml

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

    Multi-thread:

        fastapi run --workers $(nproc)

    or

        uvicorn main:app --reload

    Multi-thread:

        uvicorn main:app --workers $(nproc)
