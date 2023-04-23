#!/usr/bin/bash

# CONDA=Miniconda3-py310_23.1.0-1-Linux-x86_64.sh
# ./$CONDA

# root 身份创建
sudo useradd -d /home/app app
sudo cat ~/id_rsa.pub >~app/.ssh/authorized_keys
sudo chown app:app ~app/.ssh/authorized_keys
sudo chmod 600 ~app/.ssh/authorized_keys
sudo service ssh restart
sudo mv ~/jiuzhang ~app/
sudo chown app:app ~app/jiuzhang -R

# app 身份构建:
cd ~app
sudo -u app conda create -n chatglm --clone base
sudo -u app conda env list
sudo -u app conda activate chatglm
sudo -u app pip install psutil
sudo -u app pip install gpustat
sudo -u app pip install hanziconv

cd /root/autodl-tmp/
sudo -u app git clone https://github.com/THUDM/ChatGLM-6B.git chatglm-6b
cd chatglm-6b
sudo -u app pip install --no-index --find-links=./chatglm/packages -r requirements.txt
# sudo mv ./chatglm-6b-model chatglm-6b/chatglm_model
cd chatglm-6b

# cd /root/autodl-tmp/
# sudo -u app git clone https://github.com/OpenLMLab/MOSS.git moss
# cd moss
