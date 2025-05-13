# Respond.IO AWS Integration Architecture

This repository contains the AWS SAM (Serverless Application Model) templates and configuration for integrating with Respond.IO platform. The architecture is designed to handle various webhook events from Respond.IO and process them through a serverless event-driven architecture.

## Architecture Overview

The solution is built using various AWS services including:

- API Gateway
- SNS (Simple Notification Service)
- SQS (Simple Queue Service)
- Lambda Functions
- Aurora PostgreSQL
- EventBridge
- Secrets Manager
- Parameter Store
- CloudWatch

### High-Level Architecture Flow

1. Respond.IO webhooks send events to API Gateway endpoints
2. API Gateway forwards events to SNS topic with event type filtering
3. SNS distributes messages to appropriate SQS queues based on event type
4. Lambda functions process events from their respective SQS queues
5. Data is stored in Aurora PostgreSQL database
6. Scheduled tasks handle conversation management

## Main Components

### template.yaml

The main SAM template that defines the entire infrastructure. Key components include:

#### API Gateway
- Handles incoming webhooks from Respond.IO
- IP-based access control for Respond.IO servers
- API key authentication

#### SNS Topics
- `RespondSNSEntryPoint`: Main entry point for all events
- `RespondSNSGlobal`: Global SNS topic for broader communications

#### SQS Queues
The following event-specific queues are configured:
- Message Received
- Keyword Detection
- After Hour Notification
- After Hour Assign
- Message Sent (User)
- Contact Created/Updated
- Contact Assignee Updated
- Conversation Opened/Closed
- Message Sent (Workflow)
- Analyze Conversation

#### Lambda Functions
Multiple Lambda functions handle specific event types:
- After Hour Notification/Assign
- Keyword Detection
- Customer Data Management
- Message Processing
- Contact Management
- Conversation Management
- Analysis Functions

#### Database
- Aurora PostgreSQL cluster
- Custom parameter group and subnet group
- Monitoring and backup configurations

#### Security
- VPC configuration
- Security groups
- IAM roles and policies
- Secrets management
- API authentication

### parameter-resolver.yaml

A helper template that resolves infrastructure parameters:
- VPC ID resolution
- Subnet IDs resolution
- Helps manage network configurations across environments

### samconfig.toml

Configuration file for SAM CLI deployment with environment-specific settings:

#### Environments
- QA Environment (`qarespond`)
  - Region: us-east-1
  - Stack name: qarespond-int-respondIo
  - Parameter overrides for QA configuration

- Production Environment (`prodrespond`)
  - Region: us-east-1
  - Stack name: prodrespond-int-respondIo
  - Parameter overrides for production configuration

## Detailed Components

### SQS Queues and Event Filtering

Each SQS queue is subscribed to specific event types through SNS filtering:

1. **RespondMessageReceivedSQS**
   - Filter Policy:
     - event_type: "message.received"
     - flowtype: "platform"
   - Target Lambda: `SaveMessageReceivedToDatabaseFunction`
   - Purpose: Processes new incoming messages

2. **RespondKeywordDetectionSQS**
   - Filter Policy:
     - event_type: "message.received"
     - flowtype: "platform"
   - Target Lambda: `KeywordsDetectedFunction`
   - Purpose: Analyzes messages for specific keywords

3. **RespondAfterHourNotificationSQS**
   - Filter Policy:
     - event_type: "send.after_hour_message"
     - flowtype: "platform"
   - Target Lambda: `afterHourNotificationFunction`
   - Purpose: Handles after-hours notifications

4. **RespondAfterHourAssignSQS**
   - Filter Policy:
     - event_type: "send.after_hour_assign"
     - flowtype: "platform"
   - Target Lambda: `AfterHourAssignFunction`
   - Purpose: Manages after-hours assignments

5. **RespondMessageSentUserSQS**
   - Filter Policy:
     - event_type: "message.sent"
     - flowtype: "user"
   - Target Lambda: `SaveMessageSentToDatabaseFunction`
   - Purpose: Tracks user-sent messages

6. **RespondContactCreatedSQS**
   - Filter Policy:
     - event_type: "contact.created"
     - flowtype: "platform"
   - Target Lambda: `ContactCreatedFunction`
   - Purpose: Processes new contact creation

7. **RespondContactUpdatedSQS**
   - Filter Policy:
     - event_type: "contact.updated"
     - flowtype: "platform"
   - Target Lambda: `ContactUpdatedFunction`
   - Purpose: Handles contact updates

8. **RespondContactAssigneeUpdatedSQS**
   - Filter Policy:
     - event_type: "contact.assignee.updated"
     - flowtype: "platform"
   - Target Lambda: `ContactUpdatedAssigneeFunction`
   - Purpose: Manages contact assignee changes

9. **RespondConversationOpenedSQS**
   - Filter Policy:
     - event_type: "conversation.opened"
     - flowtype: "platform"
   - Target Lambda: `ConversationOpenedFunction`
   - Purpose: Handles new conversation events

10. **RespondConversationClosedSQS**
    - Filter Policy:
      - event_type: "conversation.closed"
      - flowtype: "platform"
    - Target Lambda: `ConversationClosedFunction`
    - Purpose: Processes conversation closure events

11. **RespondMessageSentWorkflowSQS**
    - Filter Policy:
      - event_type: "message.sent"
      - flowtype: "flowtype"
    - Target Lambda: `SaveOutgoingMessagesFromWorkflowFunction`
    - Purpose: Handles workflow-generated messages

