# Add values
# Use the AMI of the custom Ec2 image you previously created
imageid                = "ami-018a96c79ce9e5447"
# Use t2.micro for the AWS Free Tier
instance-type          = "t3.micro"
key-name               = "EC2-ITMO444-Module2-Lab"
vpc_security_group_ids = "sg-07fdd6e2ff6d14a4f" 
tag-name               = "module-05"
user-sns-topic         = "jp-sns-topic"
elb-name               = "jp-elb"
tg-name                = "jp-tg"
asg-name               = "jp-asg"
desired                = 3
min                    = 2
max                    = 5
number-of-azs          = 3
region                 = "us-east-2"
raw-s3-bucket          = "jp-raw-s3b-041226"
finished-s3-bucket     = "jp-finished-s3b-041226"
dbname                 = "company"
snapshot_identifier    = "coursera-snapshot2"
sqs-name               = "jp-sqs"
username               = "controller"
