#! /bin/bash
# setting up cloudwatch logs for mount and memory
set -vx
echo "install additional Perl modules"
sudo yum install -y perl-Switch perl-DateTime perl-Sys-Syslog perl-LWP-Protocol-https perl-Digest-SHA
sudo yum install -y awslogs
sudo yum install -y unzip
echo "download, install, and configure the monitoring scripts"
cd /home/hadoop
curl https://aws-cloudwatch.s3.amazonaws.com/downloads/CloudWatchMonitoringScripts-1.2.2.zip -O
unzip CloudWatchMonitoringScripts-1.2.2.zip && \
rm CloudWatchMonitoringScripts-1.2.2.zip && \
cd aws-scripts-mon
echo "setting cron"

crontab -l | { cat; echo "*/5 * * * * /home/hadoop/aws-scripts-mon/mon-put-instance-data.pl --mem-used-incl-cache-buff --mem-util --disk-space-util --disk-path=/ --disk-path=/mnt --disk-path=/emr" ;} | crontab -
df -h
crontab -l
