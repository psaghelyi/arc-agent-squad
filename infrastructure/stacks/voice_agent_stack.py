"""
AWS CDK Stack for Voice Agent Swarm infrastructure.

This stack creates all the necessary AWS resources for hosting
a voice-enabled agent swarm including:
- ECS Fargate for containerized agents
- ALB for load balancing
- ECR for container registry
- Bedrock permissions
- Transcribe and Polly services setup
- CloudWatch logging
- VPC with proper security groups
"""

from typing import Dict

import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_logs as logs
from constructs import Construct


class VoiceAgentStack(cdk.Stack):
    """Main stack for Voice Agent Swarm infrastructure."""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create VPC
        self.vpc = self._create_vpc()
        
        # Create ECR repository
        self.ecr_repository = self._create_ecr_repository()
        
        # Create ECS cluster
        self.ecs_cluster = self._create_ecs_cluster()
        
        # Create IAM roles
        self.task_role, self.execution_role = self._create_iam_roles()
        
        # Create ECS service
        self.ecs_service = self._create_ecs_service()
        
        # Create load balancer
        self.load_balancer = self._create_load_balancer()
        
        # Create CloudWatch log groups
        self._create_log_groups()
        
        # Output important values
        self._create_outputs()
    
    def _create_vpc(self) -> ec2.Vpc:
        """Create VPC with public and private subnets."""
        vpc = ec2.Vpc(
            self, "VoiceAgentVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # Add VPC endpoint for ECR
        vpc.add_interface_endpoint(
            "ECREndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR
        )
        
        # Add VPC endpoint for ECR Docker registry
        vpc.add_interface_endpoint(
            "ECRDockerEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )
        
        # Add VPC endpoint for CloudWatch Logs
        vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS
        )
        
        return vpc
    
    def _create_ecr_repository(self) -> ecr.Repository:
        """Create ECR repository for container images."""
        repository = ecr.Repository(
            self, "VoiceAgentRepository",
            repository_name="voice-agent-swarm",
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,
                    rule_priority=1,
                    description="Keep only 10 latest images"
                )
            ],
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        
        return repository
    
    def _create_ecs_cluster(self) -> ecs.Cluster:
        """Create ECS cluster for running containers."""
        cluster = ecs.Cluster(
            self, "VoiceAgentCluster",
            cluster_name="voice-agent-swarm",
            vpc=self.vpc,
            container_insights=True
        )
        
        return cluster
    
    def _create_iam_roles(self) -> tuple[iam.Role, iam.Role]:
        """Create IAM roles for ECS tasks."""
        
        # Task execution role
        execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ]
        )
        
        # Task role with permissions for AWS services
        task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        
        # Add Bedrock permissions
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ListFoundationModels",
                    "bedrock:GetFoundationModel"
                ],
                resources=["*"]
            )
        )
        
        # Add Transcribe permissions
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                    "transcribe:StartStreamTranscription"
                ],
                resources=["*"]
            )
        )
        
        # Add Polly permissions
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "polly:SynthesizeSpeech",
                    "polly:DescribeVoices"
                ],
                resources=["*"]
            )
        )
        
        # Add Lex permissions
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lex:RecognizeText",
                    "lex:RecognizeUtterance",
                    "lex:PostContent",
                    "lex:PostText"
                ],
                resources=["*"]
            )
        )
        
        # Add CloudWatch Logs permissions
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )
        
        return task_role, execution_role
    
    def _create_ecs_service(self) -> ecs.FargateService:
        """Create ECS Fargate service."""
        
        # Create task definition
        task_definition = ecs.FargateTaskDefinition(
            self, "VoiceAgentTaskDefinition",
            memory_limit_mib=2048,
            cpu=1024,
            task_role=self.task_role,
            execution_role=self.execution_role
        )
        
        # Add container
        container = task_definition.add_container(
            "VoiceAgentContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                self.ecr_repository, "latest"
            ),
            memory_limit_mib=2048,
            cpu=1024,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="voice-agent",
                log_group=logs.LogGroup(
                    self, "VoiceAgentLogGroup",
                    log_group_name="/aws/ecs/voice-agent-swarm",
                    retention=logs.RetentionDays.ONE_WEEK,
                    removal_policy=cdk.RemovalPolicy.DESTROY
                )
            ),
            environment={
                "AWS_DEFAULT_REGION": self.region,
                "ENVIRONMENT": "production"
            }
        )
        
        # Add port mapping
        container.add_port_mappings(
            ecs.PortMapping(
                container_port=8000,
                protocol=ecs.Protocol.TCP
            )
        )
        
        # Create security group
        security_group = ec2.SecurityGroup(
            self, "VoiceAgentSecurityGroup",
            vpc=self.vpc,
            description="Security group for Voice Agent containers",
            allow_all_outbound=True
        )
        
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8000),
            description="HTTP traffic"
        )
        
        # Create ECS service
        service = ecs.FargateService(
            self, "VoiceAgentService",
            cluster=self.ecs_cluster,
            task_definition=task_definition,
            desired_count=2,
            security_groups=[security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            enable_logging=True
        )
        
        return service
    
    def _create_load_balancer(self) -> elbv2.ApplicationLoadBalancer:
        """Create Application Load Balancer."""
        
        # Create ALB
        alb = elbv2.ApplicationLoadBalancer(
            self, "VoiceAgentALB",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name="voice-agent-swarm-alb"
        )
        
        # Create target group
        target_group = elbv2.ApplicationTargetGroup(
            self, "VoiceAgentTargetGroup",
            vpc=self.vpc,
            port=8000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                enabled=True,
                healthy_http_codes="200",
                interval=cdk.Duration.seconds(30),
                path="/health",
                protocol=elbv2.Protocol.HTTP,
                timeout=cdk.Duration.seconds(10)
            )
        )
        
        # Add targets
        target_group.add_target(
            self.ecs_service.load_balancer_target(
                container_name="VoiceAgentContainer",
                container_port=8000
            )
        )
        
        # Add listener
        alb.add_listener(
            "VoiceAgentListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[target_group]
        )
        
        return alb
    
    def _create_log_groups(self) -> None:
        """Create CloudWatch log groups."""
        
        # API Gateway logs
        logs.LogGroup(
            self, "APILogGroup",
            log_group_name="/aws/apigateway/voice-agent-swarm",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        
        # Application logs
        logs.LogGroup(
            self, "ApplicationLogGroup", 
            log_group_name="/aws/application/voice-agent-swarm",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        cdk.CfnOutput(
            self, "ECRRepositoryURI",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI for voice agent images"
        )
        
        cdk.CfnOutput(
            self, "LoadBalancerDNS",
            value=self.load_balancer.load_balancer_dns_name,
            description="DNS name of the Application Load Balancer"
        )
        
        cdk.CfnOutput(
            self, "ECSClusterName",
            value=self.ecs_cluster.cluster_name,
            description="Name of the ECS cluster"
        ) 