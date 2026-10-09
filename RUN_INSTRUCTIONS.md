# How to Run the Fusion Repository

Follow these steps to activate the virtual environment, install dependencies, and start the development server.

## 1. Activate the Virtual Environment

Before running any commands, you must activate the virtual environment. From the root of the repository (`/home/parth/Documents/Fusion/Fusion`), run:

```bash
source .venv/bin/activate
```

*(Note: Once activated, your terminal prompt will usually be prefixed with `(.venv)`.)*

## 2. Install Dependencies (If not already installed)

If you haven't installed the dependencies yet, you can do so by running:

```bash
pip install -r requirements.txt
```

## 3. Run Database Migrations

Before starting the server, ensure your database is up to date with the latest schema changes. Make sure to specify the development settings module:

```bash
cd FusionIIIT
DJANGO_SETTINGS_MODULE=Fusion.settings.development python manage.py migrate --run-syncdb
```

## 4. Start the Development Server

To start the Django development server on port 8000, run the following command from inside the `FusionIIIT` directory:

```bash
DJANGO_SETTINGS_MODULE=Fusion.settings.development python manage.py runserver 0.0.0.0:8000
```

The server will be available at [http://localhost:8000/](http://localhost:8000/).

To stop the server, press `Ctrl + C` in your terminal. You can deactivate the virtual environment anytime by running `deactivate`.
