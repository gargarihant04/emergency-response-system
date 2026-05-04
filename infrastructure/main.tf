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

# 4. Create a Route Table to direct traffic to the Internet Gateway
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.sos_vpc.id

  route {
    cidr_block = "0.0.0.0/0" # All outside internet traffic
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "SOS-Public-Route-Table"
  }
}

# 5. Associate the Route Table with your Public Subnet
resource "aws_route_table_association" "public_rt_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# 6. Create a Security Group (The Firewall)
resource "aws_security_group" "sos_sg" {
  name        = "sos-api-sg"
  description = "Allow inbound SSH and API traffic"
  vpc_id      = aws_vpc.sos_vpc.id

  # Allow SSH to access the machine
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Allow external API calls (e.g., your React frontend or curl commands)
  ingress {
    from_port   = 8000
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow the server to download updates and Docker images
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 means all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "SOS-Security-Group"
  }
}