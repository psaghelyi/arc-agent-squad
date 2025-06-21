"""
AWS CDK stack for GRC Agent Squad infrastructure.

This stack creates:
- VPC with public and private subnets
- ECS Fargate cluster and service
- Application Load Balancer
- ECR repository
- CloudWatch log groups
- Security groups and IAM roles
"""

from typing import Dict, Any

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class GRCAgentStack(Stack):
    """CDK Stack for GRC Agent Squad infrastructure."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = self._create_vpc()
        
        # Create ECR repository
        self.repository = self._create_ecr_repository()
        
        # Create ECS cluster
        self.cluster = self._create_ecs_cluster()
        
        # Create IAM roles
        self.task_role, self.execution_role = self._create_iam_roles()
        
        # Create CloudWatch log group
        self.log_group = self._create_log_group()
        
        # Create security groups
        self.security_group = self._create_security_groups()
        
        # Create ECS service and task definition
        self.service = self._create_ecs_service()
        
        # Create Application Load Balancer
        self.load_balancer = self._create_load_balancer()

    def _create_vpc(self) -> ec2.Vpc:
        """Create VPC with public and private subnets."""
        return ec2.Vpc(
            self, "GRCAgentVPC",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
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

    def _create_ecr_repository(self) -> ecr.Repository:
        """Create ECR repository for container images."""
        return ecr.Repository(
            self, "GRCAgentRepository",
            repository_name="grc-agent-squad",
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,
                    rule_priority=1,
                    description="Keep only 10 most recent images"
                )
            ]
        )

    def _create_ecs_cluster(self) -> ecs.Cluster:
        """Create ECS Fargate cluster."""
        return ecs.Cluster(
            self, "GRCAgentCluster",
            vpc=self.vpc,
            cluster_name="grc-agent-squad-cluster",
            enable_fargate_capacity_providers=True
        )

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
            self, "GRCAgentTaskDefinition",
            memory_limit_mib=2048,
            cpu=1024,
            task_role=self.task_role,
            execution_role=self.execution_role
        )
        
        # Add container
        container = task_definition.add_container(
            "GRCAgentContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                self.repository, "latest"
            ),
            memory_limit_mib=2048,
            cpu=1024,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="grc-agent",
                log_group=logs.LogGroup(
                    self, "GRCAgentLogGroup",
                    log_group_name="/aws/ecs/grc-agent-squad",
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
            self, "GRCAgentSecurityGroup",
            vpc=self.vpc,
            description="Security group for GRC Agent containers",
            allow_all_outbound=True
        )
        
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8000),
            description="HTTP traffic"
        )
        
        # Create ECS service
        service = ecs.FargateService(
            self, "GRCAgentService",
            cluster=self.cluster,
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
            self, "GRCAgentALB",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name="grc-agent-squad-alb"
        )
        
        # Create target group
        target_group = elbv2.ApplicationTargetGroup(
            self, "GRCAgentTargetGroup",
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
            self.service.load_balancer_target(
                container_name="GRCAgentContainer",
                container_port=8000
            )
        )
        
        # Add listener
        alb.add_listener(
            "GRCAgentListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[target_group]
        )
        
        return alb

    def _create_log_group(self) -> logs.LogGroup:
        """Create CloudWatch log group."""
        
        # API Gateway logs
        logs.LogGroup(
            self, "APILogGroup",
            log_group_name="/aws/apigateway/grc-agent-squad",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        
        # Application logs
        logs.LogGroup(
            self, "ApplicationLogGroup", 
            log_group_name="/aws/application/grc-agent-squad",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        
        return logs.LogGroup(
            self, "GRCAgentLogGroup",
            log_group_name="/aws/ecs/grc-agent-squad",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

    def _create_security_groups(self) -> ec2.SecurityGroup:
        """Create security groups for GRC Agent containers."""
        security_group = ec2.SecurityGroup(
            self, "GRCAgentSecurityGroup",
            vpc=self.vpc,
            description="Security group for GRC Agent containers",
            allow_all_outbound=True
        )
        
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8000),
            description="HTTP traffic"
        )
        
        return security_group

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        cdk.CfnOutput(
            self, "ECRRepositoryURI",
            value=self.repository.repository_uri,
            description="ECR Repository URI for GRC Agent images"
        )
        
        cdk.CfnOutput(
            self, "LoadBalancerDNS",
            value=self.load_balancer.load_balancer_dns_name,
            description="DNS name of the Application Load Balancer"
        )
        
        cdk.CfnOutput(
            self, "ECSClusterName",
            value=self.cluster.cluster_name,
            description="Name of the ECS cluster"
        ) 