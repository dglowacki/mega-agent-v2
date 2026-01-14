"""
AWS Client for mega-agent2 using boto3.

Provides operational control over AWS resources:
- EC2: instances, security groups, volumes
- S3: buckets, objects
- Lambda: functions, invocations
- RDS: databases, snapshots
- IAM: users, roles, policies
- CloudWatch: logs, metrics
- Route53: hosted zones, DNS records

Credentials loaded from /home/ec2-user/mega-agent/.env
"""

import boto3
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


class AWSClient:
    """Unified AWS client for mega-agent2 operations."""

    def __init__(self, region: str = None):
        """
        Initialize AWS client with credentials from .env file.

        Args:
            region: AWS region (defaults to AWS_DEFAULT_REGION from .env)
        """
        # Load credentials from old mega-agent .env
        env_path = '/home/ec2-user/mega-agent/.env'
        if os.path.exists(env_path):
            load_dotenv(env_path)

        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

        if not self.access_key or not self.secret_key:
            raise ValueError(
                "AWS credentials not found. "
                "Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set in "
                "/home/ec2-user/mega-agent/.env"
            )

        # Initialize boto3 session
        self.session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

    def get_client(self, service: str):
        """Get boto3 client for specific AWS service."""
        return self.session.client(service)

    def get_resource(self, service: str):
        """Get boto3 resource for specific AWS service."""
        return self.session.resource(service)

    # ============================================================
    # EC2 Operations
    # ============================================================

    def list_ec2_instances(self, filters: List[Dict] = None) -> List[Dict]:
        """
        List EC2 instances.

        Args:
            filters: EC2 filters (e.g., [{'Name': 'instance-state-name', 'Values': ['running']}])

        Returns:
            List of instance dictionaries with id, type, state, tags
        """
        ec2 = self.get_client('ec2')

        kwargs = {}
        if filters:
            kwargs['Filters'] = filters

        response = ec2.describe_instances(**kwargs)

        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'id': instance['InstanceId'],
                    'type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'launch_time': instance.get('LaunchTime'),
                    'private_ip': instance.get('PrivateIpAddress'),
                    'public_ip': instance.get('PublicIpAddress'),
                    'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                })

        return instances

    def stop_ec2_instance(self, instance_id: str) -> Dict:
        """Stop an EC2 instance."""
        ec2 = self.get_client('ec2')
        response = ec2.stop_instances(InstanceIds=[instance_id])
        return response['StoppingInstances'][0]

    def start_ec2_instance(self, instance_id: str) -> Dict:
        """Start an EC2 instance."""
        ec2 = self.get_client('ec2')
        response = ec2.start_instances(InstanceIds=[instance_id])
        return response['StartingInstances'][0]

    def terminate_ec2_instance(self, instance_id: str) -> Dict:
        """Terminate an EC2 instance."""
        ec2 = self.get_client('ec2')
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        return response['TerminatingInstances'][0]

    def modify_ec2_instance_type(self, instance_id: str, instance_type: str) -> Dict:
        """
        Modify EC2 instance type (instance must be stopped first).

        Args:
            instance_id: Instance ID
            instance_type: New instance type (e.g., 't3.medium')
        """
        ec2 = self.get_client('ec2')
        response = ec2.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={'Value': instance_type}
        )
        return {'instance_id': instance_id, 'new_type': instance_type}

    # ============================================================
    # S3 Operations
    # ============================================================

    def list_s3_buckets(self) -> List[Dict]:
        """List all S3 buckets."""
        s3 = self.get_client('s3')
        response = s3.list_buckets()
        return [{'name': bucket['Name'], 'created': bucket['CreationDate']}
                for bucket in response['Buckets']]

    def list_s3_objects(self, bucket: str, prefix: str = '') -> List[Dict]:
        """List objects in S3 bucket."""
        s3 = self.get_client('s3')
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if 'Contents' not in response:
            return []

        return [{'key': obj['Key'], 'size': obj['Size'], 'modified': obj['LastModified']}
                for obj in response['Contents']]

    def upload_to_s3(self, file_path: str, bucket: str, key: str) -> Dict:
        """Upload file to S3."""
        s3 = self.get_client('s3')
        s3.upload_file(file_path, bucket, key)
        return {'bucket': bucket, 'key': key, 'local_file': file_path}

    def download_from_s3(self, bucket: str, key: str, file_path: str) -> Dict:
        """Download file from S3."""
        s3 = self.get_client('s3')
        s3.download_file(bucket, key, file_path)
        return {'bucket': bucket, 'key': key, 'local_file': file_path}

    def delete_s3_object(self, bucket: str, key: str) -> Dict:
        """Delete object from S3."""
        s3 = self.get_client('s3')
        s3.delete_object(Bucket=bucket, Key=key)
        return {'bucket': bucket, 'key': key, 'deleted': True}

    def create_s3_bucket(self, bucket: str, region: str = None) -> Dict:
        """Create S3 bucket."""
        s3 = self.get_client('s3')

        if region is None:
            region = self.session.region_name

        try:
            if region == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                s3.create_bucket(Bucket=bucket)
            else:
                s3.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            return {'bucket': bucket, 'region': region, 'created': True}
        except Exception as e:
            return {'bucket': bucket, 'region': region, 'created': False, 'error': str(e)}

    def configure_s3_website(self, bucket: str, index_document: str = 'index.html',
                            error_document: str = 'error.html') -> Dict:
        """Configure S3 bucket for static website hosting."""
        s3 = self.get_client('s3')

        # Disable block public access FIRST
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )

        # Configure website hosting
        website_config = {
            'IndexDocument': {'Suffix': index_document},
            'ErrorDocument': {'Key': error_document}
        }
        s3.put_bucket_website(Bucket=bucket, WebsiteConfiguration=website_config)

        # Set bucket policy for public read
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket}/*"
            }]
        }

        import json
        s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))

        # Get website endpoint
        region = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
        if region is None:
            region = 'us-east-1'

        if region == 'us-east-1':
            endpoint = f"{bucket}.s3-website-us-east-1.amazonaws.com"
        else:
            endpoint = f"{bucket}.s3-website-{region}.amazonaws.com"

        return {
            'bucket': bucket,
            'website_endpoint': endpoint,
            'index_document': index_document,
            'error_document': error_document
        }

    # ============================================================
    # Lambda Operations
    # ============================================================

    def list_lambda_functions(self) -> List[Dict]:
        """List Lambda functions."""
        lambda_client = self.get_client('lambda')
        response = lambda_client.list_functions()

        return [{'name': func['FunctionName'],
                 'runtime': func['Runtime'],
                 'memory': func['MemorySize'],
                 'timeout': func['Timeout'],
                 'last_modified': func['LastModified']}
                for func in response['Functions']]

    def invoke_lambda(self, function_name: str, payload: Dict = None) -> Dict:
        """
        Invoke Lambda function.

        Args:
            function_name: Function name
            payload: JSON payload for function

        Returns:
            Response with status code and payload
        """
        import json
        lambda_client = self.get_client('lambda')

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload or {})
        )

        return {
            'status_code': response['StatusCode'],
            'payload': json.loads(response['Payload'].read()),
            'function_name': function_name
        }

    def get_lambda_function(self, function_name: str) -> Dict:
        """Get Lambda function configuration."""
        lambda_client = self.get_client('lambda')
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']

    # ============================================================
    # RDS Operations
    # ============================================================

    def list_rds_instances(self) -> List[Dict]:
        """List RDS database instances."""
        rds = self.get_client('rds')
        response = rds.describe_db_instances()

        return [{'id': db['DBInstanceIdentifier'],
                 'engine': db['Engine'],
                 'instance_class': db['DBInstanceClass'],
                 'status': db['DBInstanceStatus'],
                 'endpoint': db.get('Endpoint', {}).get('Address'),
                 'port': db.get('Endpoint', {}).get('Port')}
                for db in response['DBInstances']]

    def stop_rds_instance(self, db_instance_id: str) -> Dict:
        """Stop RDS instance."""
        rds = self.get_client('rds')
        response = rds.stop_db_instance(DBInstanceIdentifier=db_instance_id)
        return response['DBInstance']

    def start_rds_instance(self, db_instance_id: str) -> Dict:
        """Start RDS instance."""
        rds = self.get_client('rds')
        response = rds.start_db_instance(DBInstanceIdentifier=db_instance_id)
        return response['DBInstance']

    # ============================================================
    # CloudWatch Operations
    # ============================================================

    def get_cloudwatch_metrics(self, namespace: str, metric_name: str,
                               dimensions: List[Dict] = None,
                               start_time=None, end_time=None,
                               period: int = 300, stat: str = 'Average') -> List[Dict]:
        """
        Get CloudWatch metrics.

        Args:
            namespace: AWS namespace (e.g., 'AWS/EC2')
            metric_name: Metric name (e.g., 'CPUUtilization')
            dimensions: Metric dimensions
            start_time: Start time (datetime)
            end_time: End time (datetime)
            period: Period in seconds
            stat: Statistic (Average, Sum, Maximum, etc.)
        """
        from datetime import datetime, timedelta
        cloudwatch = self.get_client('cloudwatch')

        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()

        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions or [],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=[stat]
        )

        return response['Datapoints']

    def query_cloudwatch_logs(self, log_group: str, query: str,
                             start_time: int = None, end_time: int = None) -> List[Dict]:
        """
        Query CloudWatch Logs using CloudWatch Insights.

        Args:
            log_group: Log group name
            query: CloudWatch Insights query
            start_time: Start time (unix timestamp)
            end_time: End time (unix timestamp)
        """
        import time
        from datetime import datetime, timedelta

        logs = self.get_client('logs')

        if not start_time:
            start_time = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        if not end_time:
            end_time = int(datetime.utcnow().timestamp())

        # Start query
        response = logs.start_query(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            queryString=query
        )

        query_id = response['queryId']

        # Wait for query to complete
        while True:
            result = logs.get_query_results(queryId=query_id)
            if result['status'] in ['Complete', 'Failed', 'Cancelled']:
                break
            time.sleep(1)

        return result['results']

    # ============================================================
    # Route53 Domain Registration Operations
    # ============================================================

    def check_domain_availability(self, domain: str) -> Dict:
        """
        Check if a domain is available for registration.

        Args:
            domain: Domain name (e.g., 'example.com')

        Returns:
            Availability status and pricing
        """
        route53domains = self.session.client('route53domains', region_name='us-east-1')

        response = route53domains.check_domain_availability(DomainName=domain)

        return {
            'domain': domain,
            'availability': response['Availability']  # AVAILABLE, UNAVAILABLE, etc.
        }

    def register_domain(self, domain: str, duration_years: int,
                       admin_contact: Dict, registrant_contact: Dict = None,
                       tech_contact: Dict = None, privacy_protect: bool = True,
                       auto_renew: bool = True) -> Dict:
        """
        Register a new domain through Route53.

        Args:
            domain: Domain name
            duration_years: Registration duration (1-10 years)
            admin_contact: Admin contact info (required)
            registrant_contact: Registrant contact (defaults to admin_contact)
            tech_contact: Tech contact (defaults to admin_contact)
            privacy_protect: Enable WHOIS privacy protection
            auto_renew: Enable auto-renewal

        Contact dict format:
        {
            'FirstName': 'John',
            'LastName': 'Doe',
            'ContactType': 'PERSON' or 'COMPANY',
            'OrganizationName': 'Company Inc' (if COMPANY),
            'AddressLine1': '123 Main St',
            'City': 'Seattle',
            'State': 'WA',
            'CountryCode': 'US',
            'ZipCode': '98101',
            'PhoneNumber': '+1.2065551234',
            'Email': 'john@example.com'
        }

        Returns:
            Operation ID for tracking registration
        """
        route53domains = self.session.client('route53domains', region_name='us-east-1')

        # Use admin contact for all if not specified
        if not registrant_contact:
            registrant_contact = admin_contact.copy()
        if not tech_contact:
            tech_contact = admin_contact.copy()

        response = route53domains.register_domain(
            DomainName=domain,
            DurationInYears=duration_years,
            AutoRenew=auto_renew,
            AdminContact=admin_contact,
            RegistrantContact=registrant_contact,
            TechContact=tech_contact,
            PrivacyProtectAdminContact=privacy_protect,
            PrivacyProtectRegistrantContact=privacy_protect,
            PrivacyProtectTechContact=privacy_protect
        )

        return {
            'operation_id': response['OperationId'],
            'domain': domain
        }

    def get_domain_registration_status(self, operation_id: str) -> Dict:
        """
        Get status of domain registration operation.

        Args:
            operation_id: Operation ID from register_domain()

        Returns:
            Operation status
        """
        route53domains = self.session.client('route53domains', region_name='us-east-1')

        response = route53domains.get_operation_detail(OperationId=operation_id)

        return {
            'operation_id': operation_id,
            'status': response['Status'],
            'domain': response.get('DomainName'),
            'submitted_date': response.get('SubmittedDate')
        }

    # ============================================================
    # Route53 DNS Operations
    # ============================================================

    def create_hosted_zone(self, domain: str, comment: str = '') -> Dict:
        """
        Create Route53 hosted zone for a domain.

        Args:
            domain: Domain name (e.g., 'example.com')
            comment: Optional comment

        Returns:
            Hosted zone details including nameservers
        """
        import time
        route53 = self.get_client('route53')

        response = route53.create_hosted_zone(
            Name=domain,
            CallerReference=f'mega-agent-{int(time.time())}',
            HostedZoneConfig={'Comment': comment} if comment else {}
        )

        zone = response['HostedZone']
        delegation_set = response['DelegationSet']

        return {
            'id': zone['Id'],
            'name': zone['Name'],
            'nameservers': delegation_set['NameServers']
        }

    def list_hosted_zones(self) -> List[Dict]:
        """List Route53 hosted zones."""
        route53 = self.get_client('route53')
        response = route53.list_hosted_zones()

        return [{'id': zone['Id'],
                 'name': zone['Name'],
                 'records': zone['ResourceRecordSetCount']}
                for zone in response['HostedZones']]

    def list_dns_records(self, hosted_zone_id: str) -> List[Dict]:
        """List DNS records in hosted zone."""
        route53 = self.get_client('route53')

        if not hosted_zone_id.startswith('/hostedzone/'):
            hosted_zone_id = f'/hostedzone/{hosted_zone_id}'

        response = route53.list_resource_record_sets(HostedZoneId=hosted_zone_id)

        return [{'name': record['Name'],
                 'type': record['Type'],
                 'ttl': record.get('TTL'),
                 'values': [r['Value'] for r in record.get('ResourceRecords', [])]}
                for record in response['ResourceRecordSets']]

    def upsert_dns_record(self, hosted_zone_id: str, name: str,
                         record_type: str, value: str, ttl: int = 300) -> Dict:
        """
        Create or update DNS record in Route53.

        Args:
            hosted_zone_id: Hosted zone ID
            name: Record name (e.g., 'www.example.com')
            record_type: Record type (A, CNAME, TXT, etc.)
            value: Record value
            ttl: TTL in seconds (default: 300)

        Returns:
            Change info
        """
        route53 = self.get_client('route53')

        if not hosted_zone_id.startswith('/hostedzone/'):
            hosted_zone_id = f'/hostedzone/{hosted_zone_id}'

        # Ensure name ends with dot if not already
        if not name.endswith('.'):
            name = f'{name}.'

        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': name,
                        'Type': record_type,
                        'TTL': ttl,
                        'ResourceRecords': [{'Value': value}]
                    }
                }]
            }
        )

        return {
            'id': response['ChangeInfo']['Id'],
            'status': response['ChangeInfo']['Status'],
            'submitted_at': response['ChangeInfo']['SubmittedAt']
        }

    def upsert_cloudfront_alias(self, hosted_zone_id: str, name: str,
                                cloudfront_domain: str, cloudfront_hosted_zone_id: str = 'Z2FDTNDATAQYW2') -> Dict:
        """
        Create or update Route53 ALIAS record for CloudFront distribution.

        Use this for apex domains (e.g., 'example.com') which cannot use CNAME records.

        Args:
            hosted_zone_id: Route53 hosted zone ID
            name: Domain name (e.g., 'example.com')
            cloudfront_domain: CloudFront distribution domain (e.g., 'd123.cloudfront.net')
            cloudfront_hosted_zone_id: CloudFront hosted zone ID (default: Z2FDTNDATAQYW2)

        Returns:
            Change info
        """
        route53 = self.get_client('route53')

        if not hosted_zone_id.startswith('/hostedzone/'):
            hosted_zone_id = f'/hostedzone/{hosted_zone_id}'

        # Ensure name ends with dot if not already
        if not name.endswith('.'):
            name = f'{name}.'

        # Ensure CloudFront domain ends with dot
        if not cloudfront_domain.endswith('.'):
            cloudfront_domain = f'{cloudfront_domain}.'

        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': name,
                        'Type': 'A',
                        'AliasTarget': {
                            'HostedZoneId': cloudfront_hosted_zone_id,
                            'DNSName': cloudfront_domain,
                            'EvaluateTargetHealth': False
                        }
                    }
                }]
            }
        )

        return {
            'id': response['ChangeInfo']['Id'],
            'status': response['ChangeInfo']['Status'],
            'submitted_at': response['ChangeInfo']['SubmittedAt']
        }

    # ============================================================
    # IAM Operations
    # ============================================================

    def list_iam_users(self) -> List[Dict]:
        """List IAM users."""
        iam = self.get_client('iam')
        response = iam.list_users()

        return [{'name': user['UserName'],
                 'id': user['UserId'],
                 'arn': user['Arn'],
                 'created': user['CreateDate']}
                for user in response['Users']]

    def list_iam_roles(self) -> List[Dict]:
        """List IAM roles."""
        iam = self.get_client('iam')
        response = iam.list_roles()

        return [{'name': role['RoleName'],
                 'id': role['RoleId'],
                 'arn': role['Arn'],
                 'created': role['CreateDate']}
                for role in response['Roles']]

    # ============================================================
    # Cost Explorer Operations
    # ============================================================

    def get_cost_and_usage(self, start_date: str, end_date: str,
                          granularity: str = 'DAILY',
                          metrics: List[str] = None) -> Dict:
        """
        Get cost and usage data.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY, MONTHLY, or HOURLY
            metrics: List of metrics (default: ['UnblendedCost'])

        Returns:
            Cost and usage data
        """
        ce = self.get_client('ce')

        if not metrics:
            metrics = ['UnblendedCost']

        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity=granularity,
            Metrics=metrics
        )

        return response['ResultsByTime']

    # ============================================================
    # ACM (Certificate Manager) Operations
    # ============================================================

    def list_acm_certificates(self, region: str = 'us-east-1') -> List[Dict]:
        """
        List ACM certificates.

        Note: CloudFront requires certificates to be in us-east-1 region.

        Args:
            region: AWS region (default: us-east-1 for CloudFront)

        Returns:
            List of certificates with domain names and status
        """
        # CloudFront requires certificates in us-east-1
        acm = self.session.client('acm', region_name=region)
        response = acm.list_certificates()

        certificates = []
        for cert in response['CertificateSummaryList']:
            # Get detailed info
            details = acm.describe_certificate(CertificateArn=cert['CertificateArn'])
            cert_details = details['Certificate']

            certificates.append({
                'arn': cert['CertificateArn'],
                'domain_name': cert['DomainName'],
                'status': cert_details['Status'],
                'subject_alternative_names': cert_details.get('SubjectAlternativeNames', []),
                'type': cert_details.get('Type'),
                'in_use': cert_details.get('InUseBy', [])
            })

        return certificates

    def get_certificate_for_domain(self, domain: str, region: str = 'us-east-1') -> Optional[Dict]:
        """
        Find ACM certificate that covers a specific domain.

        Args:
            domain: Domain name (e.g., 'fcow.ca')
            region: AWS region (default: us-east-1 for CloudFront)

        Returns:
            Certificate info or None if not found
        """
        certificates = self.list_acm_certificates(region=region)

        for cert in certificates:
            # Check if domain matches main domain or any SAN
            if domain == cert['domain_name'] or domain in cert['subject_alternative_names']:
                # Check if certificate is valid
                if cert['status'] == 'ISSUED':
                    return cert

        return None

    def request_acm_certificate(self, domain: str,
                               subject_alternative_names: List[str] = None,
                               region: str = 'us-east-1') -> Dict:
        """
        Request new ACM certificate with DNS validation.

        Args:
            domain: Primary domain name
            subject_alternative_names: Additional domains (SANs)
            region: AWS region (default: us-east-1 for CloudFront)

        Returns:
            Certificate ARN and validation records
        """
        acm = self.session.client('acm', region_name=region)

        # Prepare SANs (include primary domain)
        sans = [domain]
        if subject_alternative_names:
            sans.extend(subject_alternative_names)

        # Request certificate
        response = acm.request_certificate(
            DomainName=domain,
            SubjectAlternativeNames=sans,
            ValidationMethod='DNS'
        )

        certificate_arn = response['CertificateArn']

        # Get validation records
        import time
        time.sleep(2)  # Wait for DNS validation records to be generated

        cert_details = acm.describe_certificate(CertificateArn=certificate_arn)

        return {
            'arn': certificate_arn,
            'domain_name': domain,
            'sans': sans,
            'status': cert_details['Certificate']['Status'],
            'validation_options': cert_details['Certificate'].get('DomainValidationOptions', [])
        }

    # ============================================================
    # CloudFront Operations
    # ============================================================

    def list_cloudfront_distributions(self) -> List[Dict]:
        """List CloudFront distributions."""
        cloudfront = self.get_client('cloudfront')
        response = cloudfront.list_distributions()

        if 'DistributionList' not in response or 'Items' not in response['DistributionList']:
            return []

        distributions = []
        for dist in response['DistributionList']['Items']:
            # Get domain names (CNAME aliases)
            aliases = dist.get('Aliases', {}).get('Items', [])

            distributions.append({
                'id': dist['Id'],
                'domain_name': dist['DomainName'],
                'aliases': aliases,
                'status': dist['Status'],
                'enabled': dist['Enabled'],
                'comment': dist.get('Comment', '')
            })

        return distributions

    def get_cloudfront_distribution_by_alias(self, alias: str) -> Optional[Dict]:
        """
        Find CloudFront distribution by alias (CNAME).

        Args:
            alias: Domain name alias (e.g., 'brickblaster.gg')

        Returns:
            Distribution info or None if not found
        """
        distributions = self.list_cloudfront_distributions()

        for dist in distributions:
            if alias in dist['aliases']:
                return dist

        return None

    def create_cloudfront_invalidation(self, distribution_id: str, paths: List[str] = None) -> Dict:
        """
        Create CloudFront cache invalidation.

        Args:
            distribution_id: CloudFront distribution ID
            paths: List of paths to invalidate (default: ['/*'] for all)

        Returns:
            Invalidation details including ID and status
        """
        import time
        cloudfront = self.get_client('cloudfront')

        if not paths:
            paths = ['/*']

        # Create invalidation
        response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f'mega-agent-{int(time.time())}'
            }
        )

        invalidation = response['Invalidation']

        return {
            'id': invalidation['Id'],
            'status': invalidation['Status'],
            'create_time': invalidation['CreateTime'],
            'paths': paths,
            'distribution_id': distribution_id
        }

    def get_cloudfront_invalidation_status(self, distribution_id: str, invalidation_id: str) -> Dict:
        """
        Get status of CloudFront invalidation.

        Args:
            distribution_id: CloudFront distribution ID
            invalidation_id: Invalidation ID

        Returns:
            Invalidation status
        """
        cloudfront = self.get_client('cloudfront')

        response = cloudfront.get_invalidation(
            DistributionId=distribution_id,
            Id=invalidation_id
        )

        invalidation = response['Invalidation']

        return {
            'id': invalidation['Id'],
            'status': invalidation['Status'],
            'create_time': invalidation['CreateTime'],
            'paths': invalidation['InvalidationBatch']['Paths']['Items']
        }

    def get_cloudfront_distribution_config(self, distribution_id: str) -> Dict:
        """
        Get CloudFront distribution configuration.

        Args:
            distribution_id: CloudFront distribution ID

        Returns:
            Distribution configuration and ETag
        """
        cloudfront = self.get_client('cloudfront')

        response = cloudfront.get_distribution_config(Id=distribution_id)

        return {
            'config': response['DistributionConfig'],
            'etag': response['ETag']
        }

    def add_aliases_to_cloudfront(self, distribution_id: str,
                                  new_aliases: List[str],
                                  certificate_arn: str = None) -> Dict:
        """
        Add aliases (CNAMEs) to CloudFront distribution.

        Args:
            distribution_id: CloudFront distribution ID
            new_aliases: List of domain names to add
            certificate_arn: ACM certificate ARN (if updating SSL)

        Returns:
            Updated distribution info
        """
        cloudfront = self.get_client('cloudfront')

        # Get current configuration
        config_response = self.get_cloudfront_distribution_config(distribution_id)
        config = config_response['config']
        etag = config_response['etag']

        # Add new aliases
        existing_aliases = config.get('Aliases', {}).get('Items', [])
        all_aliases = list(set(existing_aliases + new_aliases))  # Remove duplicates

        config['Aliases'] = {
            'Quantity': len(all_aliases),
            'Items': all_aliases
        }

        # Update certificate if provided
        if certificate_arn:
            config['ViewerCertificate'] = {
                'ACMCertificateArn': certificate_arn,
                'SSLSupportMethod': 'sni-only',
                'MinimumProtocolVersion': 'TLSv1.2_2021',
                'Certificate': certificate_arn,
                'CertificateSource': 'acm'
            }

        # Update distribution
        response = cloudfront.update_distribution(
            DistributionConfig=config,
            Id=distribution_id,
            IfMatch=etag
        )

        distribution = response['Distribution']

        return {
            'id': distribution['Id'],
            'domain_name': distribution['DomainName'],
            'aliases': config['Aliases']['Items'],
            'status': distribution['Status']
        }

    def create_cloudfront_distribution(self, origin_domain: str, aliases: List[str],
                                      certificate_arn: str, comment: str = '') -> Dict:
        """
        Create a CloudFront distribution for S3 website hosting.

        Args:
            origin_domain: S3 website endpoint (e.g., bucket.s3-website-us-east-1.amazonaws.com)
            aliases: List of domain aliases (CNAMEs)
            certificate_arn: ACM certificate ARN (must be in us-east-1)
            comment: Description for the distribution

        Returns:
            Distribution details including ID and domain name
        """
        import time
        cloudfront = self.get_client('cloudfront')

        # CloudFront distribution configuration
        distribution_config = {
            'CallerReference': f'mega-agent-{int(time.time())}',
            'Comment': comment or f'Distribution for {aliases[0]}',
            'Enabled': True,
            'Origins': {
                'Quantity': 1,
                'Items': [{
                    'Id': origin_domain,
                    'DomainName': origin_domain,
                    'CustomOriginConfig': {
                        'HTTPPort': 80,
                        'HTTPSPort': 443,
                        'OriginProtocolPolicy': 'http-only',
                        'OriginSslProtocols': {
                            'Quantity': 1,
                            'Items': ['TLSv1.2']
                        },
                        'OriginReadTimeout': 30,
                        'OriginKeepaliveTimeout': 5
                    }
                }]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': origin_domain,
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD'],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': ['GET', 'HEAD']
                    }
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'},
                    'Headers': {'Quantity': 0}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000,
                'Compress': True,
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                }
            },
            'Aliases': {
                'Quantity': len(aliases),
                'Items': aliases
            },
            'ViewerCertificate': {
                'ACMCertificateArn': certificate_arn,
                'SSLSupportMethod': 'sni-only',
                'MinimumProtocolVersion': 'TLSv1.2_2021',
                'Certificate': certificate_arn,
                'CertificateSource': 'acm'
            },
            'DefaultRootObject': 'index.html',
            'HttpVersion': 'http2',
            'IsIPV6Enabled': True,
            'PriceClass': 'PriceClass_100'  # Use only North America and Europe
        }

        # Create distribution
        response = cloudfront.create_distribution(DistributionConfig=distribution_config)
        distribution = response['Distribution']

        return {
            'id': distribution['Id'],
            'domain_name': distribution['DomainName'],
            'status': distribution['Status'],
            'aliases': aliases,
            'origin': origin_domain
        }

    # ============================================================
    # Utility Methods
    # ============================================================

    def get_caller_identity(self) -> Dict:
        """Get AWS caller identity (useful for verifying credentials)."""
        sts = self.get_client('sts')
        return sts.get_caller_identity()

    def list_regions(self, service: str = 'ec2') -> List[str]:
        """List available AWS regions for a service."""
        client = self.get_client(service)
        return [region['RegionName']
                for region in client.describe_regions()['Regions']]
