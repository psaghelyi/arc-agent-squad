# GRC Agent Squad Makefile
# 
# Credential Management:
# - Application startup (local-start, local-api) uses programmatic credential extraction
# - Infrastructure operations (CDK, Docker, AWS CLI) still use aws-vault for credential management
#
.PHONY: help install dev-install test lint format clean build deploy local-start docker-build docker-run cdk-deploy cdk-destroy venv venv-activate venv-status

# Variables
PYTHON := python3.13
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
AWS_PROFILE := acl-playground
AWS_REGION := us-west-2
APP_NAME := grc-agent-squad
DOCKER_IMAGE := $(APP_NAME):latest

# Default target
help: ## Show this help message
	@echo "GRC Agent Squad - Make Commands"
	@echo "==============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
install: ## Install production dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev-install: install ## Install development dependencies
	$(PIP) install -e ".[dev]"
	$(PIP) install pytest-cov

# Virtual environment management
venv: ## Create or update the virtual environment
	@if [ -d "$(VENV)" ]; then \
		echo "Virtual environment already exists. Updating..."; \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r requirements.txt; \
	else \
		echo "Creating virtual environment in ./$(VENV)..."; \
		$(PYTHON) -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r requirements.txt; \
	fi
	@echo "Virtual environment is ready!"

venv-activate: ## Print command to activate virtual environment (must use: eval $$(make venv-activate))
	@echo "source $(VENV)/bin/activate"

venv-status: ## Show virtual environment status and Python version
	@if [ -d "$(VENV)" ]; then \
		echo "Virtual environment exists in ./$(VENV)"; \
		$(PYTHON_VENV) --version; \
	else \
		echo "Virtual environment not found. Run 'make venv' to create it."; \
	fi

# Code quality
test: test-unit
	@echo "✅ Running unit tests (fast)"

test-unit:
	@echo "🧪 Running unit tests..."
	$(PYTHON_VENV) tests/test_runner.py unit

test-integration:
	@echo "🔗 Running integration tests..."
	$(PYTHON_VENV) tests/test_runner.py integration

test-e2e:
	@echo "🌐 Running end-to-end tests (requires AWS credentials, 5min timeout)..."
	$(PYTHON_VENV) tests/test_runner.py e2e

test-all:
	@echo "🧪 Running all tests..."
	$(PYTHON_VENV) tests/test_runner.py all

test-coverage:
	@echo "📊 Running tests with coverage..."
	$(PYTHON_VENV) tests/test_runner.py coverage

test-watch:
	@echo "👀 Running tests in watch mode..."
	$(PYTHON_VENV) tests/test_runner.py watch

test-quick:
	@echo "⚡ Running quick tests..."
	$(PYTHON_VENV) tests/test_runner.py quick

lint: ## Run linting
	$(PYTHON_VENV) -m flake8 src/ tests/
	$(PYTHON_VENV) -m black --check src/ tests/
	$(PYTHON_VENV) -m isort --check-only src/ tests/
	$(PYTHON_VENV) -m mypy src/

format: ## Format code
	$(PYTHON_VENV) -m black src/ tests/
	$(PYTHON_VENV) -m isort src/ tests/

# Local development
local-start: ## Start the application locally (uses programmatic credential extraction)
	@echo "Starting GRC Agent Squad locally..."
	$(PYTHON_VENV) -m src.main

local-dev: ## Start the application locally without AWS validation
	@echo "Starting GRC Agent Squad in local development mode..."
	SKIP_AWS_VALIDATION=true $(PYTHON_VENV) -m src.main

local-api: ## Start FastAPI server locally (uses programmatic credential extraction)
	@echo "Starting FastAPI server locally..."
	$(PYTHON_VENV) -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Docker operations
docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run Docker container locally with aws-vault
	aws-vault exec $(AWS_PROFILE) -- docker run -p 8000:8000 \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION=$(AWS_REGION) \
		$(DOCKER_IMAGE)

# AWS CDK operations
cdk-bootstrap: ## Bootstrap CDK in the AWS account
	aws-vault exec $(AWS_PROFILE) -- npx cdk bootstrap --region $(AWS_REGION)

cdk-synth: ## Synthesize CDK stack
	aws-vault exec $(AWS_PROFILE) -- npx cdk synth --region $(AWS_REGION)

cdk-deploy: ## Deploy to AWS using CDK with aws-vault
	@echo "Deploying to AWS with profile: $(AWS_PROFILE) in region: $(AWS_REGION)"
	aws-vault exec $(AWS_PROFILE) -- npx cdk deploy --region $(AWS_REGION) --require-approval never

cdk-destroy: ## Destroy AWS resources using CDK with aws-vault
	@echo "Destroying AWS resources..."
	aws-vault exec $(AWS_PROFILE) -- npx cdk destroy --region $(AWS_REGION) --force

# Build and push
build: clean docker-build ## Build the application

push: build ## Build and push Docker image to ECR
	@echo "Pushing to ECR..."
	aws-vault exec $(AWS_PROFILE) -- aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $$(aws-vault exec $(AWS_PROFILE) -- aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker tag $(DOCKER_IMAGE) $$(aws-vault exec $(AWS_PROFILE) -- aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com/$(APP_NAME):latest
	docker push $$(aws-vault exec $(AWS_PROFILE) -- aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com/$(APP_NAME):latest

# Cleanup
clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

clean-env: ## Remove virtual environment
	rm -rf $(VENV)

# AWS specific commands
aws-logs: ## View CloudWatch logs
	aws-vault exec $(AWS_PROFILE) -- aws logs tail /aws/lambda/$(APP_NAME) --follow --region $(AWS_REGION)

aws-status: ## Check AWS resources status
	@echo "Checking AWS resources status..."
	aws-vault exec $(AWS_PROFILE) -- aws lambda list-functions --region $(AWS_REGION) --query 'Functions[?starts_with(FunctionName, `$(APP_NAME)`)].[FunctionName,Runtime,LastModified]' --output table
	aws-vault exec $(AWS_PROFILE) -- aws apigateway get-rest-apis --region $(AWS_REGION) --query 'items[?name==`$(APP_NAME)`].[name,id,createdDate]' --output table

# Development utilities
dev-setup: dev-install ## Complete development environment setup
	@echo "Setting up pre-commit hooks..."
	$(PYTHON_VENV) -m pip install pre-commit
	$(PYTHON_VENV) -m pre_commit install

validate-aws: ## Validate AWS credentials and permissions (for infrastructure operations)
	@echo "Validating AWS credentials for profile: $(AWS_PROFILE)"
	@echo "Note: Application uses programmatic credential extraction, but this validates CLI access"
	aws-vault exec $(AWS_PROFILE) -- aws sts get-caller-identity
	aws-vault exec $(AWS_PROFILE) -- aws bedrock list-foundation-models --region $(AWS_REGION) --query 'modelSummaries[0:3].[modelId,modelName]' --output table

# Full deployment pipeline
deploy-full: test lint build push cdk-deploy ## Run full deployment pipeline

# Quick start for new developers
quick-start: dev-install validate-aws ## Quick start for new developers
	@echo "Quick start complete!"
	@echo "• The application uses programmatic credential extraction (no aws-vault needed for app startup)"
	@echo "• Run 'make local-start' or 'make local-api' to begin development" 