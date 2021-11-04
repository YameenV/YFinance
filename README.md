
# [![3 Pyhton](https://img.shields.io/badge/Pyhton-3-yellow)]() [![3 Pyhton](https://img.shields.io/badge/Sqlite-3-brightgreen)]() [![3 Pyhton](https://img.shields.io/badge/Flask-2-blue)]()
# YFinance
Its a Platform where you can manage selling, buying, and checking stock prices

## Features

- Buy stocks
- Sell stocks
- Lookup stocks

# Dashboard Page
![alt dashboard](Imagesfinance/Dashboard.png)

# Buy Page
![alt dashboard](Imagesfinance/buy.png)

# Sell Page
![alt dashboard](Imagesfinance/sell.png)

# History Page
![alt dashboard](Imagesfinance/history.png)

## Deployment

To Install all the Dependencies required for the Project

```bash
  pip install -r requirements.txt
```

To get the Api Key

Visit iexcloud.io/cloud-login#/register/.

Select the “Individual” account type, then enter your email address and a password, and click “Create account”.

Once registered, scroll down to “Get started for free” and click “Select Start” to choose the free plan.

Once you’ve confirmed your account via a confirmation email, visit https://iexcloud.io/console/tokens.

Copy the key that appears under the Token column (it should begin with pk_).

To deploy this project run

```bash
  export API_KEY=value
```

Run the Project

```bash
  flask run
```