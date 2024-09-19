#! /bin/bash
# setting up cloudwatch logs for mount and memory
set -vx
echo "install additional Perl modules"
sudo yum install -y perl-Switch perl-DateTime perl-Sys-Syslog perl-LWP-Protocol-https perl-Digest-SHA.x86_64
sudo yum install -y awslogs
sudo yum install -y unzip
echo "download, install, and configure the monitoring scripts"
cd /home/hadoop
curl https://aws-cloudwatch.s3.amazonaws.com/downloads/CloudWatchMonitoringScripts-1.2.2.zip -O
unzip CloudWatchMonitoringScripts-1.2.2.zip && \
rm CloudWatchMonitoringScripts-1.2.2.zip && \
cd aws-scripts-mon
echo "setting cron"

sudo su - <<EOF
echo "hadoop" >> /etc/cron.allow
EOF

if [[ $(df -h | grep '/mnt2' | wc -l) = "1" ]];  then
    crontab -l | { cat; echo "*/5 * * * * /home/hadoop/aws-scripts-mon/mon-put-instance-data.pl --mem-used-incl-cache-buff --mem-util --disk-space-util --disk-path=/ --disk-path=/mnt --disk-path=/mnt1 --disk-path=/emr --disk-path=/mnt2 --disk-path=/mnt3"; } | crontab -
else
    crontab -l | { cat; echo "*/5 * * * * /home/hadoop/aws-scripts-mon/mon-put-instance-data.pl --mem-used-incl-cache-buff --mem-util --disk-space-util --disk-path=/ --disk-path=/mnt --disk-path=/emr"; } | crontab -
fi
df -h
crontab -l