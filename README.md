# BinanceXchange

## About

A cryptocurrency exchange platform for trading various digital assets.

## Author

Demchyshyn Volodymyr

- Email: valdemarmalyna@gmail.com
- Telegram: https://t.me/dem_volodya
- Project on Azure: demchyshynuniversitybinance-production-25de.up.railway.app

## Getting Started:

To run the project, follow next steps:

1. Clone the repository: git clone
2. Install dependencies: pip install -r requirements.txt
3. Run the development server: python manage.py runserver

## Running with Docker

This project supports running with Docker and Docker Compose, including a PostgreSQL database.

### Quick Start

1. Build and start the containers:
   ```sh
   docker-compose up --build
   ```
2. Apply migrations and create a superuser (if needed):
   ```sh
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```
3. Access the app at [http://localhost:8000](http://localhost:8000)

### Data Migration from SQLite (optional)
If you are migrating from SQLite, you can use Django's `dumpdata` and `loaddata` commands:
```sh
python manage.py dumpdata > data.json
# After switching to PostgreSQL
python manage.py loaddata data.json
```


## SonarQube Code Analysis

SonarQube is used for code quality and coverage analysis. You can run SonarQube locally with Docker Compose:

1. Start SonarQube:
   ```sh
   docker-compose up -d sonarqube
   ```
2. Access SonarQube at [http://localhost:9000](http://localhost:9000) (default login: admin / admin).
3. Run the scanner (update SONAR_TOKEN in your .env or pass as env variable):
   ```sh
   docker-compose run --rm sonar-scanner
   ```
4. View results in the SonarQube web UI.

See `sonar-project.properties` for configuration details.

## CI/CD (Continuous Integration / Continuous Deployment)

Для автоматизації тестування, перевірки якості коду та деплою ви можете використовувати GitHub Actions, GitLab CI, Azure Pipelines або інші CI/CD сервіси.

### Приклад для GitHub Actions

Створіть файл `.github/workflows/django.yml` з таким вмістом:

```yaml
name: Django CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
          POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DJANGO_SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY }}
      DJANGO_DEBUG: False
      DJANGO_ALLOWED_HOSTS: 127.0.0.1
      DJANGO_DB_NAME: ${{ secrets.POSTGRES_DB }}
      DJANGO_DB_USER: ${{ secrets.POSTGRES_USER }}
      DJANGO_DB_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
      DJANGO_DB_HOST: localhost
      DJANGO_DB_PORT: 5432

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run migrations
      run: python manage.py migrate

    - name: Run tests
      run: coverage run manage.py test

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: true
```

### Що це дає:
- **Автоматичний запуск тестів** при кожному пуші/PR у main.
- **Перевірка міграцій** та бази даних PostgreSQL.
- **Збір та завантаження coverage** (можна підключити до SonarQube або Codecov).
- **Можливість додати деплой** (наприклад, на Azure, Heroku, Docker Hub тощо).

Докладніше: [GitHub Actions Documentation](https://docs.github.com/en/actions)

> **Note:** Set the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):
> - `DJANGO_SECRET_KEY`
> - `POSTGRES_DB`
> - `POSTGRES_USER`
> - `POSTGRES_PASSWORD`

## Example .env file

Create a `.env` file in the project root with the following content (update secrets as needed):

```
DJANGO_SECRET_KEY
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_USE_TLS=True
OPEN_API
DJANGO_DB_NAME
DJANGO_DB_USER
DJANGO_DB_PASSWORD
DJANGO_DB_HOST
DJANGO_DB_PORT
```

## Documentation

### Introduction

Very simple interface and very easy to use crypto exchange.

### Features

- User Authentication with Google account.
- Coming soon.

### Architecture

The cryptocurrency exchange app follows a client-server architecture. The client-side is built using HTML, CSS, JS and
Jinja, while the server-side is implemented with Django.

### Database schema 
![Database.jpg](Database.jpg "Database") 

### Usage

Trading and exchange of both crypto and fiat currencies

## Project Task Decomposition

Week 1 :️

- Implement feature: User Registration with Google Account✔️
- Setup Azure environment✔️
- Create initial project structure✔️
- Define database schema✔️
- Write unit tests for user registration functionality✔️

️
Week 2:

- Implement feature: Trading Dashboard✔️
- Develop user interface for dashboard components✔️
- Integrate real-time market data APIs✔️
- Implement basic trading functionalities✔️
- Conduct initial performance testing✔️

Week 3:

- Implement feature: Wallet Management ✔️
- Design wallet interface for managing balances and transactions ✔️
- Implement cryptocurrency wallet functionalities ✔️
- Integrate transaction processing system ✔️
- Conduct security review of wallet management features ✔️

Week 4:

- Implement feature: Market Analysis Tools✔️
- Integrate advanced charting libraries✔️
- Implement technical analysis indicators✔️
- Develop market analysis features such as price alerts and trend analysis✔️
- Conduct usability testing for market analysis tools(UI/UX)✔️

Week 5:

- Implement feature: Order Management✔️
- Develop order placement and tracking system✔️
- Implement order book functionality✔️
- Integrate order execution mechanisms
- Conduct end-to-end testing of order management system

Week 6:

- Implement feature: Notification System✔️
- Develop notification infrastructure✔️
- Implement email and in-platform notifications
- Integrate notification triggers with user actions✔️
- Conduct load testing for notification delivery system

Week 7:

- Implement feature: Profile Customization✔️
- Develop user profile settings interface✔️
- Implement customization options for user preferences✔️
- Integrate profile settings with user database✔️
- Conduct user acceptance testing for profile customization features✔️

Week 8:

- Implement feature: Transaction History✔️
- Design transaction history interface
- Implement transaction logging system✔️
- Develop search and filtering functionalities✔️
- Conduct security audit of transaction history system

Week 9:

- Implement feature: Support Center✔️
- Develop FAQ section and knowledge base✔️
- Implement contact options for user support✔️
- Integrate support ticketing system✔️
- Conduct usability testing for support center features✔️

Week 10:

- Implement feature: Referral Program✔️
- Design referral program structure and rewards system✔️
- Develop referral tracking mechanisms✔️
- Implement referral invitation features✔️
- Conduct testing and validation of referral program functionality✔️

Week 11:

- Implement feature: Security Features✔️
- Enhance security with two-factor authentication✔️
- Implement account recovery mechanisms ✔️
- Conduct security testing and vulnerability assessment✔️
- Develop user education materials on security best practices(FAQ)✔️

Week 12:

- Implement feature: Performance Optimization
- Identify and address performance bottlenecks
- Optimize database queries and server-side processes
- Implement caching strategies for improved speed
- Conduct final round of performance testing and optimization
