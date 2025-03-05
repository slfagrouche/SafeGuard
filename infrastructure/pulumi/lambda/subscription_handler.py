import json
import urllib3
import boto3
import os

def handler(event, context):
    # If this is a subscription confirmation
    if event['Type'] == 'SubscriptionConfirmation':
        http = urllib3.PoolManager()
        
        # Get the subscription confirmation URL
        subscribe_url = event['SubscribeURL']
        
        # Visit the URL to confirm subscription
        response = http.request('GET', subscribe_url)
        
        if response.status == 200:
            # Get the subscription ARN from the response
            subscription_arn = json.loads(response.data.decode('utf-8'))['SubscriptionArn']
            
            # Update DynamoDB with confirmed status
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(os.environ['DYNAMODB_SUBSCRIBERS_TABLE'])
            
            # Extract email from message
            message = json.loads(event['Message'])
            email = message.get('email')
            
            if email:
                table.update_item(
                    Key={'email': email},
                    UpdateExpression='SET subscription_status = :status, subscription_arn = :arn',
                    ExpressionAttributeValues={
                        ':status': 'CONFIRMED',
                        ':arn': subscription_arn
                    }
                )
            
            return {
                'statusCode': 200,
                'body': json.dumps('Subscription confirmed')
            }
    
    # For actual notifications
    elif event['Type'] == 'Notification':
        # Process the notification
        message = json.loads(event['Message'])
        # Add your notification handling logic here
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notification processed')
        }
    
    return {
        'statusCode': 400,
        'body': json.dumps('Unsupported event type')
    }
