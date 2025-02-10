# WebServer

## Usage
### Local Deployment
1. Install the dependencies
```sh
npm install
```
2. Ensure you have PostgreSQL installed on your machine
3. Create a file called .env with your PostgreSQL connnection string, like so:
```
DATABASE_URL="postgres://user:password@localhost:5432/database_name"
```
4. Run
```sh
npm start
```
### Heroku Deployment (from scratch)
Note: The [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) is required

1. Clone this GitHub repository
```sh
git clone https://github.com/scrapedau/WebServer.git
```
2. Add Heroku as a remote
```
heroku git:remote -a scraped-web-server
```
3. Run this command to get the PostgreSQL connection string
```
heroku config
```
4. Copy the value for DATABASE_URL, and create a new file called `.env`, and fill it as follows
```
DATABASE_URL="the value you copied"
```
5. If you have made any changes to the code, commit them and push them to Heroku
```
git push heroku main
```
6. Your code should be deployed now