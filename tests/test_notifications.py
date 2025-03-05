import pytest
from unittest.mock import patch, MagicMock
from incidents.notifications import sns_manager
from incidents.dynamodb import dynamodb_manager
from botocore.exceptions import ClientError

@pytest.fixture
def mock_sns():
    with patch('boto3.client') as mock_client:
        mock_sns = MagicMock()
        mock_client.return_value = mock_sns
        yield mock_sns

@pytest.fixture
def mock_dynamodb():
    with patch('incidents.dynamodb.DynamoDBManager.subscribers_table') as mock_table:
        yield mock_table

def test_subscribe_email_success(mock_sns):
    # Setup
    email = "test@example.com"
    mock_sns.subscribe.return_value = {
        'SubscriptionArn': 'test:arn:123'
    }
    
    # Execute
    result = sns_manager.subscribe_email(email)
    
    # Verify
    assert result['status'] == 'PENDING_CONFIRMATION'
    assert result['subscription_arn'] == 'test:arn:123'
    mock_sns.subscribe.assert_called_once_with(
        TopicArn=sns_manager.topic_arn,
        Protocol='email',
        Endpoint=email,
        ReturnSubscriptionArn=True
    )

def test_subscribe_email_failure(mock_sns):
    # Setup
    email = "test@example.com"
    mock_sns.subscribe.side_effect = ClientError(
        {'Error': {'Code': 'InvalidParameter'}},
        'Subscribe'
    )
    
    # Execute & Verify
    with pytest.raises(ClientError):
        sns_manager.subscribe_email(email)

def test_send_notification_success(mock_sns):
    # Setup
    subject = "Test Subject"
    message = "Test Message"
    mock_sns.publish.return_value = {'MessageId': 'test123'}
    
    # Execute
    result = sns_manager.send_notification(subject, message)
    
    # Verify
    assert result is True
    mock_sns.publish.assert_called_once()

def test_send_notification_to_specific_email(mock_sns):
    # Setup
    subject = "Test Subject"
    message = "Test Message"
    email = "test@example.com"
    mock_sns.list_subscriptions_by_topic.return_value = {
        'Subscriptions': [
            {
                'Endpoint': email,
                'SubscriptionArn': 'test:arn:123'
            }
        ]
    }
    mock_sns.publish.return_value = {'MessageId': 'test123'}
    
    # Execute
    result = sns_manager.send_notification(subject, message, email)
    
    # Verify
    assert result is True
    mock_sns.publish.assert_called_once()

def test_create_subscriber_with_sns_integration(mock_sns, mock_dynamodb):
    # Setup
    subscriber_data = {
        'email': 'test@example.com',
        'name': 'Test User',
        'address': '123 Test St',
        'latitude': '40.7128',
        'longitude': '-74.0060'
    }
    mock_sns.subscribe.return_value = {
        'SubscriptionArn': 'test:arn:123'
    }
    
    # Execute
    result = dynamodb_manager.create_subscriber(subscriber_data)
    
    # Verify
    assert result == subscriber_data['email']
    mock_dynamodb.put_item.assert_called_once()
    mock_sns.subscribe.assert_called_once()

def test_get_subscription_status(mock_sns):
    # Setup
    email = "test@example.com"
    mock_sns.list_subscriptions_by_topic.return_value = {
        'Subscriptions': [
            {
                'Endpoint': email,
                'SubscriptionArn': 'test:arn:123'
            }
        ]
    }
    
    # Execute
    result = sns_manager.get_subscription_status(email)
    
    # Verify
    assert result['status'] == 'CONFIRMED'
    assert result['subscription_arn'] == 'test:arn:123'

def test_unsubscribe_success(mock_sns):
    # Setup
    subscription_arn = 'test:arn:123'
    mock_sns.unsubscribe.return_value = {}
    
    # Execute
    result = sns_manager.unsubscribe(subscription_arn)
    
    # Verify
    assert result is True
    mock_sns.unsubscribe.assert_called_once_with(
        SubscriptionArn=subscription_arn
    )

# Manual Testing Steps
"""
To manually test the notification system:

1. Create a new subscriber:
   - Use the subscription form on the website
   - Provide a valid email address
   - Check email for confirmation link
   - Click confirmation link to verify subscription

2. Verify subscriber creation:
   - Check DynamoDB Subscribers table for new entry
   - Verify subscription_status is updated to CONFIRMED
   - Verify subscription_arn is populated
   - Check email for welcome notification

3. Test notification delivery:
   - Create a new incident
   - Verify notification is received via email
   - Check notification content matches incident details

4. Test unsubscribe functionality:
   - Use unsubscribe link in any notification email
   - Verify subscription is removed from SNS
   - Verify subscription_status is updated in DynamoDB

5. Error handling:
   - Try subscribing with invalid email
   - Try subscribing same email twice
   - Try sending notification to unsubscribed email
   - Verify appropriate error handling and user feedback

Note: Before testing, ensure these environment variables are set:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- SNS_TOPIC_ARN
"""
