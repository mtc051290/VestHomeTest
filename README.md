
# Vest | Backend Engineer - Take Home Test

Miguel Jesús Torres Cárdenas - 
_Digital Systems and Robotics Engineer_ 

<br />

API developed with FastAPI, MySQL and authentication tools for a trading application.



For this challenge I have decided to take the many advantages of FastAPI, which is a modern, high-performance web framework, to develop an API service for a virtual trading environment where a user can buy/sell stocks, hold stocks and track portfolio performance.

This project focuses on the processing of customer requests, their response and the acquisition of data from the official Nasdaq API; for now, no payment or collection processes are managed.
## 🚀 Challenges
The main challenge in this test was to create the ability to buy and sell large amounts of shares and make the relevant calculations as fast as possible.

Another great challenge was obtaining the Nasdaq endpoints, since since October 2021 the API changed and authentication is required to be able to make requests.

At the beginning, it was planned to create cron jobs to communicate continuously to the Nasdaq API, however the problem was solved in another way and without compromising application resources, it is still recommended to develop this type of systems as microservices.

## Links

[API Documentation](https://vest-backend-test.herokuapp.com/redoc)

This Document details the characteristics of the endpoints, their operation and the requirements to make requests.

Nasdaq API blocks Heroku requests and unprotected AWS EC2 instances, so the project was uploaded to Heroku in order to show documentation.


## Features

- JWT Tokens
- OAuth2 Authentication
- Buy shares
- Sell shares
- Handling large numbers of transactions
- Get profit/gain from historical operations
- Get held shares
- Get the current value of a stock
- Double check of highest, lowest and average price
- Get historic price of a stock in 1-hour intervals

## Tech Stack

**Client:** Swagger, PostMan

**Server:** Python, FastAPI, SQLAlchemy

**Database:** MySQL hosted in Heroku

**Package installer** PIP - PyPI


## Run Locally

Clone the project

```bash
  git clone https://github.com/mtc051290/VestHomeTest.git
```

Go to the project directory

```bash
  cd VestTestApp
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Start the server

```bash
  uvicorn main:app --reload
```


Manual Installation

```bash
  pip3 install fastapi[all]
  python3 -m pip install PyMySQL
  pip install sqlalchemy
  pip install "passlib[bcrypt]"
  pip install "python-jose[cryptography]"
  pip install yfinance
  pip install pandas
  pip install requests
  pip3 install pyyaml
  pip3 install yaml
  pip install bcrypt
```

Open http://localhost:8000/docs on your browser

## Scope of the project

- Build a threaded microservice to listen price changes in real time from different sources
- Integrate a load balancer for faster calculations without compromising server performance
- Implement unit test to guarantee the correct functioning of the system
- More and more calculations 🚀 

## Contact

**Email:** mtc590@gmail.com

**Phone:** +52 55 39 11 54 81