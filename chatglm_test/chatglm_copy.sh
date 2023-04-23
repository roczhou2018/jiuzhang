#!/usr/bin/bash

# USER=
# SERVER=
# CONDA=Miniconda3-py310_23.1.0-1-Linux-x86_64.sh
# CONDA=Anaconda3-2023.03-Linux-x86_64.sh
PORT=9999

# scp /mnt/e/Downloads/Edge/$CONDA $USER@$SERVER:~/
# scp /mnt/e/WorkData/chatglm-6b-model ~/
# scp ./chatglm_build.sh $USER@$SERVER:~/
cd ../..
scp -rP $PORT ./jiuzhang $USER@$SERVER:~/
scp -rP $PORT ~/.ssh/id_rsa.pub $USER@SERVER:~/
