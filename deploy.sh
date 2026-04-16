#!/bin/bash
set -e

echo "=== 그레이요리사 배포 시작 ==="

# 백엔드 의존성 설치
echo "[1/5] 백엔드 의존성 설치..."
cd backend
pip3 install -r requirements.txt
cd ..

# 프론트엔드 빌드
echo "[2/5] 프론트엔드 빌드..."
cd frontend
npm install
npm run build
cd ..

# pm2로 백엔드 실행
echo "[3/5] 백엔드 서버 시작..."
pm2 delete graychef-api 2>/dev/null || true
pm2 start ecosystem.config.cjs
pm2 save

# Nginx 설정 적용
echo "[4/5] Nginx 설정 적용..."
sudo cp nginx.conf /etc/nginx/sites-available/graychef
sudo ln -sf /etc/nginx/sites-available/graychef /etc/nginx/sites-enabled/graychef
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo "[5/5] 완료!"
echo "서비스가 http://$(curl -s ifconfig.me) 에서 실행 중입니다."
