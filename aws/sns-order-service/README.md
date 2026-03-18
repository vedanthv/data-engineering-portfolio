# Order Notification System using Next.js and AWS SNS

A simple event-driven application where users place an order from a web UI and a notification is sent using Amazon SNS.

This project demonstrates how frontend applications can trigger AWS messaging services using a lightweight API layer.

---

## Architecture

```
Browser (User)
      │
      ▼
Next.js UI
      │
      ▼
Next.js API Route
      │
      ▼
Amazon SNS Topic
      │
      ▼
Email Notification
```

Event Flow:

1. User selects product and quantity.
2. User clicks **Place Order**.
3. Next.js API endpoint publishes message to SNS.
4. SNS delivers notification to subscribed email.

---

## Tech Stack

Frontend
Next.js

Backend
Next.js API Routes

Cloud Services
Amazon SNS
Amazon EC2
AWS IAM

SDK
AWS SDK v3

---

## Project Structure

```
order-sns-app
│
├── app
│   ├── page.js
│   │
│   └── api
│       └── order
│           └── route.js
│
├── .env.local
├── package.json
└── README.md
```

---

## Features

Simple order UI

Server-side API endpoint

SNS event publishing

Email notifications

Secure IAM role authentication

Deployed on EC2

---

## Setup Instructions

### 1 Create SNS Topic

Open AWS Console

Navigate to SNS

Create Topic

Type: Standard

Name:

```
order-topic
```

Copy the Topic ARN.

Example:

```
arn:aws:sns:us-east-1:123456789012:order-topic
```

---

### 2 Create Email Subscription

Inside SNS topic:

Create subscription

Protocol:

```
Email
```

Endpoint:

```
your-email@example.com
```

Confirm the subscription via email.

---

### 3 Launch EC2 Instance

Recommended settings:

AMI: Ubuntu

Instance type:

```
t2.micro
```

Open ports:

```
22 (SSH)
3000 (Application)
```

---

### 4 Attach IAM Role

Create IAM role with permissions:

```
sns:Publish
```

Attach role to EC2 instance.

This allows the application to publish messages without storing AWS credentials.

---

### 5 Install Node.js

Connect to EC2

```
ssh -i key.pem ubuntu@EC2_PUBLIC_IP
```

Install Node using NVM

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
```

Install Node 20

```
nvm install 20
nvm use 20
```

Verify

```
node -v
```

---

### 6 Clone Repository

```
git clone <repo-url>
cd order-sns-app
```

Install dependencies

```
npm install
```

---

### 7 Configure Environment Variables

Create file:

```
.env.local
```

Add:

```
AWS_REGION=us-east-1
SNS_TOPIC_ARN=your-topic-arn
```

---

### 8 Run Application

Development

```
npm run dev
```

Production

```
npm run build
npm start
```

Application URL

```
http://EC2_PUBLIC_IP:3000
```

---

## Example API Code

```
app/api/order/route.js
```

```javascript
import { SNSClient, PublishCommand } from "@aws-sdk/client-sns";

const sns = new SNSClient({
  region: process.env.AWS_REGION
});

export async function POST(req) {

  const body = await req.json();

  const params = {
    TopicArn: process.env.SNS_TOPIC_ARN,
    Message: `Order received: ${body.product} x ${body.quantity}`,
    Subject: "New Order"
  };

  await sns.send(new PublishCommand(params));

  return Response.json({
    message: "Order successfully placed!"
  });

}
```

---

## Example Notification

Email received from SNS:

```
Subject: New Order

Order received: Pizza x 2
```

---

## Future Enhancements

Add SQS queue for message buffering

Store orders in DynamoDB

Add order history dashboard

Add push notifications

Implement event-driven order processing pipeline

Example scalable architecture:

```
Next.js UI
     │
     ▼
SNS Topic
     │
     ▼
SQS Queue
     │
     ▼
Lambda
     │
     ▼
DynamoDB
```

---