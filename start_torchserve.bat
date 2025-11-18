@echo off
REM 가상환경 활성화
call local_deploy_venv\Scripts\activate.bat

REM TorchServe 실행
torchserve --start --model-store TorchServe\model_store --ts-config TorchServe\config_properties\config_model.properties --models crack-detect=hybrid_segmentor-cuda-2.mar --disable-token-auth

REM TorchServe 실행 결과 출력
echo TorchServe가 시작되었습니다.
pause
