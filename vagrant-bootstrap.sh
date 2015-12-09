#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade
apt-get install -y python python-pip python-dev mysql-server mysql-client libmysqlclient-dev redis-server

# MySQL config

cat <<EOT >/etc/mysql/conf.d/listen_everywhere.cnf
[mysqld]
bind-address=0.0.0.0
EOT

echo "create database scheduleparty_dev;" | mysql -uroot
echo "create database scheduleparty_test;" | mysql -uroot
echo "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'password';" |mysql -uroot
mysqladmin -uroot password "password" # Not secure but this is not exposed to the internet, so it's fine
service mysql restart

cd /vagrant
sudo pip install -r requirements/dev.txt
python manage.py db upgrade
