Local Development Server
========================

Deployment
==========

This section covers deployment of Parmesan on an Ubuntu server using Nginx. This
is only provided as an example, since many other configurations are available.
Tutorials for configuring Django web apps for a variety of server configurations
can be found online. It is also possible to create a simple, temporary, local
deployment as described above. 

Package Installation
--------------------

Begin by installing the following necessary packages.

```
sudo apt update
sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl
```

Postgres Setup
--------------

This step sets up the Postgresql database and users for Parmesan. Of course, you
can use a different database, but the process may be somewhat different.

```
sudo -u postgres psql
```

This will log you in to the interactive Postgres shell. The following commands
are entered in the shell, not in the Linux command-line.

```
CREATE DATABASE parmesan;
CREATE USER django WITH PASSWORD 'password';
```

Change the password to something secure, of course.

```
ALTER ROLE django SET client_encoding TO 'utf8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE parmesan TO django;
ALTER DATABASE parmesan OWNER TO django;
\q
```

Environment Setup
-----------------

This creates a sandboxed Python environment, so you can run Django without
contaminating the system installation of Python. 

I generally recommend running this command a level _above_ the Parmesan git
repository, to avoid confusing git with new files.

```
python3 -m venv parmesan_env
. parmesan_env/bin/activate
pip install -r parmesan/requirements.txt
```

Next, create a file above the project with the following contents, named
`.variables`. You will need to create and set your own secret key and postgres
password. 

```
export WEB_PRODUCTION=true
export PARMESAN_SECRET_KEY=
export DJANGO_POSTGRES_PASS=
```

For now, run the following to enable these environment variables.

```
source .variables
```

You will also need to create a copy of this file, called `.environment`, with
the `export` keyword removed.

Django Setup
------------

Perform database migrations, create the superuser, and collect staticfiles for
deployment.

```
parmesan/manage.py makemigrations
parmesan/manage.py migrate
parmesan/manage.py createsuperuser
parmesan/manage.py collectstatic
```

Firewall Setup and Initial Testing
----------------------------------

```
sudo ufw allow 8000
```

At this point, the site should more or less function:

```
parmesan/manage.py runserver 0.0.0.0:8000
``` 

However, this is just the development server and isn't intended for production.

Gunicorn Setup
--------------

Copy the server configuration files to the appropriate locations on your server.

```
sudo cp parmesan/server/parmesan.socket /etc/systemd/system/parmesan.socket
sudo cp parmesan/server/parmesan.service /etc/systemd/system/parmesan.service
sudo systemctl start parmesan.socket
sudo systemctl enable parmesan.socket
```

Nginx Setup
-----------

```
sudo cp parmesan/server/parmesan /etc/nginx/sites-available/.
sudo ln -s /etc/nginx/sites-available/parmesan /etc/nginx/sites-enabled/.
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'
```
