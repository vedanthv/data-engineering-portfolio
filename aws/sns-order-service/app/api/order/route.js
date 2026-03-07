import { SNSClient, PublishCommand } from "@aws-sdk/client-sns";

const sns = new SNSClient({
  region: process.env.AWS_REGION
});

export async function POST(req) {

  const body = await req.json();

  const message = `
New Order Received

Product: ${body.product}
Quantity: ${body.quantity}
Time: ${new Date().toISOString()}
`;

  const params = {
    TopicArn: process.env.SNS_TOPIC_ARN,
    Message: message,
    Subject: "New Order"
  };

  await sns.send(new PublishCommand(params));

  return Response.json({
    message: "Order successfully placed!"
  });

}