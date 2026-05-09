##############################################################################
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc
##############################################################################
# Create a VPC
resource "aws_vpc" "project" {
  cidr_block = "172.32.0.0/16"
  enable_dns_hostnames = true
  
  tags = {
    Name = var.tag-name
  }
}

# Query the VPC information
data "aws_vpc" "project" {
  id = aws_vpc.project.id
}

# Get all AZs in a VPC
data "aws_availability_zones" "available" {
  state = "available"
}

# Print out a list of Availability Zones
output "list-of-azs" {
  description = "List of AZs"
  value       = data.aws_availability_zones.available.names
}

# Create security group
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group
# Don't forget the egress rules!!!
resource "aws_security_group" "allow_http" {
  name        = "allow_http"
  description = "Allow http inbound traffic and all outbound traffic"
  vpc_id      = aws_vpc.project.id

  tags = {
    proto = "http"
    Name = var.tag-name
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow_http_ipv4" {
  security_group_id = aws_security_group.allow_http.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_ipv4" {
  security_group_id = aws_security_group.allow_http.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "allow_mysql" {
  security_group_id = aws_security_group.allow_http.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 3306
  ip_protocol       = "tcp"
  to_port           = 3306
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv4" {
  security_group_id = aws_security_group.allow_http.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

data "aws_security_group" "coursera-project" {
  filter {
    name   = "tag:Name"
    values = ["module-05"]
  }

  filter {
    name   = "vpc-id"
    values = [aws_vpc.project.id]
  }
}

# Create VPC DHCP options -- public DNS provided by Amazon
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_dhcp_options
resource "aws_vpc_dhcp_options" "project" {
  domain_name = "${var.region}.compute.internal"
  domain_name_servers = ["AmazonProvidedDNS"]
  
  tags = {
    Name = var.tag-name
  }
}

# Associate these options with our VPC now
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_dhcp_options

resource "aws_vpc_dhcp_options_association" "dns_resolver" {
  vpc_id          = aws_vpc.project.id
  dhcp_options_id = aws_vpc_dhcp_options.project.id
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/internet_gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.project.id

  tags = {
    Name = var.tag-name
  }
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table
resource "aws_route_table" "example" {
  depends_on = [ aws_vpc.project ]
  vpc_id = aws_vpc.project.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = var.tag-name
  }
}

# Now we need to associate the route_table to subnets
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table_association
resource "aws_route_table_association" "subnets" {
  count = var.number-of-azs
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.example.id
}

# Now make the new route the main associated route
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/main_route_table_association
resource "aws_main_route_table_association" "a" {
  vpc_id         = aws_vpc.project.id
  route_table_id = aws_route_table.example.id
}

# IAM instance policy
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_instance_profile

resource "aws_iam_instance_profile" "coursera_profile" {
  name = "coursera_profile"
  role = aws_iam_role.role.name
}

# Creating the policy (rules) for what the role can do
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Creating the role
resource "aws_iam_role" "role" {
  name               = "project_role"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = {
    Name = var.tag-name
  }
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy
resource "aws_iam_role_policy" "s3_fullaccess_policy" {
  name = "s3_fullaccess_policy"
  role = aws_iam_role.role.id

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy
resource "aws_iam_role_policy" "rds_fullaccess_policy" {
  name = "rds_fullaccess_policy"
  role = aws_iam_role.role.id

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "rds:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy" "sm_fullaccess_policy" {
  name = "sm_fullaccess_policy"
  role = aws_iam_role.role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy" "sqs_fullaccess_policy" {
  name = "sqs_fullaccess_policy"
  role = aws_iam_role.role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "sqs:*"
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}



# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy
resource "aws_iam_role_policy" "sns_fullaccess_policy" {
  name = "sns_fullaccess_policy"
  role = aws_iam_role.role.id

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sns:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}




# creating a private IPv4 subnet per AZ
# https://stackoverflow.com/questions/63991120/automatically-create-a-subnet-for-each-aws-availability-zone-in-terraform
# https://stackoverflow.com/questions/26706683/ec2-t2-micro-instance-has-no-public-dns
resource "aws_subnet" "private" {
  depends_on = [ aws_vpc.project ]
  count = var.number-of-azs
  availability_zone = data.aws_availability_zones.available.names[count.index]
  vpc_id   = data.aws_vpc.project.id
  map_public_ip_on_launch = true
  # https://developer.hashicorp.com/terraform/language/functions/cidrsubnets
  # The 8 represents /24
  cidr_block = cidrsubnet(data.aws_vpc.project.cidr_block, 4, count.index + 3)

  tags = {
    Name = var.tag-name
    Type = "private"
    Zone = data.aws_availability_zones.available.names[count.index]
  }
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/subnets
data "aws_subnets" "public" {
  filter {
    name = "vpc-id"
    # set of strings required
    values = [data.aws_vpc.project.id]
  }
}

output "aws_subnets" {
    value = [data.aws_vpc.project.id]
}

##############################################################################
# Create launch template
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/launch_template
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/launch_template
##############################################################################
resource "aws_launch_template" "lt" {
  image_id                             = var.imageid
  instance_initiated_shutdown_behavior = "terminate"
  instance_type                        = var.instance-type
  key_name                             = var.key-name
  vpc_security_group_ids               = [aws_security_group.allow_http.id]
  iam_instance_profile {
    name = aws_iam_instance_profile.coursera_profile.name
  }

  monitoring {
    enabled = false
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = var.tag-name
    }
  }
  user_data = filebase64("./install-env.sh")
}

##############################################################################
# Create autoscaling group
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_group
##############################################################################

resource "aws_autoscaling_group" "asg" {
  name                      = var.asg-name
  depends_on                = [aws_launch_template.lt]
  desired_capacity          = var.desired
  max_size                  = var.max
  min_size                  = var.min
  health_check_grace_period = 300
  health_check_type         = "EC2"
  target_group_arns         = [aws_lb_target_group.alb-lb-tg.arn]
  # place in all AZs
  # Use this if you only have the default subnet per AZ
  # availability_zones        =  data.aws_availability_zones.available.names
  # Use this is you have multiple subnets per AZ
  vpc_zone_identifier = [for subnet in aws_subnet.private : subnet.id]

  tag {
    key                 = "assessment"
    value               = var.tag-name
    propagate_at_launch = true
  }

  launch_template {
    id      = aws_launch_template.lt.id
    version = "$Latest"
  }
}

##############################################################################
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb
##############################################################################
resource "aws_lb" "lb" {
  depends_on = [ aws_subnet.private ]
  name               = var.elb-name
  internal           = false
  load_balancer_type = "application"
  #security_groups    = [var.vpc_security_group_ids]
  security_groups = [aws_security_group.allow_http.id]
  # Place across all subnets
  #subnets            = aws_subnet.private.ids
  subnets = [for subnet in aws_subnet.private : subnet.id]

  enable_deletion_protection = false

  tags = {
    Name = var.tag-name
  }
}

# output will print a value out to the screen
output "url" {
  value = aws_lb.lb.dns_name
}

##############################################################################
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_attachment
##############################################################################
# Create a new ALB Target Group attachment

resource "aws_autoscaling_attachment" "example" {
  # Wait for lb to be running before attaching to asg
  depends_on  = [aws_lb.lb]
  autoscaling_group_name = aws_autoscaling_group.asg.id
  lb_target_group_arn    = aws_lb_target_group.alb-lb-tg.arn
}

output "alb-lb-tg-arn" {
  value = aws_lb_target_group.alb-lb-tg.arn
}

output "alb-lb-tg-id" {
  value = aws_lb_target_group.alb-lb-tg.id
}

##############################################################################
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group
##############################################################################

resource "aws_lb_target_group" "alb-lb-tg" {
  # depends_on is effectively a waiter -- it forces this resource to wait until the listed
  # resource is ready
  depends_on  = [aws_lb.lb]
  name        = var.tg-name
  target_type = "instance"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.project.id
}

##############################################################################
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener
##############################################################################

resource "aws_lb_listener" "front_end" {
  load_balancer_arn = aws_lb.lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alb-lb-tg.arn
  }
}

##############################################################################
# Create S3 buckets with policies that allow GetObject
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket
# https://stackoverflow.com/questions/65984400/how-to-delete-non-empty-s3-bucket-with-terraform
##############################################################################

resource "aws_s3_bucket" "raw-bucket" {
  bucket = var.raw-s3-bucket
  force_destroy = true
}

resource "aws_s3_bucket" "finished-bucket" {
  bucket = var.finished-s3-bucket
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "allow_access_from_another_account-raw" {
  bucket = aws_s3_bucket.raw-bucket.id
  depends_on=[data.aws_iam_policy_document.allow_access_from_another_account-raw]

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

resource "aws_s3_bucket_public_access_block" "allow_access_from_another_account-finished" {
  bucket = aws_s3_bucket.finished-bucket.id
  depends_on=[data.aws_iam_policy_document.allow_access_from_another_account-finished]
  

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "allow_access_from_another_account-raw" {
  depends_on  = [aws_s3_bucket_public_access_block.allow_access_from_another_account-raw]
  bucket = aws_s3_bucket.raw-bucket.id
  policy = data.aws_iam_policy_document.allow_access_from_another_account-raw.json
}

resource "aws_s3_bucket_policy" "allow_access_from_another_account-finished" {
  depends_on  = [aws_s3_bucket_public_access_block.allow_access_from_another_account-finished]
  bucket = aws_s3_bucket.finished-bucket.id
  policy = data.aws_iam_policy_document.allow_access_from_another_account-finished.json
}

data "aws_iam_policy_document" "allow_access_from_another_account-raw" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      aws_s3_bucket.raw-bucket.arn,
      "${aws_s3_bucket.raw-bucket.arn}/*",
    ]
  }
}

data "aws_iam_policy_document" "allow_access_from_another_account-finished" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      aws_s3_bucket.finished-bucket.arn,
      "${aws_s3_bucket.finished-bucket.arn}/*",
    ]
  }
}

# Create SQS Queue
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
resource "aws_sqs_queue" "coursera_queue" {
  name                      = var.sqs-name
  delay_seconds             = 90
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  # Default is 30 seconds
  visibility_timeout_seconds = 180

  tags = {
    Name = var.tag-name
  }
}



# Create SNS Topics
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic
resource "aws_sns_topic" "user_updates" {
  name = var.user-sns-topic
  
  tags = {
    Name = var.tag-name
  }
}

# Generate random password -- this way its never hardcoded into our variables and inserted directly as a secretcheck 
# No one will know what it is!
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_random_password
data "aws_secretsmanager_random_password" "coursera_project" {
  password_length = 30
  exclude_numbers = true
  exclude_punctuation = true
}

# Create the actual secret (not adding a value yet)
# Provides a resource to manage AWS Secrets Manager secret metadata. To manage
# secret rotation, see the aws_secretsmanager_secret_rotation resource. To 
# manage a secret value, see the aws_secretsmanager_secret_version resource.
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret
resource "aws_secretsmanager_secret" "coursera_project_username" {
  name = "uname"
  # https://github.com/hashicorp/terraform-provider-aws/issues/4467
  # This will automatically delete the secret upon Terraform destroy 
  recovery_window_in_days = 0
  tags = {
    Name = var.tag-name
  }
}

resource "aws_secretsmanager_secret" "coursera_project_password" {
  name = "pword"
  # https://github.com/hashicorp/terraform-provider-aws/issues/4467
  # This will automatically delete the secret upon Terraform destroy 
  recovery_window_in_days = 0
  tags = {
    Name = var.tag-name
  }
}

# Provides a resource to manage AWS Secrets Manager secret version including its secret value.
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version
# Used to set the value
resource "aws_secretsmanager_secret_version" "coursera_project_username" {
  #depends_on = [ aws_secretsmanager_secret_version.project_username ]
  secret_id     = aws_secretsmanager_secret.coursera_project_username.id
  secret_string = var.username
}

resource "aws_secretsmanager_secret_version" "coursera_project_password" {
  #depends_on = [ aws_secretsmanager_secret_version.project_password ]
  secret_id     = aws_secretsmanager_secret.coursera_project_password.id
  secret_string = data.aws_secretsmanager_random_password.coursera_project.random_password
}

# Retrieve secrets value set in secret manager
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version
# https://github.com/hashicorp/terraform-provider-aws/issues/14322
#data "aws_secretsmanager_secret_version" "project_username" {
#  depends_on = [ aws_secretsmanager_secret_version.coursera_project_username ]
#  secret_id = aws_secretsmanager_secret.coursera_project_username.id
#}

#data "aws_secretsmanager_secret_version" "project_password" {
#  depends_on = [ aws_secretsmanager_secret_version.coursera_project_password ]
#  secret_id = aws_secretsmanager_secret.coursera_project_password.id
#}

# Create a dbsubnet group to assign our database to our custom created subnets and vpc
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_subnet_group
resource "aws_db_subnet_group" "default" {
  name       = "coursera-project"
  subnet_ids = [for subnet in aws_subnet.private : subnet.id]

  tags = {
    Name = var.tag-name
  }
}

# Return the subnetgroup id
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/db_subnet_group
data "aws_db_subnet_group" "database" {
  depends_on = [ aws_db_subnet_group.default ]
  name = "coursera-project"
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/db_snapshot
# Use the latest production snapshot to create a dev instance.
resource "aws_db_instance" "default" {
  instance_class      = "db.t3.micro"
  #db_name             = var.dbname
  snapshot_identifier = var.snapshot_identifier
  skip_final_snapshot  = true
  username             = aws_secretsmanager_secret_version.coursera_project_username.secret_string
  password             = aws_secretsmanager_secret_version.coursera_project_password.secret_string
  vpc_security_group_ids = [data.aws_security_group.coursera-project.id]
  db_subnet_group_name = data.aws_db_subnet_group.database.id
}

output "db-address" {
  description = "Endpoint URL "
  value = aws_db_instance.default.address
}

output "db-name" {
  description = "DB Name "
  value = aws_db_instance.default.db_name
}

# Create the Backend infrastrucutre
# Create an EC2 instance to execute the SQL commands on
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance
resource "aws_instance" "backend" {
  ami                    = var.imageid
  instance_type          = var.instance-type
  key_name               = var.key-name
  vpc_security_group_ids = [aws_security_group.allow_http.id]
  subnet_id              = aws_subnet.private[0].id
  user_data              = filebase64("./install-be-env.sh")
  iam_instance_profile   = aws_iam_instance_profile.coursera_profile.name

  tags = {
    Name = var.tag-name
    Type = "backend"
  }
}

output "backend-ip" {
  description = "IP address of Backend..."
  value = aws_instance.backend.public_ip
}