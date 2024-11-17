## Part 2 : Serving the Postgres data via FastAPI Backend

Checkout the previous [part](https://github.com/vedanthv/data-engineering-portfolio/tree/main/cricket-livescores-ingestion-kafka-airflow) if you haven't!

In the previous part I setup a streaming service with Kafka [Zookeeper and Broker] powered by KRaft to ingest some live cricket match statistics.

But having data dumped in some remote Postgres DB is of no use to end users. 

So I decided to build a simple but powerful backend using FastAPI.

### About FastAPI

FastAPI is a Python framework for building APIs quickly and easily. It’s fast and uses Python’s type hints to automatically check and validate data. It also creates interactive documentation for your API, so you can test it directly in your browser. 

FastAPI supports modern features like asynchronous programming, making it great for handling lots of users at the same time. It’s simple to use, but powerful enough for big projects, helping you write clean and efficient code while focusing on building your app instead of worrying about setup and details.

### Installation

1. Install via pip [Basic Installation]

Note : You can run applications with this.

```
pip install fastapi
```

2. Another package to run applications

```
pip install fastapi[all]
```

3. Running app

Now to run the app

```
fastapi run main.py
```

You should be able to get the Swagger UI docs for your API framework by going to the URL

```
localhost:8000/docs
```

OR if on EC2 instance

```
[ec2_ip_url]:8000
```

### Endpoints that I defined

I have defined 3 basic endpoints for now. All of them are GET requests.

These are : 

- ```ipl-all``` : details from the Postgres DB from the table ipl_livescores.

- ```players``` : details from the table players.

- ```countries``` : details from the table countries.

- ```team-results``` : Results of a particular team like "RCB". Eg : **0.0.0.0:8000/team-results?Royal%Challengers%Bangalore**

### Swagger UI

![image](https://github.com/user-attachments/assets/994099fb-33ad-4da6-964b-4447d29a3493)

In an upcoming part I will be covering some POST request examples as well [mostly to capture API metrics].

For the complete code check ```main.py``` file. I wouldn't be explaining it here but feel free to reach out on Linkedin for any queries.

Each class is a mapped schema for the tables and the functions are asynchronous in nature.

Async functions allow multiple requests to be processed simultaneously without blocking. For example, while one request waits for a database response, another can be processed.

Async programming is ideal for applications that need to serve a high number of concurrent users or make multiple network or database calls per request.

In this line where the URL is defined,

```bash
DATABASE_URL = "postgresql+asyncpg://[your_username]:[your_password]@[your_postgres_hostip]/cricket"
```

The username and password would be the name that is used to login to the server.

Host Name \ IP : the Host IP of the docker container running postgres. 
      [we can find out using ```docker inspect <container_id>]

Check out the previous part for more details...
