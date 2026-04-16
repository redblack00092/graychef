#!/bin/bash

echo "=== 그레이셰프 업데이트 시작 ==="

cd ~/graychef

echo ">>> 코드 최신화..."
git pull

echo ">>> 프론트엔드 빌드..."
cd frontend
npm install
npm run build
cd ..

echo ">>> 백엔드 재시작..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..
pm2 restart graychef-api

echo ">>> Nginx 재시작..."
sudo systemctl restart nginx

echo "=== 업데이트 완료! ==="
