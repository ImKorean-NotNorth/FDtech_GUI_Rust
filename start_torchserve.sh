#!/bin/bash
# 가상환경 활성화
source ./hyeonu/bin/activate

# TorchServe 실행
torchserve --start --model-store TorchServe/model_store --ts-config TorchServe/config_properties/config_model.properties --models crack-detect=hybrid_segmentor-cuda-2.mar --disable-token-auth