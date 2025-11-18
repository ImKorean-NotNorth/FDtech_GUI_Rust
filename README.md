# FDCrackDetectGUI - 일회성 납품용 균열검출 소프트웨어
## 1. 환경설정
### 프로젝트 관련 라이브러리 설치 명령어 
pip install -r requirements.txt
### VSCode 가상환경 디버깅 방법
{  
&nbsp;&nbsp;"version": "0.2.0",  
&nbsp;&nbsp;"configurations": [  
&nbsp;&nbsp;&nbsp;&nbsp;{  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"name": "Run Python Script in Venv",  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"type": "debugpy",  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"request": "launch",  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"program": "${workspaceFolder}/pyqt5.py",           <--- 각자 파이썬 스크립트 명으로 변경  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"console": "integratedTerminal",  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"python": "${workspaceFolder}/hyeonu/bin/python"    <--- 각자 가상환경 디렉토리로 변경  
&nbsp;&nbsp;&nbsp;&nbsp;}  
&nbsp;&nbsp;]  
}  
  
위 내용 복사하여 프로젝트 폴더 내부 .vscode 디렉토리에 launch.json 생성 후 붙여넣기, vscode에서 F5 눌러서 디버깅 진행


## build
pyinstaller .\FDCrackDetector_v1.1.spec   
windows 보안 - 악성코드로 인식하는 방안 관련 해결법 https://jasmine125.tistory.com/1009