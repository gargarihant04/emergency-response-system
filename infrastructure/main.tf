# 1. Create the Virtual Private Cloud (VPC)
resource "aws_vpc" "sos_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "SOS-Emergency-VPC"
    Project = "Womens-Safety-Platform"
  }
}

# 2. Create a Public Subnet inside the VPC
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.sos_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "SOS-Public-Subnet"
  }
}

# 3. Create an Internet Gateway so the subnet can reach the outside world
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.sos_vpc.id

  tags = {
    Name = "SOS-Internet-Gateway"
  }
}