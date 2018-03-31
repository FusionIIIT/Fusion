#!/bin/bash
# Add code and remove errors

echo "Installing RabbitMQ Server";
echo "-----------------------------";
code=`wget https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.7.4/rabbitmq-server_3.7.4-1_all.deb`;

if [ $code -ne 0 ]
then
    echo "Dependency Errors Found";
    echo "Installing dependencies...";
    sudo apt install -f;
fi

rm -rf ./*.deb;

echo "[*] RabbitMQ Server Installed Successfully";
