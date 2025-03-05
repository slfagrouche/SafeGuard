import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import json
import logging

logger = logging.getLogger(__name__)

class SNSManager:
    def __init__(self):
        self.sns = boto3.client(
            'sns',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.topic_arn = settings.SNS_TOPIC_ARN

    def subscribe_email(self, email):
        """
        Subscribe an email address to the SNS topic
        
        Args:
            email (str): Email address to subscribe
            
        Returns:
            dict: Subscription details including ARN and status
        """
        try:
            response = self.sns.subscribe(
                TopicArn=self.topic_arn,
                Protocol='email',
                Endpoint=email,
                ReturnSubscriptionArn=True
            )
            return {
                'subscription_arn': response['SubscriptionArn'],
                'status': 'PENDING_CONFIRMATION'
            }
        except ClientError as e:
            logger.error(f"Error subscribing email to SNS: {str(e)}")
            raise

    def send_notification(self, subject, message, email=None):
        """
        Send a notification to all subscribers or a specific email
        
        Args:
            subject (str): Subject of the notification
            message (str): Message body
            email (str, optional): Specific email to send to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message_data = {
                'default': message,
                'email': message
            }
            
            publish_args = {
                'TopicArn': self.topic_arn,
                'Message': json.dumps(message_data),
                'Subject': subject,
                'MessageStructure': 'json'
            }
            
            # If email is provided, we'll still publish to the topic but filter by email
            if email:
                # Add message attributes to filter by email
                publish_args['MessageAttributes'] = {
                    'email': {
                        'DataType': 'String',
                        'StringValue': email
                    }
                }
            
            self.sns.publish(**publish_args)
            return True
            
        except ClientError as e:
            logger.error(f"Error sending SNS notification: {str(e)}")
            return False

    def unsubscribe(self, subscription_arn):
        """
        Unsubscribe from the SNS topic
        
        Args:
            subscription_arn (str): ARN of the subscription to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sns.unsubscribe(
                SubscriptionArn=subscription_arn
            )
            return True
        except ClientError as e:
            logger.error(f"Error unsubscribing from SNS: {str(e)}")
            return False

    def get_subscription_status(self, email):
        """
        Get the subscription status for an email address
        
        Args:
            email (str): Email address to check
            
        Returns:
            dict: Subscription details including ARN and status
        """
        try:
            subscriptions = self.sns.list_subscriptions_by_topic(
                TopicArn=self.topic_arn
            )['Subscriptions']
            
            for sub in subscriptions:
                if sub['Endpoint'] == email:
                    return {
                        'subscription_arn': sub['SubscriptionArn'],
                        'status': 'CONFIRMED' if sub['SubscriptionArn'] != 'PendingConfirmation' else 'PENDING_CONFIRMATION'
                    }
            
            return None
            
        except ClientError as e:
            logger.error(f"Error getting subscription status: {str(e)}")
            raise

# Create a singleton instance
sns_manager = SNSManager()
