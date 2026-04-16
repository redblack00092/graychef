module.exports = {
  apps: [
    {
      name: 'graychef-api',
      cwd: './backend',
      script: 'uvicorn',
      args: 'main:app --host 127.0.0.1 --port 8000',
      interpreter: 'python3',
      watch: false,
      env: {
        NODE_ENV: 'production',
      },
    },
  ],
}
