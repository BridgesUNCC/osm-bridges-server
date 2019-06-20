#!/bin/bash

sudo yum -y install yum-utils
sudo yum -y groupinstall development
sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y install python36u
sudo yum -y install python36u-pip
sudo yum -y install python36u-devel
sudo python3.6 -m pip install flask
sudo python3.6 -m pip install wget
sudo python3.6 -m pip install apscheduler
sudo python3.6 -m pip install virtualenv
