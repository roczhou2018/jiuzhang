#!/usr/bin/bash

CONDA=Miniconda3-py310_23.1.0-1-Linux-x86_64.sh
./$CONDA
conda create -n chatglm --clone base
conda env list
conda activate chatglm

cd chatglm
git clone https://github.com/THUDM/ChatGLM-6B.git chatglm-6b
pip3 install --no-index --find-links=./chatglm/packages -r requirements.txt
mv ./chatglm-6b-model chatglm-6b/chatglm_model
cd chatglm-6b
pip3 install psutil
pip3 install gpustat
