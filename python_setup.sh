#!/bin/bash

PYTHON=python3

sudo yum -y install yum-utils
sudo yum -y groupinstall development
sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y install python36u
sudo yum -y install python36u-pip
sudo yum -y install python36u-devel
sudo ${PYTHON} -m pip install flask
sudo ${PYTHON} -m pip install wget
sudo ${PYTHON} -m pip install apscheduler
sudo ${PYTHON} -m pip install virtualenv