### IAM Policies

1. **GetSecretPolicy**
   - Purpose: Allows access to Secrets Manager
   - Access: `secretsmanager:GetSecretValue`
   - Resource: PostgreSQL RDS secrets

2. **GetApiParameterPolicy**
   - Purpose: Access to API token parameter
   - Access: `ssm:GetParameter`
   - Resource: Respond.io API token parameter

3. **GetConfigParameterPolicy**
   - Purpose: Access to configuration parameters
   - Access: `ssm:GetParameter`
   - Resource: Respond.io configuration parameter

4. **SendEmailPolicy**
   - Purpose: Allows email sending via SES
   - Access: `ses:SendEmail`
   - Resource: All (*) 

### Lambda Functions and Their Configurations

1. **afterHourNotificationFunction**
   - Policies:
     - AWSLambdaBasicExecutionRole
     - GetSecretPolicy
     - GetApiParameterPolicy
     - GetConfigParameterPolicy
     - SendEmailPolicy
   - Environment Variables:
     - secretRespondIO: Database connection secret
     - RESPOND_API_TOKEN: API authentication
     - RESPOND_CONFIG_PARAMETER: Configuration settings

2. **AnalyzeConversationFunction**
   - Policies:
     - AWSLambdaBasicExecutionRole
     - GetSecretPolicy
     - SendEmailPolicy
     - GetConfigParameterPolicy
     - Bedrock invocation permissions
   - Environment Variables:
     - secretRespondIO: Database connection
     - RESPOND_CONFIG_PARAMETER: Configuration

[Continue with other Lambda functions...]

### Parameter Store Configuration

1. **RespondApiTokenParameter**
   - Path: /${Environment}/respond/parameters/common/cr/respond-api-token
   - Purpose: Stores the API token for Respond.io authentication
   - Type: String

2. **RespondConfigParameter**
   - Path: /${Environment}/respond/parameters/common/cr/respond-config
   - Purpose: Stores general configuration settings
   - Type: String

3. **SecretCommonPostgresOutputParameter**
   - Path: /${Environment}/respond/parameters/common/cr/secret/postgres/temp
   - Purpose: Stores database connection information
   - Type: String

### Network and Security Configuration

#### VPC Configuration
- Uses parameter-resolver.yaml to obtain VPC and subnet information
- Parameters retrieved from SSM Parameter Store:
  - /${Environment}/ate/parameters/network/subnet-ids
  - /${Environment}/ate/parameters/network/vpc-id

#### Security Groups

1. **SecurityGroupLambdaRespondDefault**
   - Purpose: Default security group for Lambda functions
   - Ingress Rules:
     - All traffic (0.0.0.0/0)
   - Egress Rules:
     - All traffic (0.0.0.0/0)

2. **DBSecurityGroup**
   - Purpose: Security group for Aurora RDS
   - Ingress Rules:
     - Port: 5432 (PostgreSQL)
     - Source: 10.0.0.0/8 (Internal network)

#### API Gateway Security
- IP Whitelisting:
  ```json
  "NotIpAddress": {
    "aws:SourceIp": [
      "52.74.35.155/32",
      "18.138.31.163/32",
      "54.169.155.20/32",
      "190.120.250.245/32"
    ]
  }
  ```
- API Key Authentication
- Request Validation

#### Database Security
- VPC Subnet Group Configuration
- Encrypted Credentials in Secrets Manager
- Performance Insights Enabled
- Enhanced Monitoring with Custom IAM Role

## Deployment

### Prerequisites
- AWS SAM CLI
- AWS CLI configured with appropriate credentials
- Python 3.12
- Access to target AWS account

### Deployment Commands

For QA environment:
```bash
sam deploy --config-env qarespond
```

For Production environment:
```bash
sam deploy --config-env prodrespond
```

## Environment Variables

The following environment variables are used across Lambda functions:
- `secretRespondIO`: Secret for PostgreSQL database connection
- `RESPOND_API_TOKEN`: API token for Respond.IO API
- `RESPOND_CONFIG_PARAMETER`: Configuration parameters
- `ANALYZE_CONVERSATION_FUNCTION_NAME`: Name of analysis function
- `RESPOND_ANALYZE_CONVERSATION_SQS`: SQS queue for conversation analysis

## Monitoring and Logging

- Each Lambda function has its own CloudWatch Log Group
- Log retention is set to 30 days
- CloudWatch metrics available for all components

## Security Considerations

1. API Gateway is protected with:
   - IP whitelisting
   - API key authentication
   - Request validation

2. Database security:
   - VPC isolation
   - Security group restrictions
   - Encrypted credentials in Secrets Manager

3. Lambda security:
   - VPC deployment
   - Minimal IAM permissions
   - Environment variable encryption

## Scaling and Performance

- Lambda functions configured with appropriate memory and timeout settings
- SQS queues handle message buffering and retry logic
- Aurora database can scale based on demand

## Maintenance

### Regular Tasks
- Monitor CloudWatch logs
- Review API Gateway usage
- Check SQS queue metrics
- Monitor database performance

### Troubleshooting
- Check CloudWatch logs for Lambda errors
- Verify SQS queue depths
- Monitor API Gateway 4xx/5xx errors
- Review Aurora database logs

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review event patterns in SNS/SQS
3. Verify API Gateway configurations
4. Check Lambda function configurations
