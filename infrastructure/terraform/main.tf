terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "inventory_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = {
    Name = "inventory-management-vpc"
  }
}

# Subnets
resource "aws_subnet" "public_subnet" {
  vpc_id     = aws_vpc.inventory_vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  
  tags = {
    Name = "inventory-public-subnet"
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id     = aws_vpc.inventory_vpc.id
  cidr_block = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  
  tags = {
    Name = "inventory-private-subnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "inventory_igw" {
  vpc_id = aws_vpc.inventory_vpc.id
  
  tags = {
    Name = "inventory-igw"
  }
}

